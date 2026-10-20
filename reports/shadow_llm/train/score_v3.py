import json,sys
D='lora_data_v3b/'
def gold(split):
    ids=json.load(open(D+('test_ids.json' if split=='test' else 'test_ts_ids.json')))
    rows=[json.loads(l) for l in open(D+split+'.jsonl')]
    g={}
    for i,r in zip(ids,rows):
        a=json.loads(r['messages'][-1]['content']); g[i]=a
    return g
def loadpred(p):
    if p.endswith('.json'):
        return json.load(open(p))
    out={}
    for l in open(p):
        r=json.loads(l); out[r['id']]=r
    return out
def score(g,p,name):
    print('==',name, 'n=',len(g),'missing=',sum(1 for i in g if i not in p))
    for f in ('citable','definition'):
        tp=fp=fn=0
        for i,a in g.items():
            pr=p.get(i,{}).get(f,'n'); gy=a[f]=='y'
            if pr=='y' and gy: tp+=1
            elif pr=='y': fp+=1
            elif gy: fn+=1
        P=tp/(tp+fp) if tp+fp else 0; R=tp/(tp+fn) if tp+fn else 0; F=2*P*R/(P+R) if P+R else 0
        print(f'  {f:10s} P {P*100:5.1f} R {R*100:5.1f} F1 {F*100:5.1f} (gold y {tp+fn}, pred y {tp+fp})')
gt=gold('test'); gs=gold('test_ts')
score(gt,loadpred('ollama_v2/pred_test.jsonl'),'v2 general')
score(gs,loadpred('ts_v2_pred.json'),'v2 ts')
for v in ('v3','v3b'):
    score(gt,loadpred(f'lora_q25_3b_{v}/pred_test_newgold.jsonl'),v+' general')
    score(gs,loadpred(f'lora_q25_3b_{v}/pred_test_ts.jsonl'),v+' ts')
print('\n######## SLICES')
ds={}
for l in open('dataset_v3.jsonl'):
    r=json.loads(l); ds[r['id']]=r
ts={}
for l in open('dataset_ts_v1.jsonl'):
    r=json.loads(l); ts[r['id']]=r
SP=sys.argv[1] if len(sys.argv)>1 else './'  # ts_ans.json·ts_ans2.json(검수 답) 위치
tsrev={a['id'] for f in ('ts_ans.json','ts_ans2.json') for a in json.load(open(SP+f))}
P={'v2':(loadpred('ollama_v2/pred_test.jsonl'),loadpred('ts_v2_pred.json'))}
for v in ('v3','v3b'):
    P[v]=(loadpred(f'lora_q25_3b_{v}/pred_test_newgold.jsonl'),loadpred(f'lora_q25_3b_{v}/pred_test_ts.jsonl'))
slices={
 'general: human_reviewed':{i:a for i,a in gt.items() if ds.get(i,{}).get('human_reviewed')},
 'general: decision-tagged':{i:a for i,a in gt.items() if ds.get(i,{}).get('tag') in ('footnote','kf_list','mechanism','capacity')},
 'general: rest':{i:a for i,a in gt.items() if not ds.get(i,{}).get('human_reviewed') and ds.get(i,{}).get('tag') not in ('footnote','kf_list','mechanism','capacity')},
 'ts: human_reviewed':{i:a for i,a in gs.items() if i in tsrev},
}
for name,g in slices.items():
    print('\n####',name,len(g))
    for v,(pg,pt) in P.items():
        score(g, pt if name.startswith('ts') else pg, v)
