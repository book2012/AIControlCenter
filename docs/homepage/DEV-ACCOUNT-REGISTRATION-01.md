# DEV Account Login and Registration

## Account experience

The DEV WooCommerce login page uses agachichi's warm ivory and brown palette.
It follows the device color preference: dark preference switches account and
registration pages to a dark brown-black surface with warm text and accent buttons.
The storefront header places a 회원가입 link beside LOGIN, and `/my-account/register/` is a
dedicated registration page.

Registration requests the member's name, nickname, mobile number, email, home
address, and a password chosen by the member. The 주소 검색 button opens a
Kakao Postcode modal; a selected five-digit postcode and road/jibun base address
are required and stored in WooCommerce billing/shipping profile metadata. Detailed
address remains a separate customer-entered field. This avoids users mistyping
the administrative-area/base address while preserving their apartment/unit entry.
A login attempt for an unknown
username or email opens a registration prompt; a known account with a wrong
password continues to receive the normal login error. WooCommerce remains the
account and profile store. Name, nickname,
verified phone, billing address, and shipping address are saved to the DEV
customer record. Existing WooCommerce password handling remains enabled.

Social sign-in is outside this first DEV registration step.

## Phone verification

The signup form sends and checks an SMS through the existing DEV-only Twilio
Verify bridge. The order service signs a short-lived ticket containing the
verified phone, audience, expiry, and random nonce with an Ed25519 key derived from the
DEV-only binding secret. WordPress verifies the signature offline using a
public key, matches the submitted phone, and atomically records the nonce to
prevent replay. Tickets expire after five minutes; the WordPress container
does not need network access to the Mac host API.

The current DEV bridge intentionally accepts only the configured test phone.
It retains its existing request limits and sends no SMS until a visitor
requests a code. PROD phone configuration and routes are unchanged.

## DEV routing

The DEV ingress retains Basic Auth and noindex headers. The account page routes
to isolated DEV WordPress; /__order-dev/* verification requests route to the
isolated DEV order service. The account page is not part of the Homepage HTML
release.

## Validation

The phone bridge test covers origin and consent, verified customer session,
signed ticket issue, phone binding, expiry, and replay denial. Homepage tests
cover insertion of LOGIN and the neighboring 회원가입 link. PHP syntax and
account form rendering are checked in the DEV WordPress container. Address-search
markup, postcode persistence, and phone-bound registration validation are part
of the form contract. Focused Homepage tests also verify that LOGIN inherits the
same text-only navigation style as the other header links.
