const test = require("node:test");
const assert = require("node:assert/strict");
const vm = require("node:vm");
const fs = require("node:fs");
const source = fs.readFileSync("core/homepage/ui/storefront-orders.js", "utf8");
function setup(status=200) {
  const calls = [];
  const make = () => ({value:"", hidden:false, textContent:"", children:[],dataset:{},
    classList:{add(){}}, addEventListener(){}, focus(){}, setAttribute(){}, scrollIntoView(){},
    append(...items){this.children.push(...items);},
    appendChild(item){this.children.push(item);},
    replaceChildren(...items){this.children=items;}});
  const elements = new Map();
  const by = id => {if(!elements.has(id))elements.set(id,make()); return elements.get(id);};
  vm.runInNewContext(source, {
    window:{location:{hostname:"dev.bokstory.duckdns.org"}},
    document:{getElementById:by,createElement:make,querySelectorAll:()=>[]},
    fetch:async(url,options)=>{
      calls.push({url,options});
      return {ok:status===200,status,json:async()=>({order:{
        order_number:"2610122150",items:[{name:"코트",option:"M",quantity:1}],
        total:"450000",currency:"KRW",fulfillment:{state:"SHIPPED"}
      }})};
    }
  });
  return {calls,by};
}
test("10-digit public order renders without any session request",async()=>{
  const s=setup();
  assert.equal(s.calls.length,0);
  s.by("orders-number").value=" #2610122150 ";
  s.by("lookup-phone").value="01012345678";
  await s.by("orders-lookup").onclick();
  assert.deepEqual(s.calls.map(c=>c.url),["/__order-dev/orders/public-lookup"]);
  assert.deepEqual(JSON.parse(s.calls[0].options.body),{order_number:"2610122150",phone:"01012345678"});
  assert.equal(s.by("orders-list").children.length,1);
  assert.equal(s.by("orders-auth").hidden,true);
});
test("unknown public order shows an error without authentication fallback",async()=>{
  const s=setup(404);
  s.by("orders-number").value="2610122150";
  s.by("lookup-phone").value="01012345678";
  await s.by("orders-lookup").onclick();
  assert.equal(s.calls.length,1);
  assert.match(s.by("orders-message").textContent,/주문을 찾을 수 없습니다/);
  assert.equal(s.by("orders-list").children.length,0);
});

test("public lookup requires phone before sending a request",async()=>{
  const s=setup();
  s.by("orders-number").value="2610122150";
  await s.by("orders-lookup").onclick();
  assert.equal(s.calls.length,0);
  assert.match(s.by("orders-message").textContent,/휴대폰 번호/);
});
