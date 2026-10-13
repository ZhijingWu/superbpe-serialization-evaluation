"""Static replay of already-reported vocabulary feature counts; performs no encodings."""
import argparse,json,hashlib,collections
from pathlib import Path
def mapping():
    bs=list(range(33,127))+list(range(161,173))+list(range(174,256));cs=bs[:];n=0
    for b in range(256):
        if b not in bs:bs.append(b);cs.append(256+n);n+=1
    return {chr(c):b for b,c in zip(bs,cs)}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--assets-dir',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--audit-layout',action='store_true',help='Read the legacy directory names instead of public role directories');a=ap.parse_args();r=Path(__file__).resolve().parents[1]
    cfg=json.loads((r/'configs/tokenizers.json').read_bytes());expected=json.loads((r/'results/external/vocabulary_audit.json').read_bytes())['inventory'];bd=mapping();out={}
    for role,x in cfg['assets'].items():
        p=a.assets_dir/(x['asset_directory'] if a.audit_layout else role)/'tokenizer.json';b=p.read_bytes();h=hashlib.sha256(b).hexdigest();assert h in [x['upstream_blob_sha256'],x['original_windows_checkout_sha256']]
        j=json.loads(b);adapted={**j,'added_tokens':[],'decoder':{'type':'ByteLevel','add_prefix_space':True,'trim_offsets':True,'use_regex':True}}
        assert hashlib.sha256(json.dumps(adapted,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==x['adapted_configuration_sha256']
        ct=collections.Counter()
        for piece in j['model']['vocab']:
            v=bytes(bd[c] for c in piece)
            for name,flag in [('colon_ascii_space',b': ' in v),('newline',b'\n' in v),('tab',b'\t' in v),('internal_ascii_space',b' ' in v[1:-1]),('json_punctuation',any(c in b'{}[],:"' for c in v))]:ct[name]+=flag
        assert dict(ct)==expected[role]['feature_type_counts'];out[role]=dict(ct)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(dict(status='PASS',feature_counts=out,encoding_calls=0),indent=2,sort_keys=True)+'\n',encoding='utf-8');print(json.dumps(out))
if __name__=='__main__':main()
