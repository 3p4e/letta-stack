import re,sys,os
CSS=open("/tmp/imb/fonts_inline.css",encoding="utf-8").read()
STYLE="<style>\n"+CSS+"\n</style>"
def prep(src,dst):
    h=open(src,encoding="utf-8",errors="replace").read()
    # drop google-fonts preconnect/stylesheet links, inject inlined fonts
    h2=re.sub(r'<link[^>]*fonts\.(googleapis|gstatic)\.com[^>]*>','',h,flags=re.I)
    n=len(re.findall(r'fonts\.(?:googleapis|gstatic)\.com',h))
    if '</head>' in h2: h2=h2.replace('</head>',STYLE+'\n</head>',1)
    else: h2=STYLE+h2
    open(dst,"w",encoding="utf-8").write(h2)
    return n,len(re.findall(r'https?://(?!schemas|www\.w3)',h2))
if __name__=="__main__":
    a,b=prep(sys.argv[1],sys.argv[2]); print("removed gf refs:",a,"| remaining ext urls:",b)
