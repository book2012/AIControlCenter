"""Pinned DEV Naver Cloud SENS SMS transport; acceptance is not delivery."""
import base64
import hashlib
import hmac
import re
import time
from urllib.parse import quote

import requests

from ops.macos.shopping.dev_order_operator import local_phone


class SensUnknown(RuntimeError):
    pass


def local_recipient(phone):
    return local_phone(phone)


class SensSMS:
    def __init__(self, cfg, *, session=None, clock=time.time):
        if cfg.get("environment") != "DEV" or cfg.get("provider") != "NCP_SENS" or cfg.get("enabled") is not True:
            raise ValueError("DEV_SENS_CONFIGURATION_REQUIRED")
        credentials = cfg.get("credentials", {})
        self.access = credentials.get("access_key")
        self.secret = credentials.get("secret_key")
        self.service_id = cfg.get("service_id")
        self.sender = cfg.get("sender_number")
        if any(type(v) is not str or not v or v != v.strip() for v in (self.access, self.secret, self.service_id, self.sender)):
            raise ValueError("SENS_CREDENTIALS_REQUIRED")
        if not re.fullmatch(r"ncp:sms:kr:[A-Za-z0-9:-]{8,100}", self.service_id):
            raise ValueError("SENS_SERVICE_REQUIRED")
        if not re.fullmatch(r"0[0-9]{7,10}", self.sender):
            raise ValueError("REGISTERED_SENDER_REQUIRED")
        self.session = session or requests.Session()
        self.session.trust_env = False
        self.clock = clock

    def _path(self, suffix):
        return "/sms/v2/services/" + quote(self.service_id, safe=":") + "/messages" + suffix

    def _request(self, method, suffix="", *, payload=None):
        path = self._path(suffix)
        stamp = str(int(self.clock() * 1000))
        signature = base64.b64encode(hmac.new(
            self.secret.encode(), f"{method} {path}\n{stamp}\n{self.access}".encode(), hashlib.sha256
        ).digest()).decode()
        try:
            response = self.session.request(
                method, "https://sens.apigw.ntruss.com" + path,
                headers={"x-ncp-apigw-timestamp": stamp, "x-ncp-iam-access-key": self.access,
                         "x-ncp-apigw-signature-v2": signature, "Content-Type": "application/json"},
                json=payload, timeout=15, allow_redirects=False,
            )
            if response.status_code != (202 if method == "POST" else 200) or len(response.content) > 131072:
                raise ValueError("SENS_RESPONSE_INVALID")
            doc = response.json()
            if type(doc) is not dict or doc.get("statusCode") != ("202" if method == "POST" else "200") or doc.get("statusName") != "success":
                raise ValueError("SENS_RESPONSE_INVALID")
            return doc
        except Exception:
            raise SensUnknown("SENS_RESULT_UNKNOWN") from None

    def send(self, phone, text):
        to = local_recipient(phone)
        if type(text) is not str or not text.strip():
            raise ValueError("SMS_CONTENT_REQUIRED")
        try:
            size = len(text.encode("euc-kr"))
        except UnicodeEncodeError:
            raise ValueError("SMS_ENCODING_REQUIRED") from None
        if size > 2000:
            raise ValueError("LMS_BYTE_LIMIT")
        kind = "SMS" if size <= 90 else "LMS"
        body = {"type": kind, "contentType": "COMM", "countryCode": "82", "from": self.sender,
                "content": text, "messages": [{"to": to}]}
        if kind == "LMS":
            body["subject"] = "agachichi 주문 안내"
        doc = self._request("POST", payload=body)
        rid = doc.get("requestId")
        if type(rid) is not str or not re.fullmatch(r"[A-Za-z0-9-]{16,100}", rid):
            raise SensUnknown("SENS_RECEIPT_UNKNOWN")
        return {"provider": "NCP_SENS", "request_id": rid, "to": to, "sender": self.sender,
                "text_hash": hashlib.sha256(text.encode()).hexdigest(), "state": "ACCEPTED"}

    def status(self, receipt):
        rid = receipt["request_id"]
        if not re.fullmatch(r"[A-Za-z0-9-]{16,100}", rid):
            raise ValueError("SENS_RECEIPT_INVALID")
        doc = self._request("GET", "?requestId=" + quote(rid, safe=""))
        rows = doc.get("messages")
        if type(rows) is not list or len(rows) != 1:
            raise SensUnknown("SENS_STATUS_BINDING")
        row = rows[0]
        if (row.get("requestId") != rid or row.get("to") != receipt["to"] or
                row.get("from") != receipt["sender"] or
                hashlib.sha256(row.get("content", "").encode()).hexdigest() != receipt["text_hash"]):
            raise SensUnknown("SENS_STATUS_BINDING")
        if row.get("status") != "COMPLETED":
            state = "ACCEPTED"
        elif row.get("statusName") == "success" and row.get("statusCode") == "0":
            state = "DELIVERED"
        elif row.get("statusName") == "fail":
            state = "FAILED"
        else:
            raise SensUnknown("SENS_STATUS_UNKNOWN")
        return {"state": state, "status_code": row.get("statusCode")}
