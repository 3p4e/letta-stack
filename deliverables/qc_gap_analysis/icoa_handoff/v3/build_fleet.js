// Rebuild the 215 from the shipped generator + data, exactly as HANDOFF §1 describes.
const fs=require('fs'),path=require('path');
// The deposited signatures of the QA Manager and the Head of QC. Off unless
// PP_SIGNATURES=1 is set; the Analyst box has no deposit and keeps its rule.
const SIGN=require(path.resolve(__dirname,'../../sign_block.js'));
const src=fs.readFileSync(__dirname+'/icoa3_gen.js','utf8');
const build=new Function('return ('+src+')')();
let recs=JSON.parse(fs.readFileSync(__dirname+'/icoa_v44_recs.json','utf8'));
// One certificate of quality, one internal certificate of analysis (Head of QC,
// 18.09.2026: "there is one CoQ, one retest iCoA"). The record planned a document for
// every testing ROUND a batch has, and a lot re-analysed by the 197 campaign in August,
// the 220 campaign a fortnight later and the 227 campaign in September acquires retest 1,
// 2 and 3 - while the desk issues ONE retest certificate of quality for it. Counted
// rather than assumed: the 172 certificates of quality cite 172 internal certificates,
// every one of them printed, and 43 further documents are cited by nothing at all.
// The fleet is therefore exactly what the certificates cite. Nothing is deleted from the
// record: icoa_v44_recs.json keeps every planned round, and an uncited round prints only
// when a certificate of quality comes to cite it.
const _coq=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../coq_artifact_data.json'),'utf8'));
const _cited=new Set(_coq.coqs.map(c=>String(c.icoa_code||'').trim()).filter(c=>c.indexOf('iCoA-PP_')===0));
const _all=recs.length;
recs=recs.filter(r=>_cited.has(r.code));
if(recs.length!==_cited.size) throw new Error('the certificates cite '+_cited.size+
  ' internal certificates and the record holds '+recs.length+' of them');
console.log('internal certificates: '+recs.length+' cited by a certificate of quality, '+
            (_all-recs.length)+' planned rounds not cited and not printed');
const plan=JSON.parse(fs.readFileSync(__dirname+'/coq_plan.json','utf8'));
const meta={}; for(const p of plan) meta[p.rec.cult]=Object.assign({strainCode:p.strainCode},p.rec);
const out=process.argv[2]||(__dirname+'/build');
const rows=[];
for(const r of recs){ const o=build(r,meta[r.cu]||{});
  o.html=SIGN.sign(o.html,r.code,{h:52,dy:-9});
  const f=path.join(out,o.path); fs.mkdirSync(path.dirname(f),{recursive:true}); fs.writeFileSync(f,o.html);
  rows.push([r.code,r.cu,r.p,r.strain,o.dir,r.series,r.tested,r.packaging,r.issued,o.conforms?'conforms':'open',o.path].join('\t')); }
fs.writeFileSync(path.join(out,'_built.tsv'),'code\tcu\tp\tstrain\tdir\tseries\ttested\tpackaging\tissued\tconforms\tpath\n'+rows.join('\n')+'\n');
console.log('built',rows.length);
