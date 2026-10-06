# SHOP color previews and unified purchase controls (DEV)

## Result
The 19 uploaded DEV products always show COLOR and SIZE. The two established coats show their known single color plus canonical S/M/L or M/L size variants. The 17 pending products show their registered colors and “사이즈 확인 중”; quantities do not invent a size or stock. Quantity is adjacent to the dimensions; cart/order buttons appear immediately below.

The shirt has two color front images and the mockneck knit has five. All single-color products bind their existing front to the declared color; existing sky-blue/gray fronts remain unchanged; five sibling JPEGs add alternate color previews. Images are AI references based on the uploaded palette, not evidence of actual color accuracy or fit.

## Boundaries
- gallery.json records a color_id bound to the DEV catalog and SHA256. Filenames, paths, symlinks, duplicate product/color bindings, and undeclared colors fail closed.
- The server escapes canonical labels and publishes only verified same-product image URLs. Browser preloads use a selection version; stale callbacks cannot overwrite the latest selection. A failed photo hides the previous color and displays a retry message.
- Preview buttons remain usable with stock zero. Disabled provider options and cart/order buttons keep pending stock blocked. COLOR preview is separate from purchase authorization.
- One quantity input and the original provider variation select remain available to existing guest checkout code. The provider select is hidden after successful integration; canonical buttons map to provider IDs by exact label. Actual selected provider options also synchronize the preview.
- Cart remains session-only; phone verification, address, preparation, confirmation, durable operation ledger and Telegram behavior are unchanged.
- Only homepage DEV needs activation. The order API remains on cbcada7079f5d00bdb38443bf0ea036c04d1d60a, with its current poller and private configuration untouched. No PROD/Caddy/WooCommerce mutation.

## Validation
- Test-first checks initially failed for missing color bindings and unified controls.
- 197 focused Python tests cover gallery/catalog/UI plus guest phone/checkout/order and Telegram regressions.
- Real Chrome on disposable HTTPS and fake providers checks all knit colors, shirt color-to-provider mapping with quantity 2, provider-to-thumbnail synchronization, stale callbacks, image failure/recovery, keyboard activation, mobile placement, cart persistence/edit invalidation and pending operation protection (15 checks, zero external requests/SMS).
- Shared chat browser regression confirms existing chat/history/stock and mobile behavior.
- After DEV activation, GET-only live Chrome checks all 19 products and 7 color front previews, unified controls, pending stock blocking, mobile and cart. No live order/SMS POST is possible through the test proxy.

## Activation and rollback
Archive the clean, pushed feature HEAD into a new immutable homepage-dev release. Verify the existing current manifest, listener command and cwd before changing current.json and restarting only the owned homepage listener. Preserve the old release and private manifest backup. Restore the previous manifest and owned listener if readiness fails. Do not restart the order API or its Telegram poller.

## Final assets and prompts
Built-in image_gen edit mode was used. Reference 1: existing matching model-front; reference 2: uploads/source/70634.jpg for the shirt or uploads/source/70628.jpg for the knit palette. JPEG conversion only resized/encoded the selected generated outputs at 800×1200, quality 85. Existing original/model assets are retained.

### ag-upload-top-0005-color-navy.jpg

Final repository path: brands/agachichi/assets/media/uploads/gallery/ag-upload-top-0005-color-navy.jpg

SHA256: c90d235da9e2ebbed90d0e619c13b1321f2a23a61c09248e18da3927a01a353a

Prompt: Use case: identity-preserve. Asset type: DEV shop color-option model-front photo. Image 1 is edit target; image 2 is color palette reference only. Change ONLY the shirt's blue vertical stripes to deep navy blue matching the navy striped shirt behind the foreground shirt in image 2. Keep the white stripes exactly white and preserve stripe width and geometry. Keep image 1's same model face, hair, body, front-facing pose, cream pants, shoes, light beige studio background, framing and lighting unchanged. Single full-body front photo, no collage, no text, no new branding. Output same portrait aspect ratio. This is an AI illustrative color preview.

### ag-upload-top-0006-color-ivory.jpg

Final repository path: brands/agachichi/assets/media/uploads/gallery/ag-upload-top-0006-color-ivory.jpg

SHA256: 9d3373eef9c974ff90447e827209f25698a3bcb3dbb1442f0a17c9813259d045

Prompt: Use case: identity-preserve. Asset type: DEV shop color-option model-front photo. Image 1 is edit target; image 2 is color palette reference only. Change ONLY the model's gray mockneck knit top to ivory matching that color garment in image 2. Preserve knit fabric texture and soft folds. Keep image 1's same model face, hair, body, front-facing pose, cream pants, shoes, light beige studio background, framing and lighting unchanged. Single full-body front photo, no collage, no text, no new branding. Output same portrait aspect ratio. This is an AI illustrative color preview.

### ag-upload-top-0006-color-brown.jpg

Final repository path: brands/agachichi/assets/media/uploads/gallery/ag-upload-top-0006-color-brown.jpg

SHA256: 7a10af8ad39701c9ede82d7a48c1eb98721afdca096056e6d69edbc883eae314

Prompt: Use case: identity-preserve. Asset type: DEV shop color-option model-front photo. Image 1 is edit target; image 2 is color palette reference only. Change ONLY the model's gray mockneck knit top to brown matching that color garment in image 2. Preserve knit fabric texture and soft folds. Keep image 1's same model face, hair, body, front-facing pose, cream pants, shoes, light beige studio background, framing and lighting unchanged. Single full-body front photo, no collage, no text, no new branding. Output same portrait aspect ratio. This is an AI illustrative color preview.

### ag-upload-top-0006-color-navy.jpg

Final repository path: brands/agachichi/assets/media/uploads/gallery/ag-upload-top-0006-color-navy.jpg

SHA256: 2abde5f6bf0e3146c2d9edfde4f5301f5f4bc3ff6ee25ee457ea1756f8cbfef2

Prompt: Use case: identity-preserve. Asset type: DEV shop color-option model-front photo. Image 1 is edit target; image 2 is color palette reference only. Change ONLY the model's gray mockneck knit top to navy matching that color garment in image 2. Preserve knit fabric texture and soft folds. Keep image 1's same model face, hair, body, front-facing pose, cream pants, shoes, light beige studio background, framing and lighting unchanged. Single full-body front photo, no collage, no text, no new branding. Output same portrait aspect ratio. This is an AI illustrative color preview.

### ag-upload-top-0006-color-black.jpg

Final repository path: brands/agachichi/assets/media/uploads/gallery/ag-upload-top-0006-color-black.jpg

SHA256: a0a39dab0662b3186e83afe9b96e119c28ac11d4f36ae460f450e79a0c3f7724

Prompt: Use case: identity-preserve. Asset type: DEV shop color-option model-front photo. Image 1 is edit target; image 2 is color palette reference only. Change ONLY the model's gray mockneck knit top to black matching that color garment in image 2. Preserve knit fabric texture and soft folds. Keep image 1's same model face, hair, body, front-facing pose, cream pants, shoes, light beige studio background, framing and lighting unchanged. Single full-body front photo, no collage, no text, no new branding. Output same portrait aspect ratio. This is an AI illustrative color preview.

