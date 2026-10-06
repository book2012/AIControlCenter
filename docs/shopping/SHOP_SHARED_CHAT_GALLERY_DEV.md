# Shared product chatbot, private inquiry history and coat gallery — DEV

## Behavior
One common chatbot dialog is available on the DEV home, search, product detail and my-orders pages. The seven real DEV commerce products can be selected there. A supported product detail opens the same dialog with its stable catalog ID selected and visible product tag; a guarded GET embed resolves the allowed Woo product ID before an inquiry POST. The bot asks what the customer wants to know. Local AI and existing operator Telegram escalation/approved FAQ remain the answer authorities. The embedded order panel now contains order controls rather than another product inquiry form.

Conversation text and the selected product are retained in bounded sessionStorage in the same tab across page navigation and reload. Closing the dialog keeps the conversation; closing the tab ends the local session. Pending operator reply checks resume after navigation. Browser-provided text is displayed through textContent. No OTP, customer session cookie, CSRF token or shipping data is saved in chat sessionStorage.

A separate private DEV chat-history SQLite database records new product inquiries and responses after browser conversation setup. A Secure HttpOnly SameSite=Strict session cookie identifies the anonymous browser conversation. Anonymous possession does not authorize customer history. Phone session authority and CSRF are required to attach the current browser conversation; ownership cannot be reassigned. An authenticated read returns at most 30 entries from the last 30 days belonging only to that customer. The DEV authority remains the existing single configured verified guest identity; synthetic fixtures cannot read its history. Operator answers in recent history are resolved server-side. No client-supplied answer or phone number chooses an owner.

The chatbot includes explicit phone verification controls for recent history. No SMS, order or payment is triggered just by opening it. Past anonymous inquiries without ownership evidence are not retroactively assigned. Existing order/stock and after-sales authorities are unchanged.

## Two coat galleries
Each recent coat detail preserves the existing representative image and adds the user's original upload plus one AI model lookbook containing front, side and rear views.
- ag-upload-outer-0001: 70603.jpg original, camel belted coat; KRW300000; S/M/L one each.
- ag-upload-outer-0002: 70610.jpg original, oatmeal minimalist coat; KRW450000; M/L one each.

Original uploads and AI images have separate captions. AI unseen-angle/fit estimates are explicitly labeled and cannot establish material, measurements or hidden construction. The original files remain available for comparison. Gallery assets are local, exact-manifest and SHA-256 bound; absent, malformed, cross-environment, escaped or corrupt entries fail closed.

Final project assets: brands/agachichi/assets/media/uploads/gallery/ag-upload-outer-0001-original.jpg, ag-upload-outer-0001-model-angles.jpg, ag-upload-outer-0002-original.jpg, ag-upload-outer-0002-model-angles.jpg.

## Image prompt set
Built-in imagegen editing/compositing was used; no CLI/API key was used. Camel coat: one horizontal triptych of the same fictional adult female model, front/three-quarter/back, preserving reference camel color, long drape, wide lapels, patch pockets, long sleeves and self-fabric belt; neutral trousers/shoes, soft neutral studio; remove phone UI, no logos/text or material claims. Oatmeal coat: same layout, preserving broad notched lapels, straight oversized open front, large patch pockets, plain long sleeves, oatmeal texture; no belt/buttons or invented decorations. Unknown rear construction is a plain illustrative estimate. Output JPEG resizing/encoding only preserves the generated triptych; originals are not retouched or overwritten.

## Validation and activation
193 focused regression tests passed. Isolated real Chrome passed six acceptance checks: bot asks first, correct product inquiry binding, navigation history/current PDP tag, reload persistence, authenticated recent-history presentation, mobile dialog. Chrome inquiry/auth endpoints were local fakes; zero external provider calls and zero mock SMS requests. Backend tests independently cover anonymous denial, CSRF, ownership isolation, synthetic-account denial, retention, bounds, private file permissions and server-authoritative operator replies.
DEV activation uses a clean task-only immutable Git archive, preserving existing dirty work and PROD. Live activation evidence is recorded separately after deployment. No real SMS/order/payment/carrier event is claimed by these checks.
