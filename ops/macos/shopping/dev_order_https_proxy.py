"""Pinned loopback HTTPS facade for isolated DEV WooCommerce only."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import ssl
import plistlib
import requests

ROOT=Path('/Users/kyouhan/.config/aicontrolcenter-dev-order')
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def handle_request(self):
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<=size<=1048576 or not self.path.startswith('/') or self.path.startswith('//'):
                self.send_error(400);return
            body=self.rfile.read(size) if size else None
            headers={k:v for k,v in self.headers.items() if k.lower() not in
                {'host','connection','transfer-encoding','content-length','forwarded','x-forwarded-host','x-forwarded-proto'}}
            headers['Host']='localhost:18446';headers['X-Forwarded-Proto']='https'
            response=requests.request(self.command,'http://127.0.0.1:55274'+self.path,
                headers=headers,data=body,timeout=20,allow_redirects=False)
            if len(response.content)>4194304:self.send_error(502);return
            self.send_response(response.status_code)
            for k,v in response.headers.items():
                if k.lower() not in {'connection','transfer-encoding','content-encoding','content-length'}:
                    self.send_header(k,v)
            self.send_header('Content-Length',str(len(response.content)));self.end_headers()
            self.wfile.write(response.content)
        except Exception:
            try:self.send_error(502)
            except Exception:pass
    do_GET=handle_request
    do_POST=handle_request

def launch_agent(release: Path, python: Path, private: Path = ROOT) -> bytes:
    """Pin the DEV facade to an immutable release and keep it alive after terminal exit."""
    release=release.resolve();python=python.resolve();private=private.resolve()
    script=release/'ops/macos/shopping/dev_order_https_proxy.py'
    if not script.is_file() or not python.is_file() or not private.is_dir():
        raise ValueError('DEV_PROXY_LAUNCH_PATH_INVALID')
    return plistlib.dumps({
        'Label':'com.aicontrolcenter.dev-order-https-proxy',
        'ProgramArguments':[str(python),str(script)],'WorkingDirectory':str(release),
        'EnvironmentVariables':{'PATH':'/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin','PYTHONPATH':str(release)},
        'RunAtLoad':True,'KeepAlive':True,'ThrottleInterval':10,
        'StandardOutPath':str(private/'https-proxy.log'),
        'StandardErrorPath':str(private/'https-proxy.log')})

if __name__=='__main__':
    from ops.macos.shopping.dev_order_runtime import assert_isolation
    assert_isolation()
    server=ThreadingHTTPServer(('127.0.0.1',18446),Handler)
    context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(ROOT/'dev-woo-cert.pem',ROOT/'dev-woo-key.pem')
    server.socket=context.wrap_socket(server.socket,server_side=True)
    server.serve_forever()
