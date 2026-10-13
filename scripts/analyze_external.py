"""Independent standard-library analysis of frozen external counts, no encoding."""
import argparse,csv,json,hashlib,math,random,time
from pathlib import Path
from collections import defaultdict
SOURCES=['mcp','a2a','sweagent'];FORMATS=['compact','spaced','indent2','tab']
PAIRS={'t180k_vs_bpe':('bpe200k','superbpe_t180k'),'t80k_vs_bpe':('bpe200k','superbpe_t80k'),'no_whitespace_vs_bpe':('bpe200k','no_whitespace200k'),'t180k_vs_no_whitespace':('no_whitespace200k','superbpe_t180k')}
def sha(b):return hashlib.sha256(b).hexdigest()
def mean(xs):
    v=list(xs);return math.fsum(v)/len(v) if v else None
def writej(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\r\n')
def writecsv(p,rs):
    with p.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def percentile(v,q):
    v=sorted(v);z=(len(v)-1)*q;j=int(z);return v[j]+(v[min(j+1,len(v)-1)]-v[j])*(z-j)
def ci(v):return [percentile(v,.025),percentile(v,.975)]
def correlation(x,y):
    if len(x)<2:return None
    mx,my=mean(x),mean(y);den=math.fsum((z-mx)**2 for z in x)*math.fsum((z-my)**2 for z in y)
    return math.fsum((z-mx)*(v-my) for z,v in zip(x,y))/math.sqrt(den) if den else None
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();r=a.root;o=a.output or r;o.mkdir(parents=True,exist_ok=True);start=time.process_time()
    mf=json.loads((r/'record_manifest.json').read_bytes());assert json.loads((r/'checks.json').read_bytes())['status']=='PASS'
    meta={x['record_id']:x for x in mf['records']};ids=sorted(meta);by_source={s:[i for i in ids if meta[i]['source']==s] for s in SOURCES}
    rows=list(csv.DictReader((r/'external_token_counts.csv').open(encoding='utf-8',newline='')))
    for x in rows:
        for k in ['tokens','utf8_bytes','unicode_codepoints','baseline_pretoken_boundaries']+[k for k in x if k.endswith('_tokens')]:x[k]=int(x[k])
    data={(x['record_id'],x['format'],x['tokenizer']):x for x in rows};assert len(rows)==len(data)==len(ids)*16
    g={(p,i,f):1-data[(i,f,s)]['tokens']/data[(i,f,b)]['tokens'] for p,(b,s) in PAIRS.items() for i in ids for f in FORMATS}
    ds={(p,i):g[(p,i,'indent2')]-g[(p,i,'compact')] for p in PAIRS for i in ids}
    def aggregate(ii,p,f):
        b,s=PAIRS[p];nb=sum(data[(i,f,b)]['tokens'] for i in ii);ns=sum(data[(i,f,s)]['tokens'] for i in ii);bb=sum(data[(i,f,b)]['utf8_bytes'] for i in ii);cp=sum(data[(i,f,b)]['unicode_codepoints'] for i in ii)
        return dict(records=len(ii),utf8_bytes=bb,unicode_codepoints=cp,baseline_tokens=nb,comparison_tokens=ns,absolute_token_savings=nb-ns,mean_absolute_token_savings=(nb-ns)/len(ii),
          family_average_G=mean(g[(p,i,f)] for i in ii),corpus_aggregate_G=1-ns/nb,regressing_records=sum(g[(p,i,f)]<0 for i in ii),zero_saving_records=sum(g[(p,i,f)]==0 for i in ii),
          baseline_bytes_per_token=bb/nb,comparison_bytes_per_token=bb/ns,baseline_codepoints_per_token=cp/nb,comparison_codepoints_per_token=cp/ns)
    pairs={p:{s:{f:aggregate(by_source[s] if s!='pooled' else ids,p,f) for f in FORMATS} for s in SOURCES+['pooled']} for p in PAIRS}
    record_rows=[];paired=[]
    for i in ids:
        x=meta[i];q={k:x[k] for k in ['record_id','source','record_kind','schema_lineage','compact_bytes','container_depth','key_count','string_values','string_value_bytes','max_string_value_bytes','shape_sha256']}
        q.update({p+'_D':ds[(p,i)] for p in PAIRS});q['indent2_byte_inflation']=data[(i,'indent2','bpe200k')]['utf8_bytes']/data[(i,'compact','bpe200k')]['utf8_bytes']-1
        q['spanning_fraction_change']=data[(i,'indent2','superbpe_t180k')]['boundary_spanning_tokens']/data[(i,'indent2','superbpe_t180k')]['tokens']-data[(i,'compact','superbpe_t180k')]['boundary_spanning_tokens']/data[(i,'compact','superbpe_t180k')]['tokens']
        record_rows.append(q)
        for p,(b,s) in PAIRS.items():
            for f in FORMATS:
                xx,yy=data[(i,f,b)],data[(i,f,s)]
                paired.append(dict(record_id=i,source=x['source'],record_kind=x['record_kind'],schema_lineage=x['schema_lineage'],pair=p,format=f,baseline_tokenizer=b,comparison_tokenizer=s,utf8_bytes=xx['utf8_bytes'],unicode_codepoints=xx['unicode_codepoints'],baseline_tokens=xx['tokens'],comparison_tokens=yy['tokens'],absolute_token_savings=xx['tokens']-yy['tokens'],relative_savings=g[(p,i,f)]))
    writecsv(o/'external_record_effects.csv',record_rows);writecsv(o/'external_paired_counts.csv',paired)
    metrics=[]
    for p in pairs:
        for s in pairs[p]:
            for f,x in pairs[p][s].items():metrics.append(dict(source=s,pair=p,format=f,**x))
    writecsv(o/'external_source_metrics.csv',metrics)
    clusters={}
    for s in SOURCES:
        d=defaultdict(list)
        for i in by_source[s]:d[meta[i]['schema_lineage']].append(i)
        clusters[s]=[v for _,v in sorted(d.items())]
    rng=random.Random(6198);source_draws={s:{p:[] for p in PAIRS} for s in SOURCES};source_indent_ws={s:[] for s in SOURCES};fixed=[]
    for _ in range(10000):
        means=[]
        for s in SOURCES:
            cc=clusters[s];ii=[i for _j in cc for i in cc[rng.randrange(len(cc))]]
            for p in PAIRS:source_draws[s][p].append(mean(ds[(p,i)] for i in ii))
            source_indent_ws[s].append(mean(g[('t180k_vs_no_whitespace',i,'indent2')] for i in ii));means.append(source_draws[s]['t180k_vs_bpe'][-1])
        fixed.append(mean(means))
    source_mean={s:mean(ds[('t180k_vs_bpe',i)] for i in by_source[s]) for s in SOURCES}
    source_composition=[mean(source_mean[SOURCES[rng.randrange(3)]] for _j in SOURCES) for _ in range(10000)]
    source_stats={s:dict(records=len(by_source[s]),lineages=len(clusters[s]),kind_counts={k:sum(meta[i]['record_kind']==k for i in by_source[s]) for k in sorted({meta[i]['record_kind'] for i in by_source[s]})},
        primary_D=source_mean[s],conditional_cluster_ci95=ci(source_draws[s]['t180k_vs_bpe']),positive_D=sum(ds[('t180k_vs_bpe',i)]>0 for i in by_source[s]),negative_D=sum(ds[('t180k_vs_bpe',i)]<0 for i in by_source[s]),zero_D=sum(ds[('t180k_vs_bpe',i)]==0 for i in by_source[s]),
        all_pair_D={p:dict(estimate=mean(ds[(p,i)] for i in by_source[s]),conditional_cluster_ci95=ci(source_draws[s][p])) for p in PAIRS},
        indent2_t180k_vs_no_whitespace_G_ci95=ci(source_indent_ws[s])) for s in SOURCES}
    leave_sources={s:mean(source_mean[z] for z in SOURCES if z!=s) for s in SOURCES}
    lineage_sensitivity={}
    for s in SOURCES:
        local_means=[mean(ds[('t180k_vs_bpe',i)] for i in v) for v in clusters[s]]
        left=[mean(ds[('t180k_vs_bpe',i)] for i in by_source[s] if i not in v) for v in clusters[s]]
        lineage_sensitivity[s]=dict(equal_lineage_D=mean(local_means),positive_lineage_means=sum(v>0 for v in local_means),negative_lineage_means=sum(v<0 for v in local_means),lineage_sizes=[len(v) for v in clusters[s]],leave_one_lineage_D_range=[min(left),max(left)],exact_shape_count=len({meta[i]['shape_sha256'] for i in by_source[s]}))
    grouped=[]
    def group(label,ii):
        if not ii:return
        grouped.append(dict(group=label,records=len(ii),sources=len({meta[i]['source'] for i in ii}),lineages=len({meta[i]['schema_lineage'] for i in ii}),mean_D=mean(ds[('t180k_vs_bpe',i)] for i in ii),compact_G=mean(g[('t180k_vs_bpe',i,'compact')] for i in ii),indent2_G=mean(g[('t180k_vs_bpe',i,'indent2')] for i in ii),indent2_t180k_vs_no_whitespace_G=mean(g[('t180k_vs_no_whitespace',i,'indent2')] for i in ii)))
    for s in ['all']+SOURCES:
        ss=ids if s=='all' else by_source[s]
        for name,lo,hi in [('compact_<256',0,256),('compact_256-1023',256,1024),('compact_>=1024',1024,float('inf'))]:group(s+'/'+name,[i for i in ss if lo<=meta[i]['compact_bytes']<hi])
        for name,lo,hi in [('longest_string_<64',0,64),('longest_string_64-255',64,256),('longest_string_>=256',256,float('inf'))]:group(s+'/'+name,[i for i in ss if lo<=meta[i]['max_string_value_bytes']<hi])
        group(s+'/depth_<=3',[i for i in ss if meta[i]['container_depth']<=3]);group(s+'/depth_>=4',[i for i in ss if meta[i]['container_depth']>=4])
    for k in sorted({meta[i]['record_kind'] for i in ids}):group('kind/'+k,[i for i in ids if meta[i]['record_kind']==k])
    writecsv(o/'structure_sensitivity.csv',grouped)
    corrs={}
    for s in ['all']+SOURCES:
        rr=[x for x in record_rows if s=='all' or x['source']==s]
        corrs[s]={k:correlation([x[k] for x in rr],[x['t180k_vs_bpe_D'] for x in rr]) for k in ['compact_bytes','indent2_byte_inflation','string_value_bytes','max_string_value_bytes','key_count','spanning_fraction_change']}
    kinds={k:dict(records=sum(meta[i]['record_kind']==k for i in ids),mean_D=mean(ds[('t180k_vs_bpe',i)] for i in ids if meta[i]['record_kind']==k)) for k in sorted({meta[i]['record_kind'] for i in ids})}
    diagnostic_cols=[k for k in rows[0] if k.endswith('_tokens') and k!='tokens']
    diags={}
    for s in SOURCES+['pooled']:
        ii=by_source[s] if s!='pooled' else ids;diags[s]={}
        for role in ['bpe200k','superbpe_t180k','superbpe_t80k','no_whitespace200k']:
            diags[s][role]={}
            for f in FORMATS:
                rr=[data[(i,f,role)] for i in ii];z={k:sum(x[k] for x in rr) for k in ['tokens']+diagnostic_cols};z['spanning_fraction']=z['boundary_spanning_tokens']/z['tokens'];diags[s][role][f]=z
    stats=dict(status='VALID_EXTERNAL_ONLY',record_count=len(ids),principal_descriptive_estimand='Equal-source mean of within-source equal-record D; external only',equal_source_D=mean(source_mean.values()),equal_source_fixed_source_cluster_ci95=ci(fixed),
        pooled_equal_record_D=mean(ds[('t180k_vs_bpe',i)] for i in ids),pooled_corpus_D=pairs['t180k_vs_bpe']['pooled']['indent2']['corpus_aggregate_G']-pairs['t180k_vs_bpe']['pooled']['compact']['corpus_aggregate_G'],
        source_composition_resampling_range95=ci(source_composition),source_composition_interpretation='Only three convenience sources; percentile range is a composition diagnostic, not deployment-population inference',
        sources=source_stats,pair_summaries=pairs,lineage_sensitivity=lineage_sensitivity,leave_one_source_equal_source_D=leave_sources,structure_groups=grouped,record_kinds=kinds,descriptive_correlations=corrs,boundary_diagnostics=diags,
        positive_D_records=sum(ds[('t180k_vs_bpe',i)]>0 for i in ids),negative_D_records=sum(ds[('t180k_vs_bpe',i)]<0 for i in ids),zero_D_records=sum(ds[('t180k_vs_bpe',i)]==0 for i in ids),
        synthetic_combined=False,interpretation_limit='184 protocol schema fragments and only 24 curated runtime artifacts from two tasks. A schema result does not prove a broad real-trace effect.')
    writej(o/'external_statistics.json',stats)
    writej(o/'external_bootstrap_results.json',dict(seed=6198,resamples=10000,method='Paired whole-lineage bootstrap stratified by fixed source',fixed_source_equal_source_D_draws=fixed,fixed_source_ci95=ci(fixed),source_primary_D_draws={s:source_draws[s]['t180k_vs_bpe'] for s in SOURCES},source_t180k_vs_no_whitespace_indent2_G_ci95={s:ci(source_indent_ws[s]) for s in SOURCES},source_composition_draws=source_composition,source_composition_range95=ci(source_composition),not_deployment_population_inference=True))
    writej(o/'external_analysis_verification.json',dict(status='PASS',python_version=__import__('platform').python_version(),analysis_script_sha256=sha(Path(__file__).read_bytes()),input_counts_sha256=sha((r/'external_token_counts.csv').read_bytes()),analysis_cpu_seconds=time.process_time()-start,observations=len(rows),records=len(ids),synthetic_rows_included=0))
    print(json.dumps(dict(equal_source_D=stats['equal_source_D'],conditional_ci95=stats['equal_source_fixed_source_cluster_ci95'],source_D=source_mean,pooled_D=stats['pooled_equal_record_D'],cpu_seconds=time.process_time()-start)),flush=True)
if __name__=='__main__':main()
