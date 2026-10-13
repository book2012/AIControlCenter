(() => {
  'use strict';
  document.querySelectorAll('[data-aicc-confirm]').forEach(control => {
    control.addEventListener(control.tagName === 'FORM' ? 'submit' : 'click', event => {
      if (!window.confirm(control.dataset.aiccConfirm || '계속 진행할까요?')) event.preventDefault();
    });
  });
  const signupForm = document.querySelector('.aicc-registration-form');
  const username = document.getElementById('aicc_signup_username');
  const usernameCheck = document.getElementById('aicc-check-username');
  const usernameStatus = document.getElementById('aicc-username-status');
  let checkedUsername = '';
  if (signupForm && username && usernameCheck && usernameStatus) {
    username.addEventListener('input', () => {
      checkedUsername = '';
      usernameStatus.textContent = '';
    });
    usernameCheck.addEventListener('click', async () => {
      if (!username.reportValidity()) return;
      usernameCheck.disabled = true;
      usernameStatus.textContent = '아이디 사용 여부를 확인하고 있습니다.';
      try {
        const response = await fetch(window.AICCAccountConfig.ajaxUrl, {
          method: 'POST', credentials: 'same-origin',
          headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
          body: new URLSearchParams({
            action: 'aicc_check_username',
            nonce: window.AICCAccountConfig.usernameNonce,
            username: username.value.trim()
          })
        });
        const result = await response.json();
        if (!response.ok || !result.success || !result.data) throw new Error('아이디를 확인하지 못했습니다. 다시 시도해 주세요.');
        checkedUsername = result.data.available ? username.value.trim() : '';
        usernameStatus.textContent = result.data.message;
      } catch (error) {
        checkedUsername = '';
        usernameStatus.textContent = error.message || '아이디를 확인하지 못했습니다. 다시 시도해 주세요.';
      } finally {
        usernameCheck.disabled = false;
      }
    });
    signupForm.addEventListener('submit', event => {
      if (checkedUsername !== username.value.trim()) {
        event.preventDefault();
        usernameStatus.textContent = '회원가입 전에 아이디 중복 확인을 완료해 주세요.';
        usernameCheck.focus();
      }
    });
  }
  const password = document.getElementById('aicc_signup_password');
  const passwordConfirm = document.getElementById('aicc_signup_password_confirm');
  const passwordStatus = document.getElementById('aicc-password-status');
  if (password && passwordConfirm && passwordStatus) {
    const comparePasswords = () => {
      const mismatch = passwordConfirm.value !== '' && password.value !== passwordConfirm.value;
      passwordConfirm.setCustomValidity(mismatch ? '비밀번호가 서로 일치하지 않습니다.' : '');
      passwordStatus.textContent = passwordConfirm.value === '' ? '' : mismatch ? '비밀번호가 서로 다릅니다.' : '비밀번호가 일치합니다.';
    };
    password.addEventListener('input', comparePasswords);
    passwordConfirm.addEventListener('input', comparePasswords);
  }
  const phone = document.getElementById('aicc_phone');
  const code = document.getElementById('aicc_phone_code');
  const ticket = document.getElementById('aicc_phone_ticket');
  const consent = document.getElementById('aicc-phone-consent');
  const status = document.getElementById('aicc-phone-status');
  const send = document.getElementById('aicc-send-code');
  const check = document.getElementById('aicc-check-code');
  const signupDialog = document.getElementById('aicc-signup-dialog');
  if (signupDialog && window.HTMLDialogElement) {
    signupDialog.showModal();
    signupDialog.querySelector('.aicc-dialog-close')?.addEventListener('click', () => signupDialog.close());
    signupDialog.querySelector('.aicc-dialog-later')?.addEventListener('click', () => signupDialog.close());
    signupDialog.addEventListener('click', event => {
      if (event.target === signupDialog) signupDialog.close();
    });
  }
  const addressButton = document.getElementById('aicc-address-search');
  const addressDialog = document.getElementById('aicc-postcode-dialog');
  if (addressButton && addressDialog) {
    let postcodeLoader;
    const loadPostcode = () => {
      if (window.kakao?.Postcode) return Promise.resolve();
      if (postcodeLoader) return postcodeLoader;
      postcodeLoader = new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = 'https://t1.kakaocdn.net/mapjsapi/bundle/postcode/prod/postcode.v2.js';
        script.async = true;
        script.onload = () => window.kakao?.Postcode ? resolve() : reject(new Error('주소 검색 서비스를 불러오지 못했습니다.'));
        script.onerror = () => reject(new Error('주소 검색 서비스를 불러오지 못했습니다.'));
        document.head.appendChild(script);
      });
      return postcodeLoader;
    };
    const closeAddress = () => {
      if (addressDialog.open) addressDialog.close();
      document.getElementById('aicc-postcode-frame')?.replaceChildren();
    };
    addressButton.addEventListener('click', async () => {
      const frame = document.getElementById('aicc-postcode-frame');
      try {
        await loadPostcode();
        frame.replaceChildren();
        addressDialog.showModal();
        new window.kakao.Postcode({
          oncomplete: data => {
            const address = data.userSelectedType === 'J' ? data.jibunAddress : data.roadAddress;
            if (!/^[0-9]{5}$/.test(data.zonecode || '') || !address) return;
            document.getElementById('aicc_postcode').value = data.zonecode;
            document.getElementById('aicc_address').value = address;
            closeAddress();
            document.getElementById('aicc_address_detail')?.focus();
          },
          width: '100%', height: '100%'
        }).embed(frame);
      } catch (error) {
        closeAddress();
        const status = document.getElementById('aicc-phone-status');
        if (status) status.textContent = error.message || '주소 검색을 열지 못했습니다.';
      }
    });
    document.getElementById('aicc-address-close')?.addEventListener('click', closeAddress);
    addressDialog.addEventListener('click', event => {
      if (event.target === addressDialog) closeAddress();
    });
    addressDialog.addEventListener('close', () => {
      document.getElementById('aicc-postcode-frame')?.replaceChildren();
      if (document.activeElement !== document.getElementById('aicc_address_detail')) addressButton.focus();
    });
  }
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