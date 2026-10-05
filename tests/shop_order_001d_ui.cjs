"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const {createController} = require("../deploy/shopping/wordpress/plugins/ai-shopping-storefront/assets/storefront-order.js");
const token = "a".repeat(64);
function storage() {
    const values = new Map();
    return {getItem:k=>values.get(k)||null,setItem:(k,v)=>values.set(k,v),removeItem:k=>values.delete(k),values};
}
function reply(body, status=200) {
    return {ok:status>=200&&status<300,status,headers:{get:()=>token},json:async()=>body};
}
function setup({store=storage(), postReply, statusReply, postError, authError=false}={}) {
    const calls=[], states=[];
    let keys=0;
    const fetcher=async(url, options={})=>{
        calls.push({url,options});
        if(url==="/shopping/auth/session") return reply({},authError?401:200);
        if(options.method==="POST") {
            if(postError)throw postError;
            return postReply||reply({outcome:"COMPLETED",provider_order_id:501,idempotent_replay:false},201);
        }
        return statusReply||reply({state:"COMPLETED",review_state:"CONFIRMED",provider_order_id:501});
    };
    const controller=createController({fetcher,storage:store,randomKey:()=>"order-key-"+(++keys),productId:"123",onState:s=>states.push(s)});
    return {controller,calls,states,store,get keys(){return keys;}};
}
const posts = calls => calls.filter(c=>c.options.method==="POST");

test("closed authenticated intent and no credential storage", async()=>{
    const s=setup();const result=await s.controller.submit({quantity:2,variationId:"456"});
    assert.equal(result.kind,"completed");
    const req=posts(s.calls)[0];
    assert.equal(req.options.headers["X-CSRF-Token"],token);
    assert.deepEqual(JSON.parse(req.options.body),{line_items:[{product_id:"123",quantity:2,variation_id:"456"}],idempotency_key:"order-key-1"});
    assert(!JSON.stringify([...s.store.values.values()]).includes(token));
    assert.equal(s.keys,1);
});
test("in-flight double click is rejected",async()=>{
    let release;const wait=new Promise(resolve=>release=resolve);const s=setup();
    const original=s.controller;
    const calls=[];
    const c=createController({storage:storage(),productId:"123",randomKey:()=>"key-1",fetcher:async(url,options={})=>{
        calls.push(options);if(url.endsWith("/session")){await wait;return reply({});}
        return reply({outcome:"COMPLETED",provider_order_id:1},201);
    }});
    const first=c.submit({quantity:1});
    assert.equal((await c.submit({quantity:1})).kind,"busy");release();await first;
    assert.equal(calls.filter(o=>o.method==="POST").length,1);
});
test("response loss keeps exact key across reload and never auto POSTs",async()=>{
    const s=setup({postError:new Error("network lost")});
    assert.equal((await s.controller.submit({quantity:1})).kind,"check_required");
    const resumed=setup({store:s.store});assert(resumed.controller.hasOperation());
    assert.equal(resumed.calls.length,0);
    assert.equal((await resumed.controller.inspect()).review,"CONFIRMED");
    assert.equal(posts(resumed.calls).length,0);
});
test("manual replay after ambiguous result preserves key",async()=>{
    const s=setup({postError:new Error("timeout")});
    await s.controller.submit({quantity:1});await s.controller.submit({quantity:1});
    assert.equal(s.keys,1);
    assert.deepEqual(posts(s.calls).map(c=>JSON.parse(c.options.body).idempotency_key),["order-key-1","order-key-1"]);
});
test("different intent cannot replace an unresolved operation",async()=>{
    const s=setup({postError:new Error("timeout")});await s.controller.submit({quantity:1});
    assert.equal((await s.controller.submit({quantity:2})).kind,"existing_operation");
    assert.equal(posts(s.calls).length,1);
    assert.equal(s.controller.startNew().kind,"check_required");
});
test("completed operation requires explicit new-order action",async()=>{
    const s=setup();await s.controller.submit({quantity:1});
    assert.equal((await s.controller.submit({quantity:1})).kind,"existing_operation");
    assert.equal(s.controller.startNew().kind,"new_operation");
    await s.controller.submit({quantity:1});assert.equal(s.keys,2);
});
test("authentication failure never POSTs",async()=>{
    const s=setup({authError:true});assert.equal((await s.controller.submit({quantity:1})).kind,"auth_required");
    assert.equal(posts(s.calls).length,0);
});
test("invalid quantities never fetch",async()=>{
    for(const quantity of [0,1001,1.5,NaN,true]){
        const s=setup();assert.equal((await s.controller.submit({quantity})).kind,"invalid_quantity");assert.equal(s.calls.length,0);
    }
});
test("failed storage blocks every create attempt",async()=>{
    const store=storage();store.setItem=()=>{throw new Error("disabled");};const s=setup({store});
    await s.controller.submit({quantity:1});await s.controller.submit({quantity:1});assert.equal(posts(s.calls).length,0);
});
test("corrupt saved state cannot create orders",async()=>{
    const store=storage();store.setItem("aicc.order.operation.v1.123","{bad");const s=setup({store});
    await s.controller.submit({quantity:1});assert.equal(s.calls.length,0);
});
test("unknown outcome status stays blocked against new order",async()=>{
    const s=setup({postError:new Error("timeout"),statusReply:reply({state:"UNKNOWN_OUTCOME",review_state:null,provider_order_id:null})});
    await s.controller.submit({quantity:1});assert.equal((await s.controller.inspect()).state,"UNKNOWN_OUTCOME");
    assert.equal(s.controller.startNew().kind,"check_required");assert.equal(posts(s.calls).length,1);
});
test("malformed success is treated as uncertain",async()=>{
    const s=setup({postReply:reply({outcome:"COMPLETED",provider_order_id:true},201)});
    assert.equal((await s.controller.submit({quantity:1})).kind,"check_required");
    assert.equal(s.controller.startNew().kind,"check_required");
});
