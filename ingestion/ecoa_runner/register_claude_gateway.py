import json,urllib.request,re
def env(p,k):
    for l in open(p):
        if l.startswith(k+'='): return l.split('=',1)[1].strip()
RK=env('/opt/ecoa_ingest/.env','RAGFLOW_API_KEY'); GK=env('/opt/stacks/litellm/.env','LITELLM_MASTER_KEY')
B='https://ragflow.srv1231216.hstgr.cloud'
def call(method,path,body=None):
    r=urllib.request.Request(B+path,data=json.dumps(body).encode() if body is not None else None,method=method,headers={'Authorization':'Bearer '+RK,'Content-Type':'application/json'})
    try: return json.load(urllib.request.urlopen(r,timeout=180))
    except Exception as e: return {'error':str(e)[:200]}
P='/api/v1/providers/OpenAI-API-Compatible'
print('provider:',call('PUT','/api/v1/providers',{'provider_name':'OpenAI-API-Compatible'}))
print('instance:',call('POST',P+'/instances',{'instance_name':'CLAUDE_GW','api_key':GK,'base_url':'http://litellm:4000/v1','model_info':[{'model_name':'claude-haiku-5-5','model_type':['chat'],'max_tokens':8192}]}))
for m,mt in [('claude-sonnet-5-5',8192),('claude-opus-5-5',8192),('claude-haiku-5-5',8192)]:
    for t in (['image2text'],['chat']):
        r=call('POST',P+'/instances/CLAUDE_GW/models',{'model_name':m,'model_type':t if len(t)>1 else t[0],'max_tokens':mt})
        print(m,t,r)
print(call('GET',P+'/instances/CLAUDE_GW/models'))
