// Rebuild the 215 from the shipped generator + data, exactly as HANDOFF §1 describes.
const fs=require('fs'),path=require('path');
const src=fs.readFileSync(__dirname+'/icoa3_gen.js','utf8');
const build=new Function('return ('+src+')')();
const recs=JSON.parse(fs.readFileSync(__dirname+'/icoa_v44_recs.json','utf8'));
const plan=JSON.parse(fs.readFileSync(__dirname+'/coq_plan.json','utf8'));
const meta={}; for(const p of plan) meta[p.rec.cult]=Object.assign({strainCode:p.strainCode},p.rec);
const out=process.argv[2]||(__dirname+'/build');
const rows=[];
for(const r of recs){ const o=build(r,meta[r.cu]||{});
  const f=path.join(out,o.path); fs.mkdirSync(path.dirname(f),{recursive:true}); fs.writeFileSync(f,o.html);
  rows.push([r.code,r.cu,r.p,r.strain,o.dir,r.series,r.tested,r.packaging,r.issued,o.conforms?'conforms':'open',o.path].join('\t')); }
fs.writeFileSync(path.join(out,'_built.tsv'),'code\tcu\tp\tstrain\tdir\tseries\ttested\tpackaging\tissued\tconforms\tpath\n'+rows.join('\n')+'\n');
console.log('built',rows.length);
