"""Recover only the frozen external objects from pinned sources; verify all fixture hashes."""
import argparse,csv,hashlib,json,re
from pathlib import Path
FORMATS={'compact':dict(separators=(',',':'),indent=None),'spaced':dict(separators=(', ',': '),indent=None),'indent2':dict(separators=(',',': '),indent=2),'tab':dict(separators=(',',': '),indent='\t')}
def canonical(o):return json.dumps(o,ensure_ascii=False,sort_keys=True,allow_nan=False,separators=(',',':')).encode()
def pairs(ps):
    d={}
    for k,v in ps:
        if k in d:raise ValueError('Duplicate JSON key')
        d[k]=v
    return d
def load(b):return json.loads(b,object_pairs_hook=pairs,parse_constant=lambda s:(_ for _ in ()).throw(ValueError('Nonfinite JSON')))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--cache',type=Path,required=True);ap.add_argument('--output',type=Path);ap.add_argument('--check-only',action='store_true');ap.add_argument('--flat-cache',action='store_true');a=ap.parse_args()
    if not a.check_only and a.output is None:ap.error('Choose --check-only or a new --output directory')
    if a.output and a.output.exists():raise RuntimeError('Refusing to overwrite fixtures')
    r=Path(__file__).resolve().parents[1];cfg=json.loads((r/'configs/sources.json').read_bytes());cache={}
    for source,info in cfg['sources'].items():
        for x in info['raw_downloads']:
            p=a.cache/x['label'] if a.flat_cache else a.cache/source/x['label'];b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'];cache[x['label']]=load(b)
    candidates=[]
    for src in ['mcp','a2a']:
        candidates.extend(v for _,v in sorted(cache[src+'_schema.json']['definitions'].items()))
    for j in range(5):
        obj=cache[f'swe_{j}.traj']
        for h in obj.get('history',[]):
            for t in h.get('tool_calls',[]) or []:
                v=t['function']['arguments'];o=load(v) if isinstance(v,str) else v
                if j<3 and any(k in o for k in ['search','replace','content','code']):continue
                candidates.append(o)
        for step in obj.get('trajectory',[]):
            v=step.get('state')
            if isinstance(v,(dict,str)):candidates.append(load(v) if isinstance(v,str) else v)
    manifest=json.loads((r/'results/external/record_manifest.json').read_bytes());expected={x['record_id']:x['semantic_sha256'] for x in manifest['records']}
    hashrows={}
    for x in csv.DictReader((r/'results/external/external_token_counts.csv').open(encoding='utf-8')):hashrows[(x['record_id'],x['format'])]=x['sha256']
    selected=[];seen=set()
    for o in candidates:
        assert isinstance(o,dict);b=canonical(o);h=hashlib.sha256(b).hexdigest()
        if h in seen:continue
        # The frozen source values and selection are authoritative; a changed source fails,
        # rather than silently dropping additional records or rewriting a field.
        rid='ext_'+str(len(selected)).zfill(3);assert h==expected.get(rid),(rid,'Selection/source differs from frozen evidence')
        seen.add(h);selected.append((rid,o))
    assert len(selected)==208
    total=0
    for rid,o in selected:
        for f,kw in FORMATS.items():
            b=json.dumps(o,sort_keys=True,ensure_ascii=False,allow_nan=False,**kw).encode();assert hashlib.sha256(b).hexdigest()==hashrows[(rid,f)]
            assert canonical(load(b))==canonical(o);total+=len(b)
            if not a.check_only:
                p=a.output/rid/(f+'.json');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
    print(json.dumps(dict(status='PASS',objects=208,fixture_hashes_verified=832,fixture_bytes=total,check_only=a.check_only,encoding_calls=0)))
if __name__=='__main__':main()
