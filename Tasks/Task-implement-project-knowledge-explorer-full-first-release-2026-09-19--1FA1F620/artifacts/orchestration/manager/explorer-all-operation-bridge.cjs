const fs=require('node:fs'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const api=require(process.argv[2]),packet=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
(async()=>{
 const checks=[];
 for(const x of packet.wires){
  const r=JSON.parse(x.raw),expected={operation:r.operation,request_id:r.request_id,code_epoch:r.code_epoch,service_instance:r.service_instance,session_scope:r.session_scope,project:r.project,snapshot:r.snapshot,scope:r.scope,policy:packet.policy};
  const admitted=await api.decodeReadResponse(x.raw,expected);assert.equal(admitted.ok,true,x.name);
  for(const change of [{session_scope:'4'.repeat(32)},{snapshot:'5'.repeat(64)},{project:{...r.project,root_scope_id:'6'.repeat(64)}}])assert.equal((await api.decodeReadResponse(x.raw,{...expected,...change})).ok,false,x.name+' scope');
  assert.equal(api.stableJson(admitted.value),api.stableJson(r),x.name+' value');
  checks.push({name:x.name,operation:r.operation,status:r.status,returned:r.page.returned});
 }
 process.stdout.write(JSON.stringify({status:'passed',count:checks.length,operations:[...new Set(checks.map(x=>x.operation))],correlation_rejections:checks.length*3,checks})+'\n');
})().catch(e=>{process.stderr.write(e.stack+'\n');process.exitCode=1;});
