"""One explicit DEV live phone start/check, with private durable no-retry checkpoints."""
from pathlib import Path
import json,os,tempfile,requests
ROOT=Path("/Users/kyouhan/.config/aicontrolcenter-dev-order")
STATE=ROOT/"phone-live.private.json"
ORIGIN="https://dev.bokstory.duckdns.org"
BASE="http://127.0.0.1:18445"
def save(value):
    fd,name=tempfile.mkstemp(dir=ROOT,prefix="phone-live-");os.fchmod(fd,0o600)
    with os.fdopen(fd,"w") as f:json.dump(value,f,indent=2);f.write("\n")
    os.replace(name,STATE)
def main(action):
    cfgpath=ROOT/"phone-verification.private.json"
    if cfgpath.is_symlink() or cfgpath.stat().st_mode & 0o077:raise RuntimeError("PRIVATE_CONFIG_REQUIRED")
    cfg=json.loads(cfgpath.read_text())
    if cfg.get("environment")!="DEV" or cfg.get("enabled") is not True:raise RuntimeError("DEV_ONLY")
    if STATE.exists():
        if STATE.is_symlink() or STATE.stat().st_mode & 0o077:raise RuntimeError("PRIVATE_STATE_REQUIRED")
        state=json.loads(STATE.read_text())
    else:state={"start_attempted":False,"check_attempted":False,"otp":""}
    headers={"Origin":ORIGIN}
    if action=="start":
        if state.get("start_attempted"):raise RuntimeError("EXISTING_START_INSPECT_ONLY_NO_RESEND")
        state["start_attempted"]=True;save(state)
        try:r=requests.post(BASE+"/__order-dev/phone/start",headers=headers,json={"phone":cfg["test_phone"],"consent":True},timeout=25)
        except Exception:raise RuntimeError("START_UNKNOWN_NO_RETRY") from None
        state["start_http"]=r.status_code
        state["phone_cookie"]=r.cookies.get("__Host-aicc_phone","");save(state)
        body=r.json()
        print(json.dumps({"start_http":r.status_code,"state":body.get("state"),"code":body.get("code"),"provider_code":body.get("provider_code"),"otp_file":str(STATE),"sms_receipt_confirmed":False}))
    elif action=="check":
        if state.get("check_attempted") or not state.get("phone_cookie"):raise RuntimeError("CHECK_UNAVAILABLE")
        import re
        code=state.get("otp","")
        if not re.fullmatch(r"[0-9]{4,10}",code):raise RuntimeError("ENTER_OTP_IN_PRIVATE_FILE")
        state["check_attempted"]=True;state["otp"]="";save(state)
        headers["Cookie"]="__Host-aicc_phone="+state["phone_cookie"]
        try:r=requests.post(BASE+"/__order-dev/phone/check",headers=headers,json={"code":code},timeout=25)
        except Exception:raise RuntimeError("CHECK_UNKNOWN_NO_RETRY") from None
        state["check_http"]=r.status_code
        if r.status_code==201:
            state["customer_cookie"]=r.cookies.get("__Host-aicc_customer","");state["csrf"]=r.headers.get("X-CSRF-Token","")
        save(state)
        print(json.dumps({"check_http":r.status_code,"phone_verified":r.status_code==201,"customer_session_issued":bool(state.get("customer_cookie")),"guest_order_created":False}))
    else:raise ValueError("choose start or check")
if __name__=="__main__":
    import sys
    main(sys.argv[1])
