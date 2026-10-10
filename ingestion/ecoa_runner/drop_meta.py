import os, json, urllib.request
B=os.environ['RAGFLOW_API_SERVER'].rstrip('/'); K=os.environ['RAGFLOW_API_KEY']
AID='c83609aea3fd11f1858cf58865604f65'; DROP='Extractor:eCoAMetadata'
HERE=os.path.dirname(os.path.abspath(__file__))
def req(p,d=None,m='GET'):
    r=urllib.request.Request(B+p,data=json.dumps(d).encode() if d is not None else None,method=m,
      headers={'Authorization':'Bearer '+K,'Content-Type':'application/json'})
    return json.load(urllib.request.urlopen(r,timeout=180))
d=req('/api/v1/agents/'+AID)['data']
json.dump(d,open(HERE+'/agent_before_drop_meta.json','w'),ensure_ascii=False,indent=1)
dsl=d['dsl']; C=dsl['components']
up=C[DROP]['upstream'][0]; down=C[DROP]['downstream'][0]
print('rewiring %s -> %s (removing %s)' % (up,down,DROP))
C[up]['downstream']=[down]; C[down]['upstream']=[up]
del C[DROP]
dsl['graph']['nodes']=[n for n in dsl['graph']['nodes'] if n['id']!=DROP]
edges=[e for e in dsl['graph']['edges'] if DROP not in (e.get('source'),e.get('target'))]
tmpl=next(e for e in dsl['graph']['edges'] if e.get('target')==DROP)
new=dict(tmpl); new['source']=up; new['target']=down
new['id']='xy-edge__%s%s-%s%s' % (up,new.get('sourceHandle','start'),down,new.get('targetHandle','end'))
edges.append(new); dsl['graph']['edges']=edges
print(req('/api/v1/agents/'+AID,{'title':d['title'],'dsl':dsl},'PUT'))
v=req('/api/v1/agents/'+AID)['data']['dsl']
for n,c in v['components'].items(): print('  %-26s up=%s down=%s'%(n,c.get('upstream'),c.get('downstream')))
print('  nodes:',[n['id'] for n in v['graph']['nodes']])
print('  edges:',[(e['source'],'->',e['target']) for e in v['graph']['edges']])
