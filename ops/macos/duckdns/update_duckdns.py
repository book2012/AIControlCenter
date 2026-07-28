#!/usr/bin/env python3
from __future__ import annotations

import ipaddress
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

SUBDOMAIN_ENV = "AICONTROLCENTER_DUCKDNS_SUBDOMAIN"
TOKEN_FILE_ENV = "AICONTROLCENTER_DUCKDNS_TOKEN_FILE"
ENDPOINT = "https://www.duckdns.org/update"

def emit(payload):
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True), flush=True)

def load_configuration():
    subdomain = os.environ.get(SUBDOMAIN_ENV, "").strip().lower()
    token_path = os.environ.get(TOKEN_FILE_ENV, "").strip()
    if not subdomain or not token_path:
        raise RuntimeError("configuration missing")
    path = os.path.expanduser(token_path)
    token = open(path, "r", encoding="utf-8").read().strip()
    if not token:
        raise RuntimeError("token unavailable")
    return subdomain, token

def main():
    try:
        subdomain, token = load_configuration()
        hostname = subdomain + ".duckdns.org"
        if "--check" in sys.argv:
            emit({"classification":"DUCKDNS_CONFIGURATION_VALID","hostname":hostname,"network_write":False,"result":"PASS"})
            return 0
        query = urllib.parse.urlencode({"domains":subdomain,"token":token,"verbose":"true"})
        request = urllib.request.Request(ENDPOINT + "?" + query, headers={"User-Agent":"AIControlCenter-DuckDNS/1.0"})
        with urllib.request.urlopen(request, timeout=15) as response:
            lines = [line.strip() for line in response.read().decode("utf-8", errors="replace").splitlines() if line.strip()]
        token = ""
        ok = bool(lines) and lines[0].upper() == "OK"
        state = next((line.upper() for line in lines if line.upper() in {"UPDATED", "NOCHANGE"}), None)
        ipv4 = None
        for line in lines[1:]:
            try:
                candidate = ipaddress.ip_address(line)
                if candidate.version == 4:
                    ipv4 = str(candidate)
                    break
            except ValueError:
                continue
        if not ok:
            emit({"classification":"DUCKDNS_UPDATE_REJECTED","hostname":hostname,"network_write":True,"result":"FAIL"})
            return 1
        emit({"classification":"DUCKDNS_UPDATE_OK","hostname":hostname,"ipv4":ipv4,"network_write":True,"provider_state":state,"result":"PASS"})
        return 0
    except urllib.error.HTTPError as error:
        emit({"classification":"DUCKDNS_HTTP_ERROR","http_status":error.code,"network_write":True,"result":"FAIL"})
        return 1
    except urllib.error.URLError:
        emit({"classification":"DUCKDNS_NETWORK_ERROR","network_write":True,"result":"FAIL"})
        return 1
    except Exception as error:
        emit({"classification":"DUCKDNS_RUNTIME_ERROR","error_type":type(error).__name__,"network_write":False,"result":"FAIL"})
        return 1

if __name__ == "__main__":
    sys.exit(main())
