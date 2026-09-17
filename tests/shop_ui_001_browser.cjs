/* SHOP_UI_002 offline browser checks against exported canonical FastAPI fixtures.
 * Retains the SHOP_UI_001 runner path. No server or packages are installed.
 * node tests/shop_ui_001_browser.cjs FIXTURES.json OUTPUT_DIR [CHROME_EXECUTABLE]
 */
const assert = require("node:assert/strict");
const fs = require("node:fs/promises");
const path = require("node:path");
let chromium;
try { ({ chromium } = require("playwright")); }
catch { console.log("NOT_RUN: Playwright is unavailable; no browser checks executed."); process.exitCode = 77; }

async function main() {
  const [fixtureFile, output, executablePath] = process.argv.slice(2);
  const fixtures = JSON.parse(await fs.readFile(fixtureFile, "utf8"));
  const root = path.resolve(__dirname, "..");
  const photoRoot = path.join(root, "deploy/shopping/wordpress/plugins/ai-shopping-storefront/assets/demo/orange-coco-v1/products");
  const origin = "http://shop-ui-002.test";
  const home = "/homepage/storefront";
  const listing = `${home}/search`;
  const productID = "oc-demo-top-0001";
  const detail = `${home}/product/${productID}`;
  const canonical = (value) => {
    const url = new URL(value, origin);
    if (url.pathname.startsWith(home)) {
      if (url.searchParams.get("page") === "1") url.searchParams.delete("page");
      for (const key of ["category", "q"]) if (url.searchParams.get(key) === "") url.searchParams.delete(key);
    }
    url.searchParams.sort();
    return url.pathname + url.search;
  };
  const responses = new Map(Object.entries(fixtures).map(([url, response]) => [canonical(url), response]));
  await fs.mkdir(output, { recursive: true });
  let browser;
  try {
    browser = await chromium.launch({ executablePath, headless: true,
      args: ["--disable-background-networking", "--no-first-run", "--no-default-browser-check", "--host-resolver-rules=MAP * ~NOTFOUND"] });
  } catch (error) {
    console.log(`NOT_RUN: browser launch unavailable (${error.name}); no browser checks executed.`);
    process.exitCode = 77;
    return;
  }
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: "reduce", serviceWorkers: "block" });
  const requests = [], unexpected = [], errors = [], checks = [];
  let mode = "normal", held;
  await context.route("**/*", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    requests.push({ method: request.method(), path: url.pathname + url.search, origin: url.origin });
    if (url.origin !== origin || request.method() !== "GET") { unexpected.push(request.url()); return route.abort(); }
    const photo = url.pathname.match(/^\/homepage\/assets\/storefront\/photos\/(top|bottom|outer|dress|bag|acc)\/(oc-demo-\1-[0-9]{4}\.jpg)$/);
    if (photo) {
      if (mode === "broken-photo") return route.fulfill({ status: 404, body: "" });
      return route.fulfill({ contentType: "image/jpeg", body: await fs.readFile(path.join(photoRoot, photo[1], photo[2])) });
    }
    if (url.pathname === "/homepage/assets/storefront/hero-boutique.jpg") {
      return route.fulfill({ contentType: "image/jpeg", body: await fs.readFile(path.join(root, "brands/orange-coco/assets/media/storefront/hero-boutique.jpg")) });
    }
    if (url.pathname === "/favicon.ico") return route.fulfill({ status: 204 });
    const lookup = new URL(url);
    if (mode === "numeric-category" && lookup.searchParams.get("category") === "101") lookup.searchParams.set("category", "women-tops");
    const response = responses.get(canonical(lookup.href));
    if (!response) { unexpected.push(url.pathname + url.search); return route.abort(); }
    if (url.pathname === "/shopping/categories") {
      if (mode === "badge-failure") return route.fulfill({ status: 503, body: "{}" });
      const payload = JSON.parse(response.body);
      if (mode === "missing-collections") payload.items = payload.items.filter((item) => !["new", "best"].includes(item.slug));
      if (mode === "numeric-category") payload.items.find((item) => item.slug === "women-tops").id = "101";
      // A forbidden promotional category must never become a UI badge/control.
      payload.items.push({ id: "forbidden-promotion", name: "HOT", slug: "hot", count: 1 });
      return route.fulfill({ ...response, body: JSON.stringify(payload) });
    }
    const catalog = ["/shopping/products", "/shopping/search"].includes(url.pathname) && ["4", "12"].includes(url.searchParams.get("page_size"));
    const product = url.pathname.startsWith("/shopping/products/");
    if ((catalog || product) && response.status === 200) {
      if (mode === "partial-home" && url.searchParams.get("category") === "best" && url.searchParams.get("page_size") === "4") return route.fulfill({ status: 503, body: "{}" });
      if (mode === "unavailable") return route.fulfill({ status: 503, body: "{}" });
      if (mode === "network-failure") return route.abort();
      if (mode === "timeout") return;
      if (mode === "race" && catalog && url.searchParams.get("category") === "women-tops") { held = { route, response }; return; }
      if (mode === "invalid-json") return route.fulfill({ contentType: "application/json", body: "{" });
      const payload = JSON.parse(response.body);
      if (mode === "empty" && catalog) { payload.items = []; payload.total = 0; }
      if (mode === "malformed") { if (catalog) payload.total = -1; else payload.id = "mismatched-id"; }
      if (mode === "hostile") Object.assign(product ? payload : payload.items[0], {
        name: '<img src=x onerror="alert(1)">', description: '<script>alert(1)</script>\n정확한 상품 설명',
        price: "9007199254740993.0100", currency: "USD", image_url: "https://untrusted.invalid/photo.jpg",
      });
      return route.fulfill({ ...response, body: JSON.stringify(payload) });
    }
    // Fault modes exercise the existing canonical enhancement/retry path;
    // normal navigation tests use the complete server-rendered response.
    if (response.contentType.startsWith("text/html") && !["normal", "numeric-category", "race", "broken-photo", "badge-failure"].includes(mode)) {
      return route.fulfill({ ...response, body: response.body.replace('data-server-rendered="true"', 'data-server-rendered=""') });
    }
    return route.fulfill(response);
  });
  const page = await context.newPage();
  page.on("pageerror", (error) => errors.push(error.message));
  const settled = () => page.waitForFunction(() => {
    if (document.getElementById("home-view")) return [...document.querySelectorAll(".product-grid")].every((grid) => grid.getAttribute("aria-busy") === "false");
    const target = document.getElementById("product-grid") || document.getElementById("detail-content");
    return target.getAttribute("aria-busy") === "false";
  });
  const open = async (pathname = listing, nextMode = "normal") => {
    mode = nextMode;
    await page.goto(origin + pathname, { waitUntil: "domcontentloaded" });
    if (mode !== "timeout") await settled();
  };
  const check = async (name, fn) => { await fn(); checks.push(name); console.log(`PASS ${name}`); };
  try {
    await check("editorial home has only bounded canonical collections and discovery links", async () => {
      const start = requests.length;
      await open(home);
      assert.equal(await page.locator("input, form, select, #product-count, .pagination").count(), 0);
      assert.equal(await page.locator("#new-grid .product-card").count(), 4);
      assert.equal(await page.locator("#best-grid .product-card").count(), 4);
      assert.equal(await page.locator("#new-grid [data-badge=NEW]").count(), 4);
      assert.equal(await page.locator("#best-grid [data-badge=BEST]").count(), 4);
      const data = requests.slice(start).filter((request) => request.path.startsWith("/shopping/"));
      assert.equal(data.length, 0);
      assert.ok(data.every((request) => request.path === "/shopping/categories" || new URL(request.path, origin).searchParams.get("page_size") === "4"));
      assert.equal(await page.locator("#browse-all").getAttribute("href"), listing);
      assert.match(await page.locator("#home-categories a").nth(1).getAttribute("href"), /\/search\?category=/);
      assert.equal(await page.getByText("추천", { exact: false }).count(), 0);
      await page.screenshot({ path: path.join(output, "home-desktop.png"), fullPage: true });
      await page.locator("#new-grid .product-link").first().click(); await settled();
      assert.equal(await page.locator("#back-to-list").getAttribute("href"), home);
      await page.locator("#back-to-list").click(); await settled();
      assert.equal(new URL(page.url()).pathname, home);
      await page.locator("#browse-all").click(); await settled();
      assert.equal(new URL(page.url()).pathname, listing);
    });
    await check("missing or failed home collections never become featured recommendations", async () => {
      const start = requests.length;
      await open(home, "missing-collections");
      assert.equal(await page.locator(".product-card").count(), 0);
      assert.match(await page.locator("#new-status").innerText(), /제공되는 컬렉션이 없습니다/);
      assert.deepEqual(requests.slice(start).filter((request) => request.path.startsWith("/shopping/")).map((request) => request.path), ["/shopping/categories"]);
      await open(home, "partial-home");
      assert.equal(await page.locator("#new-grid .product-card").count(), 4);
      assert.equal(await page.locator("#best-grid .product-card").count(), 0);
      assert.equal(await page.locator("#home-retry").isVisible(), true);
      mode = "normal"; await page.locator("#home-retry").click(); await settled();
      assert.equal(await page.locator("#best-grid .product-card").count(), 4);
    });
    await check("previous filtered home URLs migrate to search and preserve state", async () => {
      await open(`${home}?category=women-tops&q=블라우스&page=1`);
      assert.equal(new URL(page.url()).pathname, listing);
      assert.equal(new URL(page.url()).searchParams.get("category"), "women-tops");
      assert.equal(await page.locator("#search-input").inputValue(), "블라우스");
      await open(`${detail}?return_to=${encodeURIComponent(`${home}?category=women-tops&page=2`)}`);
      assert.equal(await page.locator("#back-to-list").getAttribute("href"), `${listing}?category=women-tops&page=2`);
    });
    await check("Korean shell, canonical NEW/BEST membership and no HOT/commerce controls", async () => {
      await open();
      await page.waitForFunction(() => document.querySelectorAll('.product-badge:not([hidden])').length === 12);
      assert.equal(await page.locator("html").getAttribute("lang"), "ko");
      assert.equal(await page.locator("#product-count").innerText(), "상품 92개");
      assert.equal(await page.locator('[data-badge="BEST"]:visible').count(), 3);
      assert.equal(await page.locator('[data-badge="HOT"], [data-category="forbidden-promotion"]').count(), 0);
      assert.equal(await page.locator("#cart, .wishlist, #instagram").count(), 0);
      assert.match(await page.locator(".preview-notice").innerText(), /상품 미리보기 · 현재 구매는 지원하지 않습니다\./);
      await page.screenshot({ path: path.join(output, "search-desktop.png"), fullPage: true });
    });
    await check("responsive 4/3/2 columns, compact hero and no overflow at 320px", async () => {
      for (const pathname of [home, listing]) {
        await open(pathname);
        for (const [width, columns] of [[1440, 4], [768, 3], [390, 2], [320, 2]]) {
          await page.setViewportSize({ width, height: 844 });
          const layout = await page.evaluate(() => ({ columns: getComputedStyle(document.querySelector(".product-grid")).gridTemplateColumns.split(" ").length,
            overflow: document.documentElement.scrollWidth > innerWidth, hero: document.querySelector(".hero")?.getBoundingClientRect().height }));
          assert.equal(layout.columns, columns);
          assert.equal(layout.overflow, false, `overflow at ${width}px`);
          if (pathname === home) assert.ok(layout.hero >= (width <= 600 ? 150 : 220) && layout.hero <= (width <= 600 ? 190 : 300));
          else assert.equal(layout.hero, undefined);
        }
      }
      await page.setViewportSize({ width: 390, height: 844 });
      await page.screenshot({ path: path.join(output, "mobile.png"), fullPage: true });
    });
    await check("keyboard skip link, card links and reduced motion", async () => {
      await open();
      await page.keyboard.press("Tab");
      assert.equal(await page.locator(":focus").innerText(), "본문 바로가기");
      assert.equal(await page.locator("html").evaluate((element) => getComputedStyle(element).scrollBehavior), "auto");
      assert.ok(await page.locator(".product-link").first().getAttribute("href"));
      await page.locator(".product-link").first().focus();
      await page.keyboard.press("Enter"); await settled();
      assert.ok(new URL(page.url()).pathname.startsWith(`${home}/product/`));
    });
    await check("category/query/page compose in URL and restore on Back/Forward/reload", async () => {
      await open();
      await page.locator('[data-category="women-tops"]').click(); await settled();
      await page.locator("#next-page").click(); await settled();
      const pageTwo = page.url();
      assert.equal(new URL(pageTwo).searchParams.get("page"), "2");
      assert.equal(await page.locator("#page-label").innerText(), "2 / 2 페이지");
      await page.locator("#search-input").fill("블라우스");
      await page.locator("#search-input").press("Enter"); await settled();
      const combined = page.url();
      assert.equal(new URL(combined).searchParams.get("category"), "women-tops");
      assert.equal(new URL(combined).searchParams.get("q"), "블라우스");
      assert.equal(new URL(combined).searchParams.get("page"), null);
      assert.ok(await page.locator(".product-card").count() > 0);
      await page.goBack(); await settled();
      assert.equal(page.url(), pageTwo);
      assert.equal(await page.locator("#search-input").inputValue(), "");
      await page.goForward(); await settled();
      assert.equal(page.url(), combined);
      assert.equal(await page.locator("#search-input").inputValue(), "블라우스");
      await page.reload(); await settled();
      assert.equal(await page.locator('[data-category="women-tops"]').getAttribute("aria-current"), "page");
      assert.equal(page.url(), combined);
    });
    await check("mood tags are suggested searches within the current category", async () => {
      await page.locator('[data-query="미니멀"]').click(); await settled();
      assert.equal(new URL(page.url()).searchParams.get("category"), "women-tops");
      assert.equal(new URL(page.url()).searchParams.get("q"), "미니멀");
      assert.equal(await page.locator("#search-input").inputValue(), "미니멀");
      assert.equal(await page.locator('[data-tag]').count(), 0);
      await page.locator("#clear-filters").click(); await settled();
      assert.equal(await page.locator("#product-count").innerText(), "상품 92개");
    });
    await check("canonical category IDs are used instead of vendor-specific aliases", async () => {
      await open(listing, "numeric-category");
      await page.locator('[data-category="women-tops"][data-category-id="101"]').click(); await settled();
      assert.equal(new URL(page.url()).searchParams.get("category"), "women-tops");
      assert.equal(await page.locator("#product-count").innerText(), "상품 20개");
      assert.ok(requests.some((request) => request.path.startsWith("/shopping/search?") && new URL(request.path, origin).searchParams.get("category") === "101"));
    });
    await check("server-rendered PDP needs no duplicate browser read and preserves listing URL", async () => {
      await open(`${listing}?category=women-tops&page=2`);
      await page.waitForLoadState("networkidle");
      const listURL = page.url();
      const id = await page.locator(".product-card").first().getAttribute("data-product-id");
      const start = requests.length;
      await page.locator(".product-link").first().click(); await settled();
      assert.deepEqual(requests.slice(start).filter((request) => request.path.startsWith("/shopping/")).map((request) => request.path), []);
      const product = JSON.parse(responses.get(`/shopping/products/${id}`).body);
      assert.equal(await page.locator("#detail-name").innerText(), product.name);
      assert.equal(await page.locator("#detail-description").innerText(), product.description);
      assert.equal(await page.locator("#detail-availability").innerText(), product.in_stock ? "재고 있음" : "품절");
      assert.equal(await page.locator("#back-to-list").getAttribute("href"), new URL(listURL).pathname + new URL(listURL).search);
      await page.setViewportSize({ width: 390, height: 844 });
      await page.screenshot({ path: path.join(output, "mobile-pdp.png"), fullPage: true });
      await page.locator("#back-to-list").click(); await settled();
      assert.equal(page.url(), listURL);
      assert.equal(await page.locator("#page-label").innerText(), "2 / 2 페이지");
      await page.goBack(); await settled();
      assert.ok(new URL(page.url()).pathname.endsWith(id));
      await page.goBack(); await settled();
      assert.equal(page.url(), listURL);
    });
    await check("direct/not-found PDP and unsafe return URLs", async () => {
      await open(detail);
      assert.equal(await page.locator("#back-to-list").getAttribute("href"), listing);
      await open(`${home}/product/no-such-product?return_to=${encodeURIComponent("https://untrusted.invalid/")}`);
      assert.equal(await page.locator("#detail-name").innerText(), "상품을 찾을 수 없습니다");
      assert.equal(await page.locator("#detail-retry").isVisible(), false);
      assert.equal(await page.locator("#back-to-list").getAttribute("href"), listing);
    });
    await check("listing and PDP failures remain distinct from empty/not-found states", async () => {
      for (const pathname of [listing, detail]) for (const failure of ["unavailable", "invalid-json", "malformed", "network-failure"]) {
        await open(pathname, failure);
        assert.equal(await page.locator(pathname === listing ? "#retry" : "#detail-retry").isVisible(), true);
        assert.equal(await page.locator(pathname === listing ? "#product-count" : "#detail-name").innerText(), "상품을 불러오지 못했습니다");
      }
      mode = "normal"; await page.locator("#detail-retry").click(); await settled();
      assert.equal(await page.locator("#description-section").isVisible(), true);
      await open(listing, "empty");
      assert.equal(await page.locator("#product-count").innerText(), "상품 0개");
    });
    await check("eight-second timeout retains explicit retry on both views", async () => {
      await page.clock.install();
      for (const pathname of [listing, detail]) {
        await open(pathname, "timeout");
        await page.clock.fastForward(8100); await settled();
        assert.match(await page.locator(pathname === listing ? "#catalog-status" : "#detail-status").innerText(), /응답 시간이/);
        mode = "normal"; await page.locator(pathname === listing ? "#retry" : "#detail-retry").click(); await settled();
      }
      await page.clock.resume();
    });
    await check("late responses cannot replace newer category results", async () => {
      await open(listing, "race");
      await page.locator('[data-category="women-tops"]').click();
      await page.waitForFunction(() => document.getElementById("product-grid").getAttribute("aria-busy") === "true");
      await page.locator('[data-category="women-dresses"]').click(); await settled();
      assert.ok(held);
      await held.route.fulfill(held.response).catch(() => {});
      assert.equal(await page.locator(".product-category").first().innerText(), "원피스");
    });
    await check("exact decimal strings, safe text descriptions and unapproved image fallback", async () => {
      for (const pathname of [listing, detail]) {
        await open(pathname, "hostile");
        assert.equal(await page.locator(pathname === listing ? ".product-name" : "#detail-name").first().innerText(), '<img src=x onerror="alert(1)">');
        assert.equal(await page.locator(pathname === listing ? ".product-price" : "#detail-price").first().innerText(), "USD 9,007,199,254,740,993.0100");
        assert.equal(await page.locator(pathname === listing ? ".product-name img" : "#detail-description script").count(), 0);
        assert.equal(await page.locator(".photo-fallback").first().isVisible(), true);
      }
      assert.match(await page.locator("#detail-description").innerText(), /<script>alert\(1\)<\/script>/);
      await open(detail, "broken-photo");
      await page.locator(".photo-fallback").waitFor({ state: "visible" });
      await open(listing, "badge-failure");
      assert.equal(await page.locator(".product-card").count(), 12);
      assert.equal(await page.locator(".product-badge:visible").count(), 0);
    });
    await check("no persistent browser state", async () => {
      assert.deepEqual(await page.evaluate(() => [localStorage.length, sessionStorage.length, document.cookie]), [0, 0, ""]);
      assert.deepEqual(await context.cookies(), []);
    });
    await check("no-JavaScript category, GET search, pagination, product and return navigation work", async () => {
      const noJS = await browser.newContext({ javaScriptEnabled: false, serviceWorkers: "block" });
      await noJS.route("**/*", async (route) => {
        const url = new URL(route.request().url());
        const response = responses.get(canonical(url.href));
        if (url.origin === origin && response) return route.fulfill(response);
        return route.abort();
      });
      const fallback = await noJS.newPage();
      for (const pathname of [home, listing, detail]) {
        await fallback.goto(origin + pathname);
        assert.equal(await fallback.locator("noscript").isVisible(), true);
        assert.equal(await fallback.locator("h1").isVisible(), true);
      }
      await fallback.goto(origin + home);
      await fallback.locator('#home-categories a[href$="category=women-tops"]').click();
      assert.equal(await fallback.locator("#product-count").innerText(), "상품 20개");
      await fallback.locator("#next-page").click();
      assert.equal(await fallback.locator("#page-label").innerText(), "2 / 2 페이지");
      const browseURL = fallback.url();
      await fallback.locator(".product-link").first().click();
      assert.match(await fallback.locator("#detail-name").innerText(), /.+/);
      await fallback.locator("#back-to-list").click();
      assert.equal(fallback.url(), browseURL);
      await fallback.locator("#search-input").fill("블라우스");
      await fallback.locator("#search-input").press("Enter");
      assert.equal(new URL(fallback.url()).searchParams.get("category"), "women-tops");
      assert.equal(new URL(fallback.url()).searchParams.get("q"), "블라우스");
      assert.ok(await fallback.locator(".product-link").count() > 0);
      await noJS.close();
    });
    assert.deepEqual(unexpected, []);
    assert.deepEqual(errors, []);
    assert.ok(requests.every((request) => request.method === "GET" && request.origin === origin));
    assert.ok(requests.every((request) => !/wp-json|wc-api|\/orders|\/checkout|\/cart/.test(request.path)));
    await fs.writeFile(path.join(output, "validation.json"), JSON.stringify({ status: "PASS", checks, requests, unexpected, errors }, null, 2));
    console.log(`${checks.length} browser scenarios passed; screenshots and validation.json in ${output}`);
  } finally { await browser.close(); }
}
if (chromium) main().catch((error) => { console.error(error); process.exitCode = 1; });
