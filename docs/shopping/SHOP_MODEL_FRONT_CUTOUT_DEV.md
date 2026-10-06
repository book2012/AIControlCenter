# DEV front model cards and garment detail


## DEV front model thumbnails and clean garment detail
The two uploaded coats use a single front-facing model portrait in HOT, UPDATE, search cards and PDP hero. Detail order is hero → 상세설명 → background-removed garment retouch → other model angles → order controls. Raw upload screenshots are retained for provenance but are not rendered. Transparent WebP cutouts preserve alpha; model shots share the same neutral studio tone. 158 focused regressions and seven isolated Chrome chatbot checks passed. No commerce stock or PROD mutation.

## Assets and provenance
Each coat has three new sibling assets in brands/agachichi/assets/media/uploads/gallery/: ag-upload-outer-0001-model-front.jpg, ag-upload-outer-0001-garment-cutout.webp, ag-upload-outer-0001-model-other.jpg; corresponding 0002 assets use the same naming. Existing original and prior model files are preserved. Exact filename, category-independent stable product ID, SHA256 and media type are validated; unknown or corrupt media fails closed. Representative front mapping is presentation-only and does not change Woo product, stock or order authorities.

## Built-in imagegen prompt set
Front portraits: use only the reference left/front model view as a 2:3 centered head-to-shoes portrait; preserve adult model, garment silhouette/color/texture, lapels, pockets, belt on camel only, no collage/text, same neutral studio. Garment retouch: remove phone/social writing/icons, environment, people/mannequin and accessories from original upload; isolate the coat on genuine transparency, preserve observed garment structure and color, normalize lighting and modestly clarify texture; no invented buttons, belt on oatmeal or material claims. Other views: retain only reference side/back views, same model and styling, neutral studio, no writing. AI edits may reconstruct occluded areas; captions distinguish edited garment photos and illustrative model views. JPEG/WebP resizing and encoding are the only subsequent pixel operations; transparent alpha was verified locally.

## Validation
158 focused regression tests passed. Existing seven isolated real Chrome chat/context/persistence/history/mobile checks passed with local fake inquiry/auth and zero external provider calls. Exact card/PDP front bindings, garment-before-other layout, original archival preservation and transparent WebP MIME are covered. Live DEV acceptance follows clean immutable Git archive activation.

## DEV activation and acceptance
Active homepage immutable release: c8f52f29d323023dc51abbdd2985dc917c941d8c. Git archive provenance and clean source were verified before activation. Both coats have front thumbnails in HOT/UPDATE, correct PDP sequence, no rendered raw original, and exact served asset SHA/MIME. Actual isolated Chrome against live DEV services passed 14 image/chat/order-initialization assertions through a GET-only proxy; no SMS, order or payment POST. DEV API remained on 0a95c8db1b96872635bfcbfcc4cdb2e04cb03fd7 and Telegram poller remained RUNNING. PROD and existing dirty work were untouched. Documentation-only closure commit is not a runtime redeployment. Evidence: SHOP_MODEL_FRONT_CUTOUT_DEV_VALIDATION.json.
