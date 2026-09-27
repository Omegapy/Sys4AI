"""Preserve complete raw UTF-8 reports as lossless bounded evidence shards."""
from pathlib import Path
import base64,hashlib,json,os,stat,sys
ROOT=Path(__file__).resolve().parents[3];Q=Path(__file__).resolve().parent
folder=Q/sys.argv[1];assert folder.parent==Q and folder.name.startswith('actual-')
input_name=sys.argv[2] if len(sys.argv)==3 else 'stdout.json';assert input_name in ('stdout.json','recovered-raw-reports.json')
report=json.loads((folder/input_name).read_text());dest=folder/'axe-raw-shards';dest.mkdir();states=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,obj):
 raw=(json.dumps(obj,indent=2,ensure_ascii=False)+'\n').encode();assert len(raw)<=250000;p.write_bytes(raw);return {'path':str(p.relative_to(ROOT)),'sha256':sha(raw),'bytes':len(raw)}
for index,scan in enumerate(report['scans']):
 ref=scan['raw_report'];path=Path(ref['path']);assert str(path).startswith('/private/tmp/explorer-a11y-evidence-')
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
 with os.fdopen(fd,'rb') as f:
  st=os.fstat(f.fileno());assert stat.S_ISREG(st.st_mode) and st.st_nlink==1;raw=f.read();end=os.fstat(f.fileno());assert (st.st_size,st.st_mtime_ns,st.st_ino)==(end.st_size,end.st_mtime_ns,end.st_ino)
 assert len(raw)==ref['bytes'] and sha(raw)==ref['sha256'];parsed=json.loads(raw);assert parsed['testEngine']['version']=='4.13.0'
 pieces=[];reconstructed=b''
 for offset in range(0,len(raw),120000):
  part=raw[offset:offset+120000];row={'whole_report_sha256':sha(raw),'offset':offset,'decoded_bytes':len(part),'encoding':'base64 of exact original UTF-8 bytes','data':base64.b64encode(part).decode()};p=dest/(str(index).zfill(2)+'-'+str(offset//120000).zfill(3)+'.json');pieces.append(save(p,row));reconstructed+=base64.b64decode(json.loads(p.read_text())['data'],validate=True)
 assert reconstructed==raw
 states.append({'name':scan['name'],'theme':scan['theme'],'original_raw_location':str(path),'complete_original_sha256':sha(raw),'complete_original_bytes':len(raw),'lossless_shards':pieces,'violation_rules':len(parsed['violations']),'incomplete_rules':len(parsed['incomplete']),'all_nodes_retained':True,'target_candidates':scan['targets_below24']})
index=save(folder/'axe-complete-report-index.json',{'status':'all_original_reports_preserved_losslessly','source_stdout_sha256':sha((folder/input_name).read_bytes()),'original_scan_status':report['status'],'states':states,'reconstruction':'In offset order decode each data field with base64, concatenate all bytes, verify complete_original_sha256, then parse UTF-8 JSON. Original root-produced full raw files also remain at their recorded private locations. Nothing is truncated; every axe category/node and target candidate is retained.','evidence_cap_bytes':250000});print(json.dumps(index))
