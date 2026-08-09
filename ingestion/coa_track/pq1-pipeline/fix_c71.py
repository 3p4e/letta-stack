#!/usr/bin/env python3
"""Fix C71 → C171 typo in Letta source filenames (6 files)."""
import asyncio, base64, json, pathlib
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

URL = "https://mcp-letta.srv1231216.hstgr.cloud/mcp"
SRC = "source-dd320361-43a1-42c1-939a-66530dfab85e"
PDFS = pathlib.Path("/tmp/pq1_pdfs")

# 6 affected samples
AFFECTED = ["1179","1180","1204","1205","1218","1219"]

def parse(res):
    if res.isError: return {"success":False}
    for c in res.content:
        txt = getattr(c,"text",None)
        if txt:
            try: return json.loads(txt)
            except: return {"success":False,"raw":txt[:200]}
    return {"success":False}

async def main():
    async with streamablehttp_client(URL) as (r,w,_):
        async with ClientSession(r,w) as s:
            await s.initialize()
            data = parse(await s.call_tool("letta_source_manager",
                {"operation":"list_files","source_id":SRC,"limit":200}))
            files = data.get("data",[])

            # Find files where filename contains _RO_C71_ and matches one of AFFECTED ids
            to_fix = []
            for f in files:
                fn = f["file_name"]
                if "_RO_C71_" not in fn: continue
                sid = fn.split("_")[-1].replace(".pdf","")  # last underscore segment
                if sid not in AFFECTED: continue
                new = fn.replace("_RO_C71_","_RO_C171_")
                to_fix.append((f["id"], fn, new, sid))

            print(f"Found {len(to_fix)} files to rename:")
            for fid,old,new,sid in to_fix:
                print(f"  {old}  →  {new}")

            for fid, old, new, sid in to_fix:
                # Delete old
                d = parse(await s.call_tool("letta_source_manager",
                    {"operation":"delete_files","source_id":SRC,"file_id":fid}))
                if not d.get("success"):
                    print(f"  DEL_FAIL {old}: {d}")
                    continue
                # Upload from local PDF (find original filename — "1179 П.pdf")
                local = PDFS / f"{sid} П.pdf"
                if not local.exists():
                    print(f"  MISS local {local}")
                    continue
                b64 = base64.b64encode(local.read_bytes()).decode()
                u = parse(await s.call_tool("letta_source_manager",
                    {"operation":"upload","source_id":SRC,
                     "file_name":new,"file_data":b64,"content_type":"application/pdf"}))
                ok = u.get("success")
                print(f"  {'OK ' if ok else 'FAIL'} {new}")

asyncio.run(main())
