"""DEV customer/operator message presentation; fixed authorized Telegram transport."""
from core.shopping.order_core.telegram import OrderTelegramTransport,TelegramDeliveryRejected
GREETING="안녕하세요 agachichi 입니다"
def greeting(text):
    return text if text.startswith(GREETING) else GREETING+"\n"+text
def chunks(text):
    if type(text) is not str or not text:raise TelegramDeliveryRejected("MESSAGE_BOUNDS")
    prefix=GREETING+"\n";body=text[len(prefix):] if text.startswith(prefix) else text
    current="";units=0
    for char in body:
        size=2 if ord(char)>0xffff else 1
        if units+size>3500:
            yield prefix+current;current="";units=0
        current+=char;units+=size
    if current:yield prefix+current
class DevTelegramTransport(OrderTelegramTransport):
    def send_message(self,text):
        receipt=None
        for chunk in chunks(text):receipt=super().send_message(chunk)
        return receipt
