"""Opt-in acquisition of pinned assets into an ignored cache, with exact byte hashes."""
import argparse,hashlib,json,urllib.request
from pathlib import Path
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--tokenizers',action='store_true');ap.add_argument('--sources',action='store_true');ap.add_argument('--output',type=Path,default=Path('build/assets'));a=ap.parse_args();root=Path(__file__).resolve().parents[1]
    if not (a.tokenizers or a.sources):ap.error('Explicitly select --tokenizers and/or --sources; no download by default')
    jobs=[]
    if a.tokenizers:
        cfg=json.loads((root/'configs/tokenizers.json').read_bytes())
        for role,x in cfg['assets'].items():jobs.append((x['url'],a.output/'tokenizers'/role/'tokenizer.json',x['upstream_blob_sha256'],x['upstream_blob_bytes']))
    if a.sources:
        cfg=json.loads((root/'configs/sources.json').read_bytes())
        for source,x in cfg['sources'].items():
            for z in x['raw_downloads']:jobs.append((z['url'],a.output/'sources'/source/z['label'],z['sha256'],z['bytes']))
    total=sum(x[3] for x in jobs);assert total<70_000_000,'Acquisition size cap exceeded'
    for url,p,h,n in jobs:
        if p.exists():b=p.read_bytes()
        else:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'SuperBPE-Serialization-Evaluation'}),timeout=30) as f:b=f.read(n+1)
        assert len(b)==n and hashlib.sha256(b).hexdigest()==h,(str(p),'Size/hash mismatch')
        p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);print(str(p)+': verified '+str(n)+' bytes')
    print('Complete. Cache contains third-party material and must not be staged or redistributed wholesale.')
if __name__=='__main__':main()
