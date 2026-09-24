const fs=require('node:fs');
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const api=require(process.argv[2]);
const packet=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
(async()=>{
  const accepted=[];
  for(const raw of packet.wires){
    const r=JSON.parse(raw);
    const expect={operation:r.operation,request_id:r.request_id,code_epoch:r.code_epoch,service_instance:r.service_instance,session_scope:r.session_scope,project:r.project,snapshot:r.snapshot,scope:r.scope,policy:null};
    assert.equal(api.decodeWire('ReadResponse',raw).ok,true);
    const decoded=await api.decodeReadResponse(raw,expect);
    assert.equal(decoded.ok,true);
    assert.equal((await api.decodeReadResponse(raw,{...expect,request_id:'different-request'})).ok,false);
    if(r.operation==='entry') assert.equal(JSON.stringify(decoded.value.data.chunks),JSON.stringify(r.data.chunks));
    accepted.push(decoded.value);
  }
  const graph=accepted[0];
  for(const id of packet.marker_ids){
    const m=graph.data.items.find(x=>x.kind==='detail_required'&&x.id===id);
    assert.ok(m);assert.equal(m.reason,'field_limit');assert.equal(m.detail.section,'qualifiers');
  }
  const safe=graph.data.items.find(x=>x.kind==='edge'&&x.edge.id===packet.full_edge_id);
  assert.ok(safe);
  const chunks=accepted.slice(1).flatMap(r=>r.data.chunks);
  assert.ok(chunks.every(c=>c.encoding==='canonical_json'));
  const exact=chunks.map(c=>c.text).join('');
  assert.ok(exact.includes('9007199254740993'));
  assert.ok(exact.includes('-0.0'));
  for(const token of ['9007199254740993','9007199254740993.0','9.007199254740993e15','1.0000000000000001','1e-324','1e309','-0.0']) assert.equal(api.decodeWire('CanonicalJson','{"x":'+token+'}').ok,false);
  for(const token of ['0.1','1.0','1e0']) assert.equal(api.decodeWire('CanonicalJson','{"x":'+token+'}').ok,true);
  process.stdout.write(JSON.stringify({status:'passed',responses:accepted.length,correlation_negative_cases:accepted.length,numeric_markers:packet.marker_ids.length,safe_edge_preserved:true,exact_qualifier_text_preserved:true,unsafe_numeric_cases_rejected:7,ordinary_numeric_cases_admitted:3,exact_text_sha256:crypto.createHash('sha256').update(exact).digest('hex'),qualification:'Actual adapter fixture through freshly compiled current pure client APIs; no HTTP, browser, full policy handshake or production UI claim.'})+'\n');
})().catch(e=>{process.stderr.write(e.stack+'\n');process.exitCode=1;});
