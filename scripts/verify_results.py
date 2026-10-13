"""Offline statistical replay and integrity check. No tokenizers or network needed."""
import argparse,hashlib,json,math,csv,subprocess,sys
from pathlib import Path
FILES={'synthetic':['primary_statistics.json','bootstrap_results.json','raw_token_counts.csv','sensitivity_results.csv','family_effects.csv'],
       'external':['external_statistics.json','external_bootstrap_results.json','external_record_effects.csv','external_source_metrics.csv','external_paired_counts.csv','structure_sensitivity.csv']}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1]);ap.add_argument('--output',type=Path);a=ap.parse_args();r=a.repo.resolve();out=a.output or r/'build/replayed';out.mkdir(parents=True,exist_ok=True)
    for group in FILES:
        src=r/'results'/group;target=out/group;target.mkdir(parents=True,exist_ok=True)
        subprocess.run([sys.executable,str(r/'scripts'/('analyze_synthetic.py' if group=='synthetic' else 'analyze_external.py')),'--root',str(src),'--output',str(target)],check=True)
        for n in FILES[group]:assert (src/n).read_bytes()==(target/n).read_bytes(),(group,n,'Statistical replay differs')
    old=json.loads((r/'results/synthetic/primary_statistics.json').read_bytes());ext=json.loads((r/'results/external/external_statistics.json').read_bytes())
    assert abs(old['primary_estimate']-.06721989474552999)<1e-14
    assert abs(ext['equal_source_D']-.15337727894171493)<1e-14
    assert ext['pair_summaries']['t180k_vs_no_whitespace']['pooled']['indent2']['regressing_records']==201
    rs=list(csv.DictReader((r/'results/external/external_paired_counts.csv').open(encoding='utf-8')))
    for x in rs:
        b,s=int(x['baseline_tokens']),int(x['comparison_tokens']);assert int(x['absolute_token_savings'])==b-s;assert abs(float(x['relative_savings'])-(1-s/b))<1e-14
    v=dict(status='PASS',python=sys.version.split()[0],byte_identical_statistical_files=FILES,synthetic_estimate=old['primary_estimate'],external_estimate=ext['equal_source_D'],external_indent2_no_whitespace_wins=201,network_requests=0,encoding_calls=0)
    (out/'verification.json').write_text(json.dumps(v,indent=2,sort_keys=True)+'\n',encoding='utf-8');print(json.dumps(v))
if __name__=='__main__':main()
