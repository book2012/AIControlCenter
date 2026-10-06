# One shared, product-tagged DEV chatbot presentation.
from html import escape as html_escape
def escape(value,quote=True):return html_escape(value,quote=quote).replace("{","&#123;").replace("}","&#125;")
def widget(service,context=''):
    from core.homepage.storefront import dev_orderable,product_data
    rows=[]
    for pid in sorted(dev_orderable(service)):
        try:p=product_data(service.get_product(pid))
        except Exception:continue
        if p['id']==pid:rows.append(p)
    if not rows:return ''
    allowed={p['id'] for p in rows};context=context if context in allowed else ''
    options='<option value="">상담할 상품을 선택해 주세요</option>'+''.join('<option value="'+escape(p['id'],quote=True)+'"'+(' selected' if p['id']==context else '')+'>'+escape(p['name'])+'</option>' for p in rows)
    return '''<button id="shop-chat-launcher" class="shop-chat-launcher" type="button" aria-controls="shop-chat" aria-haspopup="dialog">챗봇 상담</button>
<dialog id="shop-chat" aria-labelledby="shop-chat-title" data-context="CONTEXT">
<header><h2 id="shop-chat-title">agachichi 챗봇</h2><button id="shop-chat-close" type="button" aria-label="챗봇 닫기">닫기</button></header>
<label for="shop-chat-product">상담 상품</label><select id="shop-chat-product">OPTIONS</select>
<p id="shop-chat-tag" class="shop-chat-tag"></p><button id="shop-chat-stock" type="button">재고·사이즈 물어보기</button>
<div id="shop-chat-messages" role="log" aria-live="polite"></div>
<p>문의는 인증 없이 가능합니다. 전화번호·이름·주소는 질문에 적지 마세요.</p>
<form id="shop-chat-form"><label for="shop-chat-question">무엇이 궁금하세요?</label><input id="shop-chat-question" maxlength="500" required autocomplete="off"><button id="shop-chat-send" type="submit">보내기</button></form>
<button id="shop-chat-history" type="button">휴대폰 인증 · 최근 문의 내역</button>
<section id="shop-chat-phone" hidden><label>휴대폰 번호<input id="shop-chat-phone-number" type="tel" autocomplete="tel" maxlength="32"></label><label><input id="shop-chat-consent" type="checkbox">인증 문자 수신 동의</label><button id="shop-chat-sms" type="button">인증 문자 받기</button><label>인증번호<input id="shop-chat-code" inputmode="numeric" autocomplete="one-time-code" maxlength="10"></label><button id="shop-chat-verify" type="button">인증 확인</button></section><section id="shop-chat-recent" hidden aria-label="최근 문의 내역"></section>
<p id="shop-chat-error" role="alert"></p></dialog><script src="/homepage/assets/storefront-chat.js" defer></script>'''.replace('CONTEXT',escape(context,quote=True)).replace('OPTIONS',options)
