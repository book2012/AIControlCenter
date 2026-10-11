import hashlib,hmac,json
from types import SimpleNamespace
import pytest
from ops.macos.shopping.dev_solapi_sms import SolapiSMS,SolapiUnknown,payload

CFG={"environment":"DEV","provider":"SOLAPI","credentials":{"api_key":"TESTKEY","api_secret":"TESTSECRET"},"sender_number":"0212345678"}
PHONE="+821012345678"
GID="G4V1234567890TEST";MID="M4V1234567890TEST"

class Session:
    def __init__(self):
        self.calls=[];self.response={}
    def request(self,*args,**kwargs):
        self.calls.append((args,kwargs))
        return SimpleNamespace(status_code=200,content=b"response",json=lambda:self.response)

def accepted(session):
    event=hashlib.sha256(b"order:15").hexdigest()
    session.response={"groupInfo":{"groupId":GID,"count":{"registeredSuccess":1},
        "messageList":[{"messageId":MID,"customFields":{"aicc_event":event}}]},"failedMessageList":[]}

def test_domestic_number_encoding_and_lms_bounds():
    assert payload(CFG["sender_number"],PHONE,"짧은 문자","event")["to"]=="01012345678"
    assert payload(CFG["sender_number"],PHONE,"가"*45,"event")["type"]=="SMS"
    assert payload(CFG["sender_number"],PHONE,"가"*46,"event")["type"]=="LMS"
    with pytest.raises(ValueError):payload(CFG["sender_number"],PHONE,"가"*1001,"event")
    with pytest.raises(ValueError):payload(CFG["sender_number"],"+12025550123","test","event")

def test_hmac_is_fresh_redirect_disabled_and_accepted_is_not_delivered():
    session=Session();accepted(session);client=SolapiSMS(CFG,session=session)
    receipt=client.send(PHONE,"주문 확인","order:15")
    assert receipt["state"]=="ACCEPTED"
    args,kw=session.calls[0];assert args==("POST","https://api.solapi.com/messages/v4/send-many/detail")
    assert kw["allow_redirects"] is False and session.trust_env is False
    header=kw["headers"]["Authorization"];values=dict(x.split("=",1) for x in header.removeprefix("HMAC-SHA256 ").split(", "))
    assert values["signature"]==hmac.new(b"TESTSECRET",(values["date"]+values["salt"]).encode(),hashlib.sha256).hexdigest()
    assert client.auth()["Authorization"]!=header
    assert "TESTKEY" not in repr(client) and "TESTSECRET" not in repr(client)

@pytest.mark.parametrize("code,state",[("2000","ACCEPTED"),("4000","DELIVERED"),("3113","FAILED")])
def test_delivery_polling_verifies_exact_receipt_without_resend(code,state):
    session=Session();accepted(session);client=SolapiSMS(CFG,session=session);receipt=client.send(PHONE,"주문 확인","order:15")
    session.response={"messageList":{MID:{"groupId":GID,"to":"01012345678","from":CFG["sender_number"],
        "customFields":{"aicc_event":receipt["event_hash"]},"text":"주문 확인","statusCode":code}}}
    assert client.status(receipt)=={"state":state,"status_code":code}
    assert len(session.calls)==2 and session.calls[-1][0][0]=="GET"

def test_receipt_mismatch_and_ambiguous_send_never_retry():
    session=Session();accepted(session);client=SolapiSMS(CFG,session=session)
    session.response["groupInfo"]["messageList"][0]["customFields"]["aicc_event"]="wrong"
    with pytest.raises(SolapiUnknown):client.send(PHONE,"test","order:15")
    assert len(session.calls)==1
    session.response={"groupInfo":{"count":{"registeredSuccess":0}},"failedMessageList":[{}]}
    with pytest.raises(SolapiUnknown):client.send(PHONE,"test","different")
    assert len(session.calls)==2

def test_status_binding_rejects_wrong_recipient():
    session=Session();accepted(session);client=SolapiSMS(CFG,session=session);receipt=client.send(PHONE,"test","order:15")
    session.response={"messageList":{MID:{"groupId":GID,"to":"01099999999","from":CFG["sender_number"]}}}
    with pytest.raises(SolapiUnknown):client.status(receipt)
