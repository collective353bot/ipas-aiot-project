// node test_sync.js — 測試 template.html 內的合併函式
const fs=require('fs'),assert=require('assert');
const t=fs.readFileSync(__dirname+'/template.html','utf8');
const code=t.slice(t.indexOf('/*SYNC_BEGIN*/'),t.indexOf('/*SYNC_END*/'));
const M=new Function(code+';return{syncMerge,syncStamp,syncStampAudio}')();
const E=()=>({done:{},answers:{},wrong:{},mock:{}});
let n=0;const ok=(name,f)=>{f();n++;console.log('ok -',name)};
ok('phone empty vs desktop D1 done -> both get D1',()=>{
 const desk={s:Object.assign(E(),{done:{1:1000}}),a:{pos:{},rate:1},m:{m:{'done/1':1000},x:{}}};
 const phone={s:E(),a:{pos:{},rate:1},m:{m:{},x:{}}};
 assert.equal(M.syncMerge(phone,desk).s.done[1],1000);assert.equal(M.syncMerge(desk,phone).s.done[1],1000)});
ok('conflicting answers -> newer wins (both orders)',()=>{
 const a={s:Object.assign(E(),{answers:{q1:{c:0,ok:false,t:100}}}),m:{m:{'answers/q1':100}}};
 const b={s:Object.assign(E(),{answers:{q1:{c:2,ok:true,t:200}}}),m:{m:{'answers/q1':200}}};
 assert.equal(M.syncMerge(a,b).s.answers.q1.c,2);assert.equal(M.syncMerge(b,a).s.answers.q1.c,2)});
ok('old data without meta timestamps: union + item t used',()=>{
 const a={s:Object.assign(E(),{done:{1:true},answers:{q1:{c:1,ok:true,t:50}},wrong:{q3:5}})};
 const b={s:Object.assign(E(),{done:{2:true},answers:{q1:{c:3,ok:false,t:90},q2:{c:0,ok:true}}})};
 const r=M.syncMerge(a,b);assert.deepEqual(Object.keys(r.s.done).sort(),['1','2']);
 assert.equal(r.s.answers.q1.c,3);assert.ok(r.s.answers.q2);assert.equal(r.s.wrong.q3,5)});
ok('deletion tombstone beats older item, newer item beats tombstone',()=>{
 const a={s:E(),m:{x:{'wrong/q1':300}}};const b={s:Object.assign(E(),{wrong:{q1:200}}),m:{m:{'wrong/q1':200}}};
 const r=M.syncMerge(a,b);assert.ok(!('q1' in r.s.wrong));assert.equal(r.m.x['wrong/q1'],300);
 const c={s:Object.assign(E(),{wrong:{q1:400}}),m:{m:{'wrong/q1':400}}};assert.equal(M.syncMerge(r,c).s.wrong.q1,400)});
ok('audio: max w/o timestamps, newer with timestamps; rate newer',()=>{
 assert.equal(M.syncMerge({a:{pos:{d1:30}}},{a:{pos:{d1:90}}}).a.pos.d1,90);
 const r=M.syncMerge({a:{pos:{d1:10},rate:2},m:{m:{'pos/d1':500,rate:500}}},{a:{pos:{d1:90},rate:1},m:{m:{'pos/d1':100,rate:100}}});
 assert.equal(r.a.pos.d1,10);assert.equal(r.a.rate,2)});
ok('stamp detects add/change/delete',()=>{
 const m=M.syncStamp({},Object.assign(E(),{done:{1:1},answers:{q:{c:1}}}),Object.assign(E(),{answers:{q:{c:2}},wrong:{z:1}}),777);
 assert.equal(m.m['answers/q'],777);assert.equal(m.m['wrong/z'],777);assert.equal(m.x['done/1'],777)});
ok('merge idempotent & commutative on content',()=>{
 const a={s:Object.assign(E(),{done:{1:5}}),a:{pos:{d2:3}},m:{m:{'done/1':5}}},b={s:Object.assign(E(),{done:{2:6}}),m:{x:{'done/3':9}}};
 const r1=M.syncMerge(a,b),r2=M.syncMerge(b,a);assert.deepEqual(r1,r2);assert.deepEqual(M.syncMerge(r1,r1),r1)});
console.log(n+' passed');
