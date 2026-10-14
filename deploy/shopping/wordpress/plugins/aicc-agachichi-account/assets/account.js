(() => {
  'use strict';
  document.querySelectorAll('[data-aicc-confirm]').forEach(control => {
    if (control.matches('.header-logout')) return;
    control.addEventListener(control.tagName === 'FORM' ? 'submit' : 'click', event => {
      if (!window.confirm(control.dataset.aiccConfirm || '계속 진행할까요?')) event.preventDefault();
    });
  });
  document.querySelectorAll('.header-logout').forEach(control => {
    control.addEventListener('click', async event => {
      event.preventDefault();
      if (!window.confirm(control.dataset.aiccConfirm || '로그아웃하시겠습니까?')) return;
      control.setAttribute('aria-disabled', 'true');
      try {
        const response = await fetch(window.AICCAccountConfig.ajaxUrl, {
          method: 'POST', credentials: 'same-origin', cache: 'no-store',
          headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', Accept: 'application/json'},
          body: new URLSearchParams({action: 'aicc_account_logout', nonce: window.AICCAccountConfig.logoutNonce || ''})
        });
        const result = await response.json();
        if (!response.ok || !result.success || result.data?.loggedOut !== true) throw new Error();
        window.location.assign('/homepage/storefront/');
      } catch (_) {
        control.removeAttribute('aria-disabled');
        window.alert('로그아웃하지 못했습니다. 페이지를 새로고침한 뒤 다시 시도해 주세요.');
      }
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

  if (window.AICCAccountConfig?.accountRecoveryEnabled === true) {
    const api = String(window.AICCAccountConfig.recoveryApi || '/v1/shop/account-recovery').replace(/\/$/, '');
    const cleanPhone = value => {
      const digits = value.replace(/\D/g, '');
      if (digits.startsWith('010') && digits.length === 11) return '+82' + digits.slice(1);
      if (digits.startsWith('8210') && digits.length === 12) return '+' + digits;
      if (value.startsWith('+8210') && digits.length === 12) return '+' + digits;
      return '';
    };
    const post = async (path, value) => {
      const response = await fetch(api + path, {
        method: 'POST', credentials: 'same-origin', cache: 'no-store',
        headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
        body: JSON.stringify(value)
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error('요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.');
      return result;
    };
    document.querySelectorAll('form[data-aicc-recovery="id"]').forEach(form => {
      const status = form.querySelector('[role="status"]');
      const codeStep = form.querySelector('[data-aicc-code-step]');
      const codeInput = form.elements.code;
      let challenge = '';
      let requestAttempted = false;
      let confirmationPending = false;
      const requestButton = form.querySelector('button[type=submit]');
      const confirmButton = form.querySelector('[data-aicc-id-confirm]');
      form.addEventListener('submit', async event => {
        event.preventDefault();
        if (requestAttempted) return;
        const phone = cleanPhone(form.elements.phone.value.trim());
        if (!phone) { status.textContent = '휴대폰 번호를 다시 확인해 주세요.'; return; }
        requestAttempted = true;
        requestButton.disabled = true;
        status.textContent = '인증번호 요청을 처리하고 있습니다.';
        try {
          const result = await post('/id-challenge', {name: form.elements.name.value.trim(), phone});
          challenge = typeof result.challenge === 'string' ? result.challenge : '';
          codeStep.hidden = false;
          codeInput.focus();
          status.textContent = '요청을 접수했습니다. 입력한 정보가 확인되면 등록된 휴대폰으로 인증번호가 전송됩니다.';
        } catch (error) { status.textContent = '요청 결과를 확인할 수 없습니다. 같은 요청을 다시 보내지 말고 잠시 후 확인해 주세요.'; }
      });
      confirmButton?.addEventListener('click', async () => {
        if (confirmationPending) return;
        const phone = cleanPhone(form.elements.phone.value.trim());
        const code = codeInput.value.trim();
        if (!challenge || !phone || !/^[0-9]{4,10}$/.test(code)) {
          status.textContent = '인증번호를 확인해 주세요.'; return;
        }
        confirmationPending = true;
        confirmButton.disabled = true;
        status.textContent = '아이디를 확인하고 있습니다.';
        try {
          const result = await post('/id-confirm', {challenge, phone, code});
          codeInput.value = '';
          status.textContent = result.state === 'FOUND' && typeof result.login_id === 'string'
            ? '회원님의 아이디는 ' + result.login_id + ' 입니다.'
            : '정보를 확인하지 못했습니다. 입력 내용을 확인해 주세요.';
          challenge = '';
        } catch (error) { status.textContent = '인증 결과를 확인하지 못했습니다. 요청을 반복하지 말고 잠시 후 다시 확인해 주세요.'; }
      });
    });
    document.querySelectorAll('form[data-aicc-recovery="password"]').forEach(form => {
      const status = form.querySelector('[role="status"]');
      let requestAttempted = false;
      const requestButton = form.querySelector('button[type=submit]');
      form.addEventListener('submit', async event => {
        event.preventDefault();
        if (requestAttempted) return;
        const phone = cleanPhone(form.elements.phone.value.trim());
        if (!phone) { status.textContent = '휴대폰 번호를 다시 확인해 주세요.'; return; }
        requestAttempted = true;
        requestButton.disabled = true;
        status.textContent = '요청을 처리하고 있습니다.';
        try {
          await post('/password-reset', {
            login_id: form.elements.login_id.value.trim(),
            name: form.elements.name.value.trim(), phone
          });
          status.textContent = '입력한 정보와 일치하는 계정이 있으면 비밀번호 재설정 링크를 문자로 보내드립니다.';
        } catch (error) { status.textContent = '요청 결과를 확인할 수 없습니다. 같은 요청을 다시 보내지 말고 잠시 후 확인해 주세요.'; }
      });
    });
    const resetPage = document.querySelector('[data-aicc-reset-token]');
    const resetForm = document.querySelector('form[data-aicc-recovery="complete"]');
    if (resetPage && resetForm) {
      const token = resetPage.dataset.aiccResetToken || '';
      if (window.history?.replaceState) window.history.replaceState(null, '', window.location.pathname);
      resetPage.dataset.aiccResetToken = '';
      const status = resetForm.querySelector('[role="status"]');
      let resetAttempted = false;
      const resetButton = resetForm.querySelector('button[type=submit]');
      resetForm.addEventListener('submit', async event => {
        event.preventDefault();
        if (resetAttempted) return;
        const password = resetForm.elements.password.value;
        if (!token || password.length < 8 || password !== resetForm.elements.confirm.value) {
          status.textContent = '비밀번호를 확인해 주세요. 두 입력이 같고 8자 이상이어야 합니다.'; return;
        }
        resetAttempted = true;
        resetButton.disabled = true;
        status.textContent = '비밀번호를 변경하고 있습니다.';
        try {
          const result = await post('/password-reset/complete', {token, new_password: password});
          resetForm.reset();
          status.textContent = result.state === 'COMPLETED'
            ? '비밀번호가 변경되었습니다. 로그인해 주세요.'
            : '링크가 만료되었거나 이미 사용되었습니다. 다시 요청해 주세요.';
        } catch (error) { status.textContent = '변경 결과를 확인하지 못했습니다. 링크를 반복 사용하지 말고 로그인 화면에서 상태를 확인해 주세요.'; }
      });
    }
  }
})();
