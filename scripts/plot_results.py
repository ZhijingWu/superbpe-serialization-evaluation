"""Plot saved estimates and intervals. Does not tokenize data or rerun bootstrap."""
import argparse,json
from pathlib import Path
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=Path('build/figures'));a=ap.parse_args()
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    r=Path(__file__).resolve().parents[1];old=json.loads((r/'results/synthetic/primary_statistics.json').read_bytes());s=json.loads((r/'results/external/external_statistics.json').read_bytes())
    labels=['Synthetic pilot (100 families)','MCP (91 schemas; 10 groups)','A2A (93 schemas; 8 groups)','SWE-agent (24 objects; 2 tasks)','External equal-source mean']
    values=[old['primary_estimate']]+[s['sources'][x]['primary_D'] for x in ['mcp','a2a','sweagent']]+[s['equal_source_D']]
    cis=[old['primary_ci95']]+[s['sources'][x]['conditional_cluster_ci95'] for x in ['mcp','a2a','sweagent']]+[s['equal_source_fixed_source_cluster_ci95']]
    fig,ax=plt.subplots(figsize=(8,4),layout='constrained')
    for j,(v,interval) in enumerate(zip(values,cis)):
        col=['#777777','#0072B2','#D55E00','#009E73','#20262e'][j];ax.hlines(j,interval[0]*100,interval[1]*100,color=col,lw=2);ax.scatter(v*100,j,c=col,s=40)
    ax.set(yticks=range(5),yticklabels=labels,xlim=(0,22),xlabel='Indent-2 minus compact G (percentage points)');ax.invert_yaxis();ax.grid(axis='x',alpha=.16);ax.axvline(5,color='#777777',ls=':',lw=1)
    a.output.mkdir(parents=True,exist_ok=True);fig.savefig(a.output/'effect_comparison.png',dpi=250);plt.close(fig)
    print('Figure generated from saved statistics; no new experiment.')
if __name__=='__main__':main()
