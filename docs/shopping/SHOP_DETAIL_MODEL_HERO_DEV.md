# DEV detailed explanation and model hero


## DEV detail explanation and model image visibility
Removed the separate chatbot button below SIZE. Detailed explanation and the message "제품 문의는 챗봇으로 해주세요." precede the order panel. The two uploaded coats now show their labeled AI model-angle image immediately as the PDP hero; original photos remain in the detail gallery. Home catalog images and commerce/stock records are unchanged. 156 focused regression tests and seven isolated Chrome checks passed. DEV only; existing dirty work and PROD are preserved.

The former gallery was below the full detail/order layout while the hero retained the previous image. This made the new model photos easy to miss. The two coat PDP heroes now use the already validated model-angle JPEG with an explicit AI reference caption. Uploaded originals and the full gallery remain available. The floating common chatbot still attaches the current supported product; no new separate product inquiry control is introduced. Browser provider calls are mocked in the regression harness; live activation checks follow immutable task-only commit.

Live DEV homepage code release: 7e9264798bac63ed5aa1c564b97257acf5933167. Both coat hero JPEGs returned HTTP200 and original photos remained present. Actual live Chrome through a GET-only loopback proxy confirmed the visible model hero, 상세설명, inquiry guidance, current-product chatbot tag, image loading and initialized order controls. No order/SMS/payment POST occurred. The existing DEV order API remains on unchanged compatible release 0a95c8db1b96872635bfcbfcc4cdb2e04cb03fd7.
