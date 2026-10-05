"""Pinned loopback HTTPS facade for isolated DEV WooCommerce only."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import ssl
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

if __name__=='__main__':
    server=ThreadingHTTPServer(('127.0.0.1',18446),Handler)
    context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(ROOT/'dev-woo-cert.pem',ROOT/'dev-woo-key.pem')
    server.socket=context.wrap_socket(server.socket,server_side=True)
    server.serve_forever()
