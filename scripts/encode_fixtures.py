"""Optional direct-file encoding replay. Not run during release preparation."""
import argparse,csv,hashlib,json,platform,sys,time,os,threading,ctypes,gc
from pathlib import Path
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--fixtures',type=Path,required=True);ap.add_argument('--assets-dir',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    import tokenizers
    from tokenizers import Tokenizer
    assert platform.python_version()=='3.13.5' and tokenizers.__version__=='0.20.3','Encoding runtime must match the audit'
    r=Path(__file__).resolve().parents[1];assets=json.loads((r/'configs/tokenizers.json').read_bytes())['assets'];files=sorted(a.fixtures.rglob('*.json'));assert files,'No fixture files'
    assert sum(p.stat().st_size for p in files)<10_000_000;assert not a.output.exists(),'Refusing to overwrite encoding results'
    observations=[];start=time.process_time();done=threading.Event()
    def peak_memory():
        if os.name=='nt':
            class PM(ctypes.Structure):
                _fields_=[('cb',ctypes.c_ulong),('faults',ctypes.c_ulong)]+[(k,ctypes.c_size_t) for k in ['peak','working','qp','q','qnp','qn','private','private_peak']]
            z=PM();z.cb=ctypes.sizeof(z);ctypes.windll.kernel32.GetCurrentProcess.restype=ctypes.c_void_p
            fn=ctypes.windll.psapi.GetProcessMemoryInfo;fn.argtypes=[ctypes.c_void_p,ctypes.POINTER(PM),ctypes.c_ulong]
            assert fn(ctypes.windll.kernel32.GetCurrentProcess(),ctypes.byref(z),z.cb)
            return max(z.peak,z.private_peak)
        import resource
        n=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return n if sys.platform=='darwin' else n*1024
    def watchdog():
        while not done.wait(.25):
            if time.process_time()-start>1800 or peak_memory()>4*1024**3:
                print('CPU/RAM stopping limit exceeded; no valid result CSV written.',file=sys.stderr,flush=True);os._exit(7)
    threading.Thread(target=watchdog,daemon=True).start()
    for role,x in assets.items():
        p=a.assets_dir/role/'tokenizer.json';b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==x['upstream_blob_sha256'];original=Tokenizer.from_file(str(p));j=json.loads(b)
        assert j['normalizer'] is None and j['model']['dropout'] is None and not j['model']['ignore_merges']
        assert j.get('post_processor') is None and j.get('padding') is None and j.get('truncation') is None
        j['added_tokens']=[];j['decoder']={'type':'ByteLevel','add_prefix_space':True,'trim_offsets':True,'use_regex':True};serialized=json.dumps(j,sort_keys=True,ensure_ascii=False,separators=(',',':'))
        assert hashlib.sha256(serialized.encode()).hexdigest()==x['adapted_configuration_sha256'];t=Tokenizer.from_str(serialized);t.no_padding();t.no_truncation();assert t.get_vocab_size()==200000
        for f in files:
            raw=f.read_bytes();text=raw.decode('utf-8',errors='strict');json.loads(text)
            assert not any(q in text for q in ['<|endoftext|>','<|padding|>','|||IP_ADDRESS|||','|||EMAIL_ADDRESS|||','|||PHONE_NUMBER|||'])
            ids=t.encode(text,add_special_tokens=False).ids;assert ids==original.encode(text,add_special_tokens=False).ids
            assert t.decode(ids,skip_special_tokens=False)==text and ids==t.encode(text,add_special_tokens=False).ids
            observations.append(dict(relative_fixture_path=f.relative_to(a.fixtures).as_posix(),tokenizer=role,utf8_bytes=len(raw),unicode_codepoints=len(text),tokens=len(ids),fixture_sha256=hashlib.sha256(raw).hexdigest()))
            assert time.process_time()-start<1800 and peak_memory()<=4*1024**3,'Resource cap exceeded'
        del t,original,j,b;gc.collect()
    done.set()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(observations[0]));w.writeheader();w.writerows(observations)
    print('Encoding replay completed; these are new replay outputs, not a replacement for frozen evidence.')
if __name__=='__main__':main()
