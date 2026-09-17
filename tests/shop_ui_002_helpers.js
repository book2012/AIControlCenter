/* Read-only JavaScriptCore unit checks. These are NOT browser/Playwright tests.
 * Run: jsc tests/shop_ui_002_helpers.js
 * Expose the IIFE's pure presentation functions before its browser bootstrap.
 */
const source = readFile("core/homepage/ui/storefront.js");
const bootstrap = "\n  if (isDetail) {";
if (source.split(bootstrap).length !== 2) throw new Error("Browser bootstrap boundary changed");
new Function(source
  .replace('const isDetail = Boolean(byId("detail-view"));', 'const isDetail = false;')
  .replace('const isHome = Boolean(byId("home-view"));', 'const isHome = false;')
  .replace(bootstrap, "\n  globalThis.presentation = { priceLabel, validateProduct, validatePage, validateCategories }; return;" + bootstrap))();
let count = 0;
function equal(actual, expected) {
  if (actual !== expected) throw new Error(`Expected ${expected}; received ${actual}`);
  count++;
}
function rejects(fn) {
  let rejected = false;
  try { fn(); } catch { rejected = true; }
  equal(rejected, true);
}
const product = { id: "42", name: "상품 이름", category: "TOP", description: "상품 설명", source: "woocommerce",
  price: "25000", currency: "KRW", in_stock: true, image_url: null };
for (const [price, currency, expected] of [
  ["25000", "KRW", "25,000원"], ["0", "KRW", "0원"], ["25000.00", "KRW", "25,000.00원"],
  ["9007199254740993.0100", "USD", "USD 9,007,199,254,740,993.0100"],
  ["0.000000000000000001", "USD", "USD 0.000000000000000001"],
]) equal(presentation.priceLabel({ ...product, price, currency }), expected);
for (const price of [null, 0, 1.5, "", "NaN", "Infinity", "-1", "1e10", "1x"]) {
  rejects(() => presentation.validateProduct({ ...product, price }));
}
for (const [field, value] of [["id", "../orders/1"], ["id", 42], ["name", ""], ["in_stock", "true"], ["description", {}], ["currency", "US"], ["image_url", {}]]) {
  rejects(() => presentation.validateProduct({ ...product, [field]: value }));
}
const text = '<img src=x onerror="alert(1)">';
equal(presentation.validateProduct({ ...product, name: text }).name, text);
const page = { items: [product], total: 1, page: 1, page_size: 12 };
equal(presentation.validatePage(page, 1, 12), page);
for (const invalid of [{ ...page, total: -1 }, { ...page, total: 1.5 }, { ...page, page: 2 },
  { ...page, items: [] }, { ...page, items: [product, product], total: 2 }, { ...page, total: 20 }]) {
  rejects(() => presentation.validatePage(invalid, 1, 12));
}
const empty = { items: [], total: 0, page: 1, page_size: 12 };
equal(presentation.validatePage(empty, 1, 12), empty);
const beyond = { items: [], total: 1, page: 2, page_size: 12 };
equal(presentation.validatePage(beyond, 2, 12), beyond);
const preview = { items: Array.from({ length: 4 }, (_, i) => ({ ...product, id: String(i + 1) })), total: 24, page: 1, page_size: 4 };
equal(presentation.validatePage(preview, 1, 4), preview);
rejects(() => presentation.validatePage({ ...preview, items: preview.items.slice(0, 3) }, 1, 4));
const categories = presentation.validateCategories({ items: [
  { id: "101", name: "NEW", slug: "new" }, { id: "102", name: "BEST", slug: "best" },
  { id: "103", name: "TOP", slug: "women-tops" }, { id: "104", name: "HOT", slug: "hot" },
] });
equal(categories.length, 3);
equal(categories[0].id, "101");
equal(categories[1].slug, "best");
equal(categories[2].label, "상의");
rejects(() => presentation.validateCategories(null));
rejects(() => presentation.validateCategories({ items: [{ id: "101" }] }));
rejects(() => presentation.validateCategories({ items: [categories[0], categories[0]] }));
print(`${count} JavaScriptCore helper checks: PASS (not browser validation)`);
