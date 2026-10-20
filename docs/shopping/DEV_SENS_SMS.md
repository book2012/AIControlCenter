# DEV Korean sender SMS: Naver Cloud SENS

## Scope

AIControlCenter keeps the fixed DEV test recipient and owns both the OTP verifier and order notification outbox. SENS sends SMS/LMS and reports carrier delivery. PROD remains isolated. Twilio Verify and the DEV preview remain active until the SENS credentials and sender are validated.

## Account prerequisites

1. Create a Naver Cloud SENS SMS project and obtain its service ID.
2. Register a phone number owned by the business or operator, with ownership documents, in **SMS > Calling Number**. Confirm it is approved and is not enrolled in number spoofing prevention blocking web/SMS sends.
3. Create an access key and secret key with access to the SENS project. Do not paste them into chat or commit them.
4. Set the private Mac file `/Users/kyouhan/.config/aicontrolcenter-dev-order/sens.private.json` to mode `0600`:
   ```json
   {
     "environment": "DEV",
     "provider": "NCP_SENS",
     "enabled": true,
     "service_id": "ncp:sms:kr:YOUR_SERVICE_ID:sens",
     "sender_number": "YOUR_APPROVED_KOREAN_NUMBER",
     "credentials": {
       "access_key": "YOUR_ACCESS_KEY",
       "secret_key": "YOUR_SECRET_KEY"
     }
   }
   ```
5. After read-only setup validation, switch the private `phone-verification.private.json` provider from `twilio_verify` to `sens_sms`; retain the one approved `test_phone` and binding key. Restart only the DEV API release containing this code. An OTP is six digits, expires after five minutes, and is stored as an HMAC, never as plaintext. An ambiguous send is not retried.
6. For order notification activation, replace the synthetic bank details in `order-notification.private.json` with the real deposit details, set provider `NCP_SENS`, and exit `DEV_PREVIEW`. The private SENS file must also be enabled. Existing historical orders never backfill; use a deliberate operator resend for one paid DEV order, then check the carrier result before allowing new-order dispatch.

## Status as of 2026-10-20

The SENS adapter, fixed-recipient OTP port, and order notification reconciliation are implemented and covered by offline tests. No Naver Cloud credentials, project, or approved sender are present on this Mac. The DEV runtime remains on Twilio Verify for authentication and DEV_PREVIEW for order notices. No SENS request has been sent.

SENS API: [send](https://api.ncloud-docs.com/docs/sens-sms-send), [delivery result](https://api.ncloud-docs.com/docs/sens-sms-get), [sender registration](https://guide.ncloud-docs.com/docs/sens-callingno).
