(() => {
  'use strict';
  const phone = document.getElementById('aicc_phone');
  const code = document.getElementById('aicc_phone_code');
  const ticket = document.getElementById('aicc_phone_ticket');
  const consent = document.getElementById('aicc-phone-consent');
  const status = document.getElementById('aicc-phone-status');
  const send = document.getElementById('aicc-send-code');
  const check = document.getElementById('aicc-check-code');
  if (!phone || !code || !ticket || !status || !send || !check) return;
  let sentPhone = '';
  const message = value => { status.textContent = value; };
  const reset = () => { ticket.value = ''; sentPhone = ''; message(''); };
  phone.addEventListener('input', reset);
  send.addEventListener('click', async () => {
    ticket.value = '';
    const number = phone.value.trim();
    if (!number || !consent.checked) { message('휴대폰 번호와 인증 동의를 확인해 주세요.'); return; }
    send.disabled = true;
    message('인증번호를 요청하고 있습니다.');
    try {
      const response = await fetch('/__order-dev/phone/start', {
        method: 'POST', credentials: 'same-origin',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({phone: number, consent: true})
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message || '인증번호를 보내지 못했습니다.');
      sentPhone = number;
      message(data.message || '인증번호를 입력해 주세요.');
      code.focus();
    } catch (error) {
      message(error.message || '인증번호를 보내지 못했습니다. 잠시 후 다시 시도해 주세요.');
    } finally { send.disabled = false; }
  });
  check.addEventListener('click', async () => {
    if (!sentPhone || sentPhone !== phone.value.trim()) { message('먼저 인증번호를 요청해 주세요.'); return; }
    if (!/^[0-9]{4,10}$/.test(code.value.trim())) { message('인증번호를 확인해 주세요.'); return; }
    check.disabled = true;
    message('인증번호를 확인하고 있습니다.');
    try {
      const response = await fetch('/__order-dev/phone/check', {
        method: 'POST', credentials: 'same-origin',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({code: code.value.trim()})
      });
      code.value = '';
      if (!response.ok) throw new Error('인증번호가 맞지 않거나 만료되었습니다.');
      const proof = response.headers.get('X-AICC-Registration-Ticket');
      if (!proof || proof.length > 512 || !/^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/.test(proof)) throw new Error('인증 상태를 확인할 수 없습니다.');
      ticket.value = proof;
      message('휴대폰 인증이 완료되었습니다.');
    } catch (error) {
      ticket.value = '';
      message(error.message || '인증을 완료하지 못했습니다. 다시 시도해 주세요.');
    } finally { check.disabled = false; }
  });
})();