"""Independent analysis: standard library only; consumes frozen CSV and manifest."""
import argparse,csv,hashlib,json,math,random,statistics,time
from collections import defaultdict
from pathlib import Path
CATS=['tool_arguments','json_schemas','execution_records','inter_agent_messages']
FORMATS=['compact','spaced','indent2','tab']
PAIRS=[('primary','bpe200k','superbpe_t180k'),('t80k_vs_bpe','bpe200k','superbpe_t80k'),
       ('t180k_vs_no_whitespace','no_whitespace200k','superbpe_t180k'),('no_whitespace_vs_bpe','bpe200k','no_whitespace200k')]
DIAGS=['boundary_spanning_tokens','internal_ascii_space_tokens','spanning_ascii_space_tokens','spanning_newline_or_tab_tokens','spanning_punctuation_tokens','partial_utf8_tokens']
def sha(b):return hashlib.sha256(b).hexdigest()
def writej(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\r\n')
def writecsv(p,rs):
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def pct(xs,q):
    s=sorted(xs);v=(len(s)-1)*q;i=int(v);j=min(i+1,len(s)-1);return s[i]+(s[j]-s[i])*(v-i)
def ci(xs):return [pct(xs,.025),pct(xs,.975)]
def avg(xs):return statistics.mean(xs)
def corr(xs,ys):
    if len(xs)<2:return None
    mx,my=avg(xs),avg(ys);a=sum((x-mx)*(y-my) for x,y in zip(xs,ys));b=sum((x-mx)**2 for x in xs)*sum((y-my)**2 for y in ys)
    return a/math.sqrt(b) if b else None
def classify(interval):
    lo,hi=interval
    if lo>.05 or hi<-.05:return 'A_robust_practical_serialization_effect'
    if lo>=-.05 and hi<=.05:return 'B_practically_bounded_null'
    return 'C_small_or_uncertain_effect'
def summary(fids,f,b,s,data):
    br=[data[(i,f,b)] for i in fids];sr=[data[(i,f,s)] for i in fids]
    nb=sum(r['tokens'] for r in br);ns=sum(r['tokens'] for r in sr);bb=sum(r['utf8_bytes'] for r in br);cc=sum(r['unicode_codepoints'] for r in br)
    gs=[1-y['tokens']/x['tokens'] for x,y in zip(br,sr)]
    return dict(family_count=len(fids),utf8_bytes=bb,unicode_codepoints=cc,bpe_tokens=nb,comparison_tokens=ns,
      absolute_token_savings=nb-ns,mean_absolute_token_savings=(nb-ns)/len(fids),
      family_average_relative_savings=avg(gs),corpus_aggregate_relative_savings=1-ns/nb,
      baseline_bytes_per_token=bb/nb,comparison_bytes_per_token=bb/ns,
      baseline_codepoints_per_token=cc/nb,comparison_codepoints_per_token=cc/ns,
      regressing_families=sum(g<0 for g in gs),zero_saving_families=sum(g==0 for g in gs),min_family_G=min(gs),max_family_G=max(gs))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    root=a.root;out=a.output or root;out.mkdir(parents=True,exist_ok=True);started=time.process_time()
    mf=json.loads((root/'record_manifest.json').read_bytes());check=json.loads((root/'checks.json').read_bytes())
    assert check['status']=='PASS'
    rows=list(csv.DictReader((root/'tokenizer_observations.csv').open(encoding='utf-8',newline='')))
    assert len(rows)==1920
    for r in rows:
        for k in ['tokens','utf8_bytes','unicode_codepoints','baseline_pretoken_boundaries']+DIAGS:r[k]=int(r[k])
    data={(r['family_id'],r['format'],r['tokenizer']):r for r in rows}
    assert len(data)==1920
    fam={r['family_id']:r for r in mf['families'] if r['split']=='evaluation'};fids=sorted(fam);assert len(fids)==100
    bycat={c:[i for i in fids if fam[i]['category']==c] for c in CATS};assert all(len(v)==25 for v in bycat.values())
    raw=[];sensitivity=[]
    for i in fids:
        for f in FORMATS:
            br=data[(i,f,'bpe200k')];sr=data[(i,f,'superbpe_t180k')]
            r={k:br[k] for k in ['family_id','category','schema_lineage','unicode_slice','payload_class','format','sha256','utf8_bytes','unicode_codepoints']}
            r.update(bpe_token_count=br['tokens'],superbpe_token_count=sr['tokens'],absolute_token_savings=br['tokens']-sr['tokens'],relative_token_savings=1-sr['tokens']/br['tokens'],
                     bpe_bytes_per_token=br['utf8_bytes']/br['tokens'],superbpe_bytes_per_token=sr['utf8_bytes']/sr['tokens'],
                     bpe_codepoints_per_token=br['unicode_codepoints']/br['tokens'],superbpe_codepoints_per_token=sr['unicode_codepoints']/sr['tokens'],baseline_pretoken_boundaries=br['baseline_pretoken_boundaries'])
            for k in DIAGS:r['bpe_'+k]=br[k];r['superbpe_'+k]=sr[k]
            raw.append(r)
            for name,b,s in PAIRS[1:]:
                x,y=data[(i,f,b)],data[(i,f,s)]
                sensitivity.append(dict(pair=name,family_id=i,category=fam[i]['category'],schema_lineage=fam[i]['schema_lineage'],format=f,baseline_tokenizer=b,comparison_tokenizer=s,utf8_bytes=x['utf8_bytes'],unicode_codepoints=x['unicode_codepoints'],baseline_tokens=x['tokens'],comparison_tokens=y['tokens'],absolute_token_savings=x['tokens']-y['tokens'],relative_token_savings=1-y['tokens']/x['tokens']))
    writecsv(out/'raw_token_counts.csv',raw);writecsv(out/'sensitivity_results.csv',sensitivity)
    g={(i,f):1-data[(i,f,'superbpe_t180k')]['tokens']/data[(i,f,'bpe200k')]['tokens'] for i in fids for f in FORMATS}
    ds={i:g[(i,'indent2')]-g[(i,'compact')] for i in fids}
    overall={f:summary(fids,f,'bpe200k','superbpe_t180k',data) for f in FORMATS}
    categories={c:dict(mean_delta=avg(ds[i] for i in bycat[c]),formats={f:summary(bycat[c],f,'bpe200k','superbpe_t180k',data) for f in FORMATS}) for c in CATS}
    clusters={}
    for c in CATS:
        d=defaultdict(list)
        for i in bycat[c]:d[fam[i]['schema_lineage']].append(i)
        clusters[c]=[v for _,v in sorted(d.items())]
    rng=random.Random(6198);draws=[];catdraw={c:[] for c in CATS};corpusdraw=[]
    for _ in range(10000):
        cm=[];allids=[]
        for c in CATS:
            cl=clusters[c];ids=[i for _j in cl for i in cl[rng.randrange(len(cl))]]
            # Repeat all held-out siblings in a sampled lineage; retain equal family weighting.
            m=avg(ds[i] for i in ids);catdraw[c].append(m);cm.append(m);allids.extend(ids)
        draws.append(avg(cm))
        ng={f:1-sum(data[(i,f,'superbpe_t180k')]['tokens'] for i in allids)/sum(data[(i,f,'bpe200k')]['tokens'] for i in allids) for f in ['compact','indent2']}
        corpusdraw.append(ng['indent2']-ng['compact'])
    interval=ci(draws);delta=avg(categories[c]['mean_delta'] for c in CATS)
    for c in CATS:categories[c]['bootstrap_ci95']=ci(catdraw[c]);categories[c]['evaluation_lineages']=len(clusters[c]);categories[c]['positive_D_families']=sum(ds[i]>0 for i in bycat[c])
    dsrows=[dict(family_id=i,category=fam[i]['category'],schema_lineage=fam[i]['schema_lineage'],payload_class=fam[i]['payload_class'],unicode_slice=fam[i]['unicode_slice'],compact_G=g[(i,'compact')],indent2_G=g[(i,'indent2')],delta=ds[i],four_format_spread=max(g[(i,f)] for f in FORMATS)-min(g[(i,f)] for f in FORMATS)) for i in fids]
    writecsv(out/'family_effects.csv',dsrows)
    # Rule fixed before counts: up to two most positive and two most negative D per category; ties by ID.
    selected={}
    for c in CATS:
        pos=sorted((i for i in bycat[c] if ds[i]>0),key=lambda i:(-ds[i],i))[:2]
        neg=sorted((i for i in bycat[c] if ds[i]<0),key=lambda i:(ds[i],i))[:2]
        selected[c]=dict(positive=pos,negative=neg)
    diagnostics={role:{f:{k:sum(data[(i,f,role)][k] for i in fids) for k in ['tokens']+DIAGS} for f in FORMATS} for role in ['bpe200k','superbpe_t180k','superbpe_t80k','no_whitespace200k']}
    for role in diagnostics:
        for f in FORMATS:
            x=diagnostics[role][f];x['boundary_spanning_fraction']=x['boundary_spanning_tokens']/x['tokens']
    aux={}
    for flag,values in [('payload_class',['prose_rich','identifier_rich']),('unicode_slice',[False,True])]:
        aux[flag]={str(v):dict(families=sum(fam[i][flag]==v for i in fids),mean_delta=avg(ds[i] for i in fids if fam[i][flag]==v),formats={f:summary([i for i in fids if fam[i][flag]==v],f,'bpe200k','superbpe_t180k',data) for f in FORMATS}) for v in values}
    lengths=[fam[i]['compact_bytes'] for i in fids];infl=[data[(i,'indent2','bpe200k')]['utf8_bytes']/data[(i,'compact','bpe200k')]['utf8_bytes']-1 for i in fids]
    cross=[data[(i,'indent2','superbpe_t180k')]['boundary_spanning_tokens']/data[(i,'indent2','superbpe_t180k')]['tokens']-data[(i,'compact','superbpe_t180k')]['boundary_spanning_tokens']/data[(i,'compact','superbpe_t180k')]['tokens'] for i in fids]
    aux['descriptive_correlations']=dict(delta_vs_compact_bytes=corr(lengths,[ds[i] for i in fids]),delta_vs_byte_inflation=corr(infl,[ds[i] for i in fids]),delta_vs_spanning_fraction_change=corr(cross,[ds[i] for i in fids]),warning='Descriptive correlations, no causal mediation or formal hypothesis tests')
    lineage_means={c:[avg(ds[i] for i in ids) for ids in clusters[c]] for c in CATS}
    aux['lineages']=dict(equal_lineage_equal_category_delta=avg(avg(v) for v in lineage_means.values()),positive_lineage_means={c:sum(v>0 for v in lineage_means[c]) for c in CATS},lineage_sizes={c:[len(v) for v in clusters[c]] for c in CATS},warning='Shared phrase bank and generic structures induce additional dependence beyond declared schema clusters')
    # Leave-one-lineage influence is descriptive, does not replace the primary endpoint.
    leave=[]
    for c in CATS:
        for cl in clusters[c]:
            keep=[i for i in bycat[c] if i not in cl]
            leave.append(avg([avg(ds[i] for i in keep) if z==c else categories[z]['mean_delta'] for z in CATS]))
    aux['lineages']['leave_one_lineage_delta_range']=[min(leave),max(leave)]
    pairsummary={name:{c:{f:summary(bycat[c] if c!='overall' else fids,f,b,s,data) for f in FORMATS} for c in ['overall']+CATS} for name,b,s in PAIRS[1:]}
    stats=dict(status='VALID',primary_estimate=delta,primary_ci95=interval,practical_margin=0.05,outcome_class=classify(interval),
      primary_estimand='Equal-category mean of family paired D=G_indent2-G_compact; 25 held-out families per category',
      family_average_definition='Arithmetic mean of 1 - N_comparison/N_baseline across semantic families',
      corpus_aggregate_definition='1 - sum(N_comparison)/sum(N_baseline); weights vary by serialization',
      overall_formats=overall,categories=categories,corpus_aggregate_delta=overall['indent2']['corpus_aggregate_relative_savings']-overall['compact']['corpus_aggregate_relative_savings'],
      corpus_aggregate_delta_ci95=ci(corpusdraw),positive_D_families=sum(v>0 for v in ds.values()),negative_D_families=sum(v<0 for v in ds.values()),zero_D_families=sum(v==0 for v in ds.values()),
      boundary_diagnostics=diagnostics,descriptive_checks=aux,sensitivity_summary=pairsummary,
      example_selection_rule='Up to 2 largest positive and 2 most negative D in each category, ties by family_id; no example substitutes for aggregate analysis',selected_example_families=selected)
    writej(out/'primary_statistics.json',stats)
    writej(out/'bootstrap_results.json',dict(seed=6198,resamples=10000,method='Paired stratified whole-schema-lineage cluster percentile bootstrap',
      interval_definition='2.5th and 97.5th percentiles with linear interpolation, not a population interval for real agent deployments',
      sampling_order=CATS,cluster_policy='Sorted lineages in each category; draw K clusters with replacement, preserve every evaluation sibling, then family mean within category; equal category mean',
      clusters_per_category={c:len(clusters[c]) for c in CATS},primary_point=delta,primary_ci95=interval,primary_draws=draws,
      category_ci95={c:ci(catdraw[c]) for c in CATS},corpus_aggregate_delta_ci95=ci(corpusdraw),corpus_aggregate_delta_draws=corpusdraw))
    writej(out/'analysis_verification.json',dict(status='PASS',analysis_script_sha256=sha(Path(__file__).read_bytes()),
      raw_input_sha256=sha((root/'tokenizer_observations.csv').read_bytes()),rows_in_raw_token_counts=len(raw),sensitivity_rows=len(sensitivity),
      analysis_cpu_seconds=time.process_time()-started,fixture_manifest_sha256=sha((root/'record_manifest.json').read_bytes()),
      primary_average_agrees_with_all_family_average=abs(delta-avg(ds.values()))<1e-12))
    print(json.dumps(dict(primary_delta=delta,ci95=interval,outcome=stats['outcome_class'],analysis_cpu_seconds=time.process_time()-started)))
if __name__=='__main__':main()
