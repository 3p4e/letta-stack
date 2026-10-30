"""Build the HPLC training course: content.py -> HTML -> A4 PDF (Chromium via Playwright)."""
import html, os, subprocess, sys
from PIL import Image
from content import MODULES, GS, OPG, SUG, IM, TH, VA, TS, WI

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, 'fig')
IMG = os.path.join(HERE, 'img')
PHOTOS = os.environ.get('PP_PHOTOS', os.path.join(HERE, 'photos')).split(os.pathsep)
os.makedirs(IMG, exist_ok=True)

SRC = {'GS': (GS, 0), 'OPG': (OPG, 0), 'SUG': (SUG, 0), 'IM': (IM, 0), 'TH': (TH, 0)}


def image(fid, maxw=1500):
    """Return a compressed JPEG path for a figure id or a PHOTO:<file>."""
    if fid.startswith('PHOTO:'):
        name = fid[6:]
        src = next(os.path.join(d, name) for d in PHOTOS if os.path.exists(os.path.join(d, name)))
        out = os.path.join(IMG, 'photo_' + os.path.splitext(name)[0] + '.jpg')
        maxw = 1300
    else:
        src = os.path.join(FIG, fid + '.png')
        out = os.path.join(IMG, fid + '.jpg')
    if not os.path.exists(out):
        im = Image.open(src).convert('RGB')
        if im.width > maxw:
            im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
        im.save(out, quality=82, optimize=True)
    return out


def source_of(fid):
    if fid.startswith('PHOTO:'):
        return 'Photograph of our instrument screen, 30.10.2026 / 15.09.2026'
    man, page, _ = fid.split('_')
    return f'Source: {SRC[man][0]}, p. {page}'


def fig_html(fid, caption='', width=None):
    path = image(fid)
    with Image.open(path) as im:
        w, h = im.size
    if width is None:   # pick a width from the aspect ratio so short wide strips stay legible
        width = 88 if w / h > 2.2 else 70 if w / h > 1.2 else 52
    cap = (html.escape(caption) + ' ' if caption else '') + f'<span class="src">{html.escape(source_of(fid))}</span>'
    return (f'<figure style="width:{width}%"><img src="file://{path}"/>'
            f'<figcaption>{cap}</figcaption></figure>')


def block(b, mod_no, counter):
    kind = b[0]
    if kind == 'h':
        return f'<h3>{html.escape(b[1])}</h3>'
    if kind == 'p':
        return f'<p>{b[1]}</p>'
    if kind == 'fig':
        return fig_html(b[1], b[2], b[3] if len(b) > 3 else None)
    if kind == 'figrow':
        cells = ''.join(f'<div class="cell">{fig_html(f, c, 100)}</div>' for f, c in b[1])
        return f'<div class="figrow">{cells}</div>'
    if kind == 'box':
        _, k, title, body = b
        label = {'gmp': 'GMP', 'lab': 'OUR LAB', 'warn': 'CAUTION', 'tip': 'TIP'}[k]
        return f'<div class="box {k}"><div class="boxhead"><span class="tag">{label}</span>{html.escape(title)}</div><div class="boxbody">{body}</div></div>'
    if kind == 'table':
        _, head, rows = b
        th = ''.join(f'<th>{h}</th>' for h in head)
        tr = ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in rows)
        return f'<table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>'
    if kind == 'steps':
        _, steps, src = b
        out = ['<ol class="steps">']
        for text, fid in steps:
            counter[0] += 1
            if not fid:
                out.append(f'<li><div class="stepno">{counter[0]}</div><div class="steptext">{text}</div></li>')
                continue
            with Image.open(image(fid)) as im:
                wide = im.width / im.height > 2.0
            if wide:   # a wide strip reads best under the text
                out.append(f'<li><div class="stepno">{counter[0]}</div><div class="steptext">{text}{fig_html(fid, width=96)}</div></li>')
            else:
                out.append(f'<li class="two"><div class="stepno">{counter[0]}</div><div class="steptext">{text}</div>'
                           f'<div class="stepfig">{fig_html(fid, width=100)}</div></li>')
        out.append(f'</ol><div class="stepsrc">Procedure source: {html.escape(src)}</div>')
        return ''.join(out)
    raise ValueError(kind)


QUIZ = [
 ('Which documents on file qualify the hardware (pump, oven, PDA, autosampler) of our analyser?', 'None. IQ/OQ/EQR 0008090850 qualify the LabSolutions DB software and PC only; a hardware OQ and PQ are outstanding (Module 1.3).'),
 ('Name the four LabSolutions file types and which one is the raw data.', '.lcm method, .lcb batch, .lcd data, .lsr report format. The .lcd (all-in-one) is the raw data (1.2).'),
 ('Why must lines C and D be filled although the method uses only A and B?', 'Low-pressure gradient pump: air in the gradient (proportioning) valve or lines makes retention times fluctuate (Operators Guide p. 33; 4.1).'),
 ('You raise the flow from 1.0 to 1.5 mL/min and the pressure stays at 43 bar. What are the first two things to check?', 'Is the drain valve open? Is a flow-line connection leaking? Then: air in the pump head, check valves, suction filter (Virtual Advisor; 4.4, 12.1).'),
 ('A flow rate typed in the Instrument Monitor: is it saved in the method? Where is it recorded?', 'No. It is only recorded in the operation log (Log Browser) (Operators Guide p. 26; 3.4).'),
 ('How long should the D2 lamp be on before analysis?', 'About 1 hour (1–1.5 h for high sensitivity) (Virtual Advisor; 4.4).'),
 ('What does Vial# −1 do, and why is it the first row of our batch?', 'Acquires without injecting; it tests mobile phase, pump and detector before anything is injected (5; 6.9).'),
 ('What Sample Type do the first and following calibration standards get?', 'First: Standard + Initialize Calibration Curve "1: Standard (I)"; following: Standard + Add Calibration Level (6.3).'),
 ('Which Batch Table setting makes the batch stop when the SST fails?', '[Action] cell: Test = System Suitability, Result = Fail, Action = Stop (Wait Next Queue) (6.7).'),
 ('What is the identification allowance for a peak at 5.00 min with a 5 % window?', '± (5.00 × 5/100 + 0.02) = ± 0.27 min (7.3).'),
 ('Why can a peak be reported as "CBD" when it is not CBD?', 'The software names whatever peak falls in the window; shifted chromatography puts another compound there. Confirm with retention time of the day\'s standard and the PDA spectrum (7.3, 8.2).'),
 ('Changing Width or Slope in [Data Analysis] changes which results?', 'Only the open data file, until exported to the method and re-applied (7.1).'),
 ('A spectrum shows maxima at ~270 and ~305 nm. Acidic or neutral cannabinoid?', 'Acidic (THCA/CBDA/CBGA) (8.2).'),
 ('A spectrum goes strongly negative below 250 nm. What does it mean?', 'The mobile-phase background changed after zeroing (composition); not an analyte; 220 nm results unreliable (8.2).'),
 ('Which column-performance method gives Ph. Eur. calculations?', 'EP on the [Performance] tab (7.6).'),
 ('What happens if you try to close a changed method that has "Input reason when saving file" set?', 'A window lists the changes and cannot be closed until a reason is entered (10.2).'),
 ('When must the PDA wavelength check (D2/Ho) be done?', 'Installation, lamp change, cell change, moving the detector, validation (11.1).'),
 ('How often is the plunger-rinse solution (10 % 2-propanol) replaced?', 'Weekly, even if it looks clean (11.3).'),
 ('Cyclic, regular baseline waviness: which cause does the manual give?', 'Air conditioning blowing on the detector or large room-temperature swings (Operators Guide p. 36; 12.2).'),
 ('On 30.10.2026, why could the air conditioning not be the root cause?', 'The disturbance was in a no-injection blank and at the same time in successive runs; selectivity changed; the column was in a 50 °C oven; pressure did not follow flow (12.3).'),
]


def build(out_pdf):
    counter = [0]
    toc = ''.join(f'<li><span>Module {m["no"]}</span> {html.escape(m["title"])}</li>' for m in MODULES)
    body = []
    for m in MODULES:
        counter[0] = 0
        body.append(f'<section class="module"><div class="modhead"><div class="modno">Module {m["no"]}</div>'
                    f'<h2>{html.escape(m["title"])}</h2><div class="goal"><b>Objective.</b> {m["goal"]}</div></div>')
        body.extend(block(b, m['no'], counter) for b in m['blocks'])
        body.append('</section>')
    quiz = ''.join(f'<li>{html.escape(q)}<div class="ansline"></div></li>' for q, _ in QUIZ)
    key = ''.join(f'<li>{html.escape(a)}</li>' for _, a in QUIZ)
    refs = [
      'Shimadzu Corp. <i>LC Getting Started Guide</i>, 223-10811C, Apr. 2019.',
      'Shimadzu Corp. <i>LabSolutions DB Operators Guide</i>, 223-10821H, Jul. 2023.',
      'Shimadzu Corp. <i>LabSolutions DB System Users Guide</i>, 223-10815S, Dec. 2023.',
      'Shimadzu Corp. <i>LabSolutions DB Installation &amp; Maintenance Guide</i>, 223-10817AC, Oct. 2023.',
      'Shimadzu Corp. <i>LabSolutions Data Acquisition &amp; Processing Theory Guide</i>, 223-60090O, Mar. 2024.',
      'Shimadzu Scientific Instruments. <i>i-Series Virtual Advisor</i>: Troubleshooting chromatogram problems; Troubleshooting hardware problems; Periodic maintenance (pump, autosampler). https://www.ssi.shimadzu.com/service-support/virtual-advisor/i-series/',
      'Shimadzu Scientific Instruments. <i>Liquid Chromatography Troubleshooting Guide</i>, SSI-12-24, 2023, pp. 14, 17, 22.',
      'Shimadzu Scientific Instruments. <i>Cannabis Lab Start-Up Guide</i>, pp. 4–5 (Cannabis Analyzer for Potency, High Throughput method).',
      'Shimadzu d.o.o. <i>0008090850 IQ, OQ, EQR</i> — LabSolutions DB qualification, 20.02.2025.',
      'Purely Plant. <i>QCWI 001 v01 — WI for handling and maintaining Shimadzu HPLC</i>, 06.03.2025; <i>QCLB 018</i> logbook.',
      'European Commission. <i>EudraLex Vol. 4, Part I, Chapter 6: Quality Control</i>, 2014 (in force 01.10.2014): 6.7, 6.15, 6.17, 6.35.',
      'European Commission. <i>EudraLex Vol. 4, Annex 11: Computerised Systems</i>, 2011: §7, §9, §10, §11, §12.',
      'European Commission. <i>EudraLex Vol. 4, Annex 15: Qualification and Validation</i>, 2015: §3.10–3.13, §4.1, Glossary.',
      'ICH. <i>Q9(R1) Quality Risk Management</i>, 2023.',
      'Council of Europe. <i>Ph. Eur. 2.2.46 Chromatographic separation techniques</i> (system suitability).',
    ]
    refs_html = ''.join(f'<li>{r}</li>' for r in refs)
    css = open(os.path.join(HERE, 'course.css')).read()
    doc = f'''<!doctype html><html><head><meta charset="utf-8"><title>Shimadzu HPLC Training Course</title><style>{css}</style></head><body>
<section class="cover">
 <div class="covertop">PURELY PLANT · QUALITY CONTROL DEPARTMENT</div>
 <h1>Shimadzu HPLC<br/>Cannabis Analyzer for Potency</h1>
 <div class="sub">Step-by-step training course: instrument operation, LabSolutions DB, data analysis, data integrity, maintenance and troubleshooting</div>
 <img class="coverimg" src="file://{image('GS_4_0')}"/>
 <table class="meta">
  <tr><td>Document</td><td>Training course — draft for QA review (code to be assigned by QA)</td></tr>
  <tr><td>Prepared by</td><td>Blagoj Nikolov, Head of Quality Control</td></tr>
  <tr><td>Date</td><td>30.10.2026</td></tr>
  <tr><td>Applies to</td><td>Shimadzu i-Series HPLC with PDA (Cannabis Analyzer for Potency), LabSolutions DB; qualification ref. 0008090850. Model / serial no. from the nameplate: ______________</td></tr>
  <tr><td>Based on</td><td>The five Shimadzu manuals supplied with the system, Shimadzu i-Series Virtual Advisor, QCWI 001 v01, EU GMP Ch. 6, Annex 11, Annex 15</td></tr>
 </table>
</section>
<section class="front">
 <h2>How to use this course</h2>
 <p>Twelve modules, in the order an analyst meets the instrument: from switching it on to reviewing, protecting and troubleshooting data. Each module starts with its objective. Each procedure is numbered and cites the page of the Shimadzu manual it comes from, so the trainee can read the original. The figures are the real LabSolutions screens, taken from those manuals, and photographs of our own instrument.</p>
 <p>Box types:
  <span class="tag gmpt">GMP</span> regulatory requirement ·
  <span class="tag labt">OUR LAB</span> our configuration and rules ·
  <span class="tag warnt">CAUTION</span> where errors happen ·
  <span class="tag tipt">TIP</span> good practice.</p>
 <p><b>Training method.</b> Read the module, then perform each numbered procedure on the instrument under supervision (in Postrun Analysis, on archived data, for Modules 7–10). Complete the assessment (pass mark 80 %) and the training record. Training on this course does not replace qualification of the instrument or validation of the method.</p>
 <h2>Contents</h2><ol class="toc">{toc}<li><span>Annex</span> Assessment, answer key, training record, references</li></ol>
 <div class="box warn"><div class="boxhead"><span class="tag">CAUTION</span>Scope and limits</div><div class="boxbody">The supplied manuals are the LabSolutions software manuals. The instrument's own hardware instruction manual (LC-2030/2050 i-Series) is not in our files; hardware maintenance here follows Shimadzu's public i-Series Virtual Advisor and must be checked against that manual when Shimadzu d.o.o. supplies it. Under QCWI 001 §6 repairs and maintenance beyond daily care are done by the manufacturer's authorised service.</div></div>
</section>
{''.join(body)}
<section class="module annex">
 <div class="modhead"><div class="modno">Annex A</div><h2>Assessment</h2><div class="goal">Answer all 20 questions without the course. Pass: 16 correct (80 %).</div></div>
 <ol class="quiz">{quiz}</ol>
</section>
<section class="module annex">
 <div class="modhead"><div class="modno">Annex B</div><h2>Answer key (trainer only)</h2></div>
 <ol class="key">{key}</ol>
</section>
<section class="module annex">
 <div class="modhead"><div class="modno">Annex C</div><h2>Training record</h2></div>
 <table class="record"><thead><tr><th>Module</th><th>Practical done on instrument (date)</th><th>Trainee</th><th>Trainer</th></tr></thead><tbody>
 {''.join(f'<tr><td>{m["no"]}. {html.escape(m["title"])}</td><td></td><td></td><td></td></tr>' for m in MODULES)}
 </tbody></table>
 <table class="record sign"><tr><td>Assessment score: ____ / 20</td><td>Result: ☐ Pass ☐ Repeat</td></tr>
 <tr><td>Trainee (name, signature, date)<br/><br/></td><td>Trainer (name, signature, date)<br/><br/></td></tr>
 <tr><td colspan="2">Approved — Head of QC (name, signature, date)<br/><br/></td></tr></table>
 <h2 style="margin-top:28px">References</h2><ol class="refs">{refs_html}</ol>
 <p class="small">The Shimadzu screen images are reproduced from the manuals supplied with our licensed system for internal training only (© Shimadzu Corporation; reproduction outside the company requires Shimadzu's permission).</p>
</section>
</body></html>'''
    html_path = os.path.join(HERE, 'course.html')
    open(html_path, 'w').write(doc)
    js = f'''const {{chromium}}=require('playwright');(async()=>{{const b=await chromium.launch();const p=await b.newPage();
await p.goto('file://{html_path}',{{waitUntil:'load'}});
await p.pdf({{path:'{out_pdf}',format:'A4',printBackground:true,displayHeaderFooter:true,
margin:{{top:'18mm',bottom:'16mm',left:'15mm',right:'15mm'}},
headerTemplate:'<div style="font-family:Inter,sans-serif;font-size:7px;color:#6b7280;width:100%;padding:0 15mm;display:flex;justify-content:space-between"><span>Purely Plant · QC · Shimadzu HPLC training course</span><span>Draft for QA review · 30.10.2026</span></div>',
footerTemplate:'<div style="font-family:Inter,sans-serif;font-size:7px;color:#6b7280;width:100%;padding:0 15mm;display:flex;justify-content:space-between"><span>Internal training use only</span><span>Page <span class="pageNumber"></span> / <span class="totalPages"></span></span></div>'}});
await b.close();}})();'''
    open(os.path.join(HERE, 'print.js'), 'w').write(js)
    subprocess.run(['node', os.path.join(HERE, 'print.js')], check=True)


if __name__ == '__main__':
    build(sys.argv[1])
