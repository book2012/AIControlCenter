# DEV second coat and HOT/UPDATE home

The original screenshot 70610.jpg was restored from its authoritative original because the interrupted base64 transfer contained an incomplete image. The original remains retained; the interrupted untracked file in the earlier worktree is preserved.

## Reviewed product
- Stable catalog ID: ag-upload-outer-0002; name: 오트밀 미니멀 롱 코트.
- Operator-supplied price: KRW 450000.
- Sizes M and L, initial stock one each.
- DEV Woo parent #41, variations M #42 / L #43, image #44, status publish.
- Category OUTER; visual tags 롱코트, 오트밀, 라이트베이지, 미니멀, 패치포켓, 가을, 겨울.
- Material composition and detailed measurements are not inferred from the photo.
- Price and actual availability at confirmation continue to come from WooCommerce.

## Media
Built-in image generation editing was used on the inspected original. The edit removes phone/social UI, neutralizes yellow lighting and presents the same photographed mannequin/coat against a subdued neutral background. No belt, buttons, new garment geometry or material composition was requested. AI retouch may introduce visual differences; retain the original for comparison and product accuracy review.
Project image: brands/agachichi/assets/media/uploads/ag-upload-outer-0002.jpg, validated by SHA-256 in the upload manifest.
Prompt: faithful ecommerce retouch of the existing oatmeal beige coat; remove all screen UI; preserve silhouette, opening, lapels, sleeves, crop, patch pockets, seams, texture and color; balanced natural light, subdued warm neutral background; no invented garment details, logos or writing.

## Home presentation
The DEV lookbook default now shows an explicit HOT editorial selection followed by the UPDATE/new-product feed. Both uploaded coats are explicitly assigned to hot/new. HOT means editorial recommendation, not inferred sales volume. The HOT filter reads only the validated explicit stable ID projection. Category/search pages remain available, including all 122 preview catalog records; seven are mapped to actual isolated DEV commerce. The original 120-item demo catalog is untouched.
The same storefront detail page includes the governed order panel. Existing phone, stock, Telegram and after-sales authorities remain unchanged.

## Registration and replay
The new narrowly scoped DEV registrar checks Docker/database isolation, the fixed approved price/inventory, media hash, SKU/catalog/image bindings and active mapping. A new product receives the initial stock once. Replay validates the published product and existing quantities and does not reset stock, create another product or reprice existing unrelated products. Partial/unknown creation fails closed for inspection rather than an automatic blind retry.
Actual initial registration returned #41; replay returned created=false with the same variations and M1/L1. Prior #36 and existing orders are preserved.

## Verification
154 focused preview/storefront/media regression tests passed with five existing deprecation warnings. Python syntax and git diff checks passed. Actual Woo registration and idempotent replay passed. Live immutable DEV code release 996382f1c6b08d8e2af7609ceda406b31838d5f4 is active. Read-only checks passed for the homepage UPDATE feed, second-coat detail, embedded product/size bindings, and order API poller RUNNING. Read-only Woo inspection confirmed #41 M1/L1 at KRW450000 and preserved #36 S1/M1/L1 at KRW300000. Full browser acceptance remains incomplete: isolated headless Chrome exceeded its 45-second timeout. No SMS, order, payment or Telegram send was performed by these acceptance checks. Production is not activated.
