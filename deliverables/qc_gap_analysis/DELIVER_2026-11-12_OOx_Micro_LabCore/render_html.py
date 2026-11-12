import os,sys,json,base64,subprocess
U=os.environ['RUNNER_URL']
def call(p,b):
    r=subprocess.run(['curl','-sS','-m','300','-X','POST','-H','Authorization: Bearer '+os.environ['RUNNER_TOKEN'],'-H','Content-Type: application/json','--data-binary','@-',U+p],input=json.dumps(b).encode(),capture_output=True);return json.loads(r.stdout)
src,out,kind=sys.argv[1],sys.argv[2],sys.argv[3]   # kind: html|docx
call('/shell',{'cmd':'mkdir -p /tmp/bb && docker exec gotenberg mkdir -p /tmp/bb','timeout':60})
name='index.html' if kind=='html' else 'in.docx'
call('/file/write',{'path':'/tmp/bb/'+name,'content_b64':base64.b64encode(open(src,'rb').read()).decode(),'mode':420})
ep='chromium/convert/html -F preferCssPageSize=true -F printBackground=true' if kind=='html' else 'libreoffice/convert'
ep=ep.split(' ',1); extra=ep[1] if len(ep)>1 else ''
r=call('/shell',{'cmd':f'docker cp /tmp/bb/{name} gotenberg:/tmp/bb/{name} && docker exec gotenberg curl -sS -f -o /tmp/bb/o.pdf -F files=@/tmp/bb/{name} {extra} http://localhost:3000/forms/{ep[0]} && docker cp gotenberg:/tmp/bb/o.pdf /tmp/bb/o.pdf','timeout':240})
d=call('/file/read',{'path':'/tmp/bb/o.pdf','max_bytes':8000000}); open(out,'wb').write(base64.b64decode(d['content_b64']))
call('/shell',{'cmd':'rm -rf /tmp/bb; docker exec gotenberg rm -rf /tmp/bb','timeout':60})
