"""Explicit pinned DEV-only TLS transport. No environment or endpoint defaults."""
from urllib.parse import urlsplit
import requests

class PinnedDevWooOrderSession:
    def __init__(self,certificate):
        self.certificate=str(certificate)
        self._session=requests.Session();self._session.trust_env=False
    @staticmethod
    def endpoint(url):
        parsed=urlsplit(url)
        if (parsed.scheme!='https' or parsed.netloc!='localhost' or parsed.query or parsed.fragment
            or not __import__('re').fullmatch(r'/wp-json/wc/v3/orders(?:/[1-9][0-9]*)?',parsed.path)):
            raise ValueError('DEV_ORDER_ENDPOINT_DENIED')
        return 'https://localhost:18446'+parsed.path
    def post(self,url,**kwargs):return self._session.post(self.endpoint(url),verify=self.certificate,**kwargs)
    def get(self,url,**kwargs):return self._session.get(self.endpoint(url),verify=self.certificate,**kwargs)
