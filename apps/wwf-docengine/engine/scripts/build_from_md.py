#!/usr/bin/env python3
"""
build_from_md.py — render bilingual Markdown into a Purely Plant controlled .docx
USING THE pp-document-suite ENGINE, with the skill's INTELLIGENT table layout.

  doctype SOP  -> pp_format two-column (MK|EN, divider, native TOC); §7/§8/§9 nested full-width
                  tables sized by pp_report.fixed() (the layout brain).
  doctype ANNEX/FORM/CHECKLIST/LOG -> pp_format base-template shell (logo header + Page X of Y),
                  navy #2B547E section banners, and ALL tables built via pp_report:
                    - label|value forms   -> 2-col, label #F2F2F2, value entry; fixed() purpose-sizes
                    - data tables         -> navy header row, zebra rows, fixed() use-aware widths +
                                             repeating header on page breaks
                    - single-select lists -> status_grid() compact checkbox grid
                  All widths are decided by pp_report.fixed() (compact-centred summaries vs full-width
                  data; Name/Date/Signature entry columns purpose-sized; ordinal columns minimal).

Markdown convention: PP_UNIFIED_DOCX_GUIDE.md. Usage: python3 scripts/build_from_md.py <src.md> <out.docx>

Line grammar notes (review 19.10.2026):
  * A heading is '#'+ followed by text; a table/form row whose first cell is '#' ("# ||| Параметар~~Parameter")
    is a row, not a heading, and never ends the block.
  * A line, or a table/form row, that begins with a backslash is LITERAL: the backslash is dropped and the rest
    is never read as a heading, bullet or [[marker]]. The wizard writes it in front of a value that would
    otherwise be one ("# 3 Напомена", "- 20 °C", "[[x]]").
  * A two-cell form row is 'Label MK ||| Label EN' (an empty write-in) — except when the first cell is Cyrillic
    and the second holds no Latin letter ("Име ||| Петар", "Датум ||| 12.10.2026"): then the second cell is the
    VALUE and there is no English label.

Blocks added 04.11.2026 (from the HPLC method validation draft; Head of QC accepted all, with lighter colours):
  [[SIGN]] Role MK ||| Role EN        one line: a Name | Signature | Date | Time sign-off strip; [[SIGN:peer]] and
                                      [[SIGN:approver]] tint it as the second and third tier of an approval cascade.
  [[DECISION]] … [[/DECISION]]        one row per option: ☐ Option MK ||| Option EN ||| rule MK~~rule EN [||| tone]
                                      (tone pass|fail|caution|info, else read from the option's words); ☒ = chosen.
  [[EQ]] … [[/EQ]]                    a formula panel: formula lines, then an optional 'каде ||| where' line and
                                      'symbol ||| meaning MK ||| meaning EN' legend lines. A formula line written
                                      $ LaTeX $ is a native, editable Word equation (pp_math); anything else is typed text.
  Formulas anywhere (prose, bullets, cells, headings, legends): $x_i^2$ inline, $$ … $$ display, \\$ a dollar sign.
  A formula that cannot be converted stops the build (MathError); it is never printed as LaTeX text.
  [[CHECKLIST]] … [[/CHECKLIST]]      one item per line (MK ||| EN): # | ☐ item | Date | Initials | Note.
  Inline [[EX:value]] = example value (red, in brackets); [[FILL:hint]] = write-in (grey hint, dotted line).
  HEADERDATA "build: execution" prints every [[EX:…]] as an empty write-in and leaves the verdicts of those rows
  blank; "end_mark: no" drops the END OF DOCUMENT line.
"""
import sys, os, re
# Locate the engine modules (pp_format/pp_report/...). Inside the packaged skill they are siblings
# of this file; in the ACME_SOP repo layout they live under ../pp-document-suite/scripts. Try both.
_here = os.path.dirname(os.path.abspath(__file__))
for _cand in (_here, os.path.join(_here, "..", "pp-document-suite", "scripts")):
    if os.path.exists(os.path.join(_cand, "pp_format.py")):
        sys.path.insert(0, _cand); break
sys.path.insert(0, _here)
import pp_format as pf
import pp_report as pr
import pp_theme as T
from docx.enum.text import WD_ALIGN_PARAGRAPH

PAGE_W = pr.PAGE_W  # 18.46 cm text width (base-template 1.27 cm margins)
# '#'+, whitespace, then text that is not a cell separator: "# ||| Параметар~~Parameter" (a table row with an
# ordinal column headed '#') ended the table and printed as a heading (review 19.10.2026).
# A row whose first cell is '#' is a row, not a heading, whatever follows: '# ||| …', '# ~~ # | …', '# | …' (04.11.2026).
HEADING = re.compile(r'^(#+)\s+(?!\|\|\||~~|\|)(\S.*)')
# Any of these at the start of a line opens a block, and so ends a block whose [[/...]] is missing.
BLOCK_START = ('[[TABLE', '[[FORM', '[[BOX', '[[PAGEBREAK', '[[NEWPAGE', '[[SIGN', '[[DECISION', '[[EQ', '[[CHECKLIST')

def parse(md):
    hd={}
    # Line-anchored scan (ported from the DocEngine canon-2026-07 parser, 09.10.2026): the
    # terminator is a line that IS "-->" by itself, so a value containing a literal "-->"
    # (an informally written title) can never end the block early and leak the remaining
    # fields into the body. A single-line block falls back to the regex.
    all_lines=md.splitlines(); hd_start=hd_end=None
    for idx,ln in enumerate(all_lines):
        if ln.strip()=='<!--HEADERDATA':
            hd_start=idx; break
    if hd_start is not None:
        for idx in range(hd_start+1, len(all_lines)):
            if all_lines[idx].strip()=='-->':
                hd_end=idx; break
    if hd_start is not None and hd_end is not None:
        for ln in all_lines[hd_start+1:hd_end]:
            if ':' in ln:
                k,v=ln.split(':',1); hd[k.strip()]=v.strip()
        md="\n".join(all_lines[hd_end+1:])
    else:
        m=re.search(r'<!--HEADERDATA(.*?)-->', md, re.S)
        if m:
            for ln in m.group(1).strip().splitlines():
                if ':' in ln:
                    k,v=ln.split(':',1); hd[k.strip()]=v.strip()
            md=md[m.end():]
        elif hd_start is not None:
            # No '-->' at all: the header fields used to be printed as SOP body text under an empty title,
            # whatever doctype they named (review 14.10.2026). A controlled document never ships like that.
            raise ValueError("HEADERDATA block is not closed: add a line '-->' after its last field")
    blocks=[]; lines=md.splitlines(); i=0
    while i<len(lines):
        s=lines[i].strip()
        if not s: i+=1; continue
        if s.startswith('\\'):                            # literal line: plain paragraph, whatever it starts with
            mk,en=(s[1:].split('|||',1)+[''])[:2]
            blocks.append(('p', mk.strip(), en.strip())); i+=1; continue
        if s.startswith('[[PAGEBREAK]]') or s.startswith('[[NEWPAGE]]'):
            blocks.append(('pagebreak',)); i+=1; continue
        if s.startswith('[[BOX'):                       # marked space: [[BOX:<min height cm>]] caption / content [[/BOX]]
            mo=re.match(r'\[\[BOX(?::\s*([0-9.]+))?\]\]', s); h=float(mo.group(1)) if mo and mo.group(1) else 4.0
            i+=1; rows=[]
            while i<len(lines) and not lines[i].strip().startswith('[[/BOX'):
                if lines[i].strip(): rows.append([c.strip() for c in lines[i].split('|||')])
                i+=1
            blocks.append(('box', rows, h)); i+=1; continue
        if s.startswith('[[SIGN'):                      # one-line sign-off strip: [[SIGN(:tier)]] Role MK ||| Role EN
            mo=re.match(r'\[\[SIGN(?::\s*(\w+))?\]\]\s*(.*)', s)
            tier=(mo.group(1) or 'analyst').lower() if mo else 'analyst'
            mk,en=((mo.group(2) if mo else '').split('|||',1)+[''])[:2]
            blocks.append(('sign', tier, mk.strip(), en.strip())); i+=1; continue
        if s.startswith(('[[DECISION', '[[EQ', '[[CHECKLIST')):
            kind=re.match(r'\[\[(DECISION|EQ|CHECKLIST)', s).group(1).lower(); rows=[]
            i+=1
            while i<len(lines):
                t=lines[i].strip()
                if t.startswith('\\'): t=t[1:]
                elif t.startswith('[[/'): i+=1; break
                elif t.startswith(BLOCK_START) or HEADING.match(t): break
                if t: rows.append([c.strip() for c in t.split('|||')])
                i+=1
            blocks.append((kind, rows)); continue
        if s.startswith('[[TABLE') or s.startswith('[[FORM'):
            kind='form' if s.startswith('[[FORM') else 'table'; rows=[]
            mo=re.match(r'\[\[(?:FORM|TABLE):([^\]]+)\]\]', s); mode=mo.group(1).strip() if mo else None
            i+=1
            while i<len(lines):
                t=lines[i].strip(); closed=False
                if t.startswith('\\'): t=t[1:]                   # literal row (see the module docstring)
                elif t.startswith('[[/'): i+=1; break
                # Any block marker or heading ends a block whose [[/...]] is missing; [[PAGEBREAK]] and [[BOX]]
                # used to be swallowed as table rows printing their own markers (review 14.10.2026).
                elif t.startswith(BLOCK_START) or HEADING.match(t): break
                else:
                    # The closing marker written at the end of the last row ("… | | | [[/TABLE]]") closes the block;
                    # it printed as text in a delivered document (04.11.2026).
                    m=re.search(r'\s*\[\[/(?:TABLE|FORM)\]\]\s*$', t)
                    if m: t=t[:m.start()].strip(); closed=True
                # A row of pipes only is an empty entry row, whatever its pipe count: split on '|||' it printed
                # a stray '||' in a cell (QCT026, 20.10.2026).
                if t and re.fullmatch(r'[|\s]*', t): rows.append([''])
                elif t: rows.append([c.strip() for c in t.split('|||')])
                i+=1
                if closed: break
            if kind=='table':
                rows=pipe_rows(rows)
                # A cell that is only '_' is an empty write-in (the same mark a [[FORM]] value takes); it printed a literal
                # underscore in a delivered record (minutes of meeting, 06.11.2026).
                rows=[['' if c.strip()=='_' else c for c in r] for r in rows]
            blocks.append((kind, rows, mode)); continue
        hm=HEADING.match(s)
        if hm:
            # 'MK ||| EN' (the prose form) is split on '|||' first: split on the first '|' it printed '| || EN'.
            sep='|||' if '|||' in hm.group(2) else '|'
            lvl=len(hm.group(1)); mk,en=(hm.group(2).split(sep,1)+[''])[:2]; num=''
            nm=re.match(r'^([0-9]+(?:\.[0-9]+)*\.?)\s+(.*)', mk.strip())
            if nm: num=nm.group(1); mk=nm.group(2)
            blocks.append(('h', lvl, num, mk.strip(), en.strip())); i+=1; continue
        bm=re.match(r'^[-*]\s+(.*)', s)
        if bm:
            mk,en=(bm.group(1).split('|||',1)+[''])[:2]
            blocks.append(('bullet', mk.strip(), en.strip())); i+=1; continue
        mk,en=(s.split('|||',1)+[''])[:2]
        blocks.append(('p', mk.strip(), en.strip())); i+=1
    return hd, blocks

_CYR=re.compile(r'[Ѐ-ӿ]'); _LAT=re.compile(r'[A-Za-z]')
def pipe_rows(rows):
    """Tolerant reading of a table written with single pipes between cells (`a | b | c`, MK~~EN inside a cell) instead of
    `|||`: every row was ONE cell, so the document printed `~~`, `|`, a trail of empty `| | |` and the closing marker as
    text (Head of QC, 04.11.2026). The header row fixes the column count; a data row with more cells than the header
    wrote its first cell as a `MK | EN` pair (`Аналитичар 1 | Analyst 1`, `L1 | L1`), which is merged back into one
    cell; a short row is padded. Only a table whose rows all have no `|||` and whose header holds a ` | ` is read so."""
    if len(rows)<2 or any(len(r)>1 for r in rows): return rows
    split=lambda c: re.split(r'\s*\|\s*', c.strip())
    head=split(rows[0][0])
    if len(head)<2: return rows
    ncol=len(head); out=[head]
    for r in rows[1:]:
        t=split(r[0])
        while len(t)>ncol:
            for i in range(len(t)-1):
                a,b=t[i],t[i+1]
                if '~~' in a or '~~' in b or not a or not b: continue
                if T.same_in_both(a,b) or (_CYR.search(a) and not _CYR.search(b) and _LAT.search(b)):
                    t[i:i+2]=[a+'~~'+b]; break
            else:
                t[ncol-1:]=[' | '.join(x for x in t[ncol-1:] if x)]; break      # no pair to merge: the rest joins the last cell
        # A leading MK|EN pair followed only by empty cells ('1 | 1 | | | | | |', 'Mean | Mean | | | |') is one entry, not two
        # cells: the second half must not land in the first data column.
        if len(t)>=2 and not any(t[2:]) and '~~' not in t[0] and '~~' not in t[1] and t[0] and t[1] and (
                T.same_in_both(t[0],t[1]) or (_CYR.search(t[0]) and not _CYR.search(t[1]) and _LAT.search(t[1]))):
            t[0:2]=[t[0]+'~~'+t[1]]
        t+=['']*(ncol-len(t)); out.append(t)
    return out

def cs(raw):
    mk,en=(raw.split('~~',1)+[''])[:2]; return mk.strip(), en.strip()

def bil(mk,en):
    return (mk + (" | "+en if en else "")).strip()

# ---- single-select option list detection (-> status_grid) ----
OPT = re.compile(r'([☐☒])\s*([^☐☒]+?)\s*(?=[☐☒]|$)')
def as_options(rows):
    """If a FORM/TABLE block is really one 'select one' line of ☐ options, return the option list.
       An option written with ☒ instead of ☐ is the selected one (filled records and examples);
       it is returned as OPTIONS.selected."""
    flat=[c for r in rows for c in r if c.strip()]
    # Only a block that is NOTHING but options. A labelled field ("Статус на приемот ||| Receipt status ||| ☐ ...")
    # or a table with a header row used to qualify too, and everything before the first ☐ (the label, a
    # sibling field, the header) was discarded (review 14.10.2026: WHSOP_003_A01/A04/A05, QASOP_0XX_A04).
    if not flat or any(not c.lstrip().startswith(('☐', '☒')) for c in flat):
        return None
    joined=" ".join(flat)
    marks=joined.count('☐')+joined.count('☒')
    if marks>=2 and len(rows)<=2 and '~~' not in joined:
        found=[(m,o.strip()) for m,o in OPT.findall(joined) if o.strip()]
        if len(found)>=2:
            opts=_Opts(o for _,o in found)
            opts.selected=next((o for m,o in found if m=='☒'), None)
            return opts
    return None

class _Opts(list):
    selected=None

# =========================== ANNEX ===========================
def _bar(d, num, mk, en, level=1):
    """Section bar as a SHADED PARAGRAPH, not a one-row table: Word and LibreOffice both honour keep-with-next on a
       paragraph, so a bar is never stranded at the foot of a page. Since 04.11.2026 (Head of QC: lighter, not the
       dark navy strip) a level-1 bar is pale blue under a navy rule and a sub-bar a paler band with a navy edge;
       the Macedonian is bold navy and the English follows as a small grey italic caption, without a pipe."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    p=d.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.LEFT; pr.sp(p,0,0)
    pPr=p._p.get_or_add_pPr()
    bdr=OxmlElement('w:pBdr')
    if level<=1:
        edges=(('top','12','3',T.NAVY_HEX),('left','4','4',T.BAR_HEX),('bottom','4','3',T.GRID_HEX),('right','4','4',T.BAR_HEX))
    else:
        edges=(('top','4','2',T.SUBBAR_HEX),('left','18','4',T.NAVY_HEX),('bottom','4','2',T.SUBBAR_HEX),('right','4','4',T.SUBBAR_HEX))
    for e,sz,space,colr in edges:
        el=OxmlElement('w:'+e); el.set(qn('w:val'),'single'); el.set(qn('w:sz'),sz)
        el.set(qn('w:space'),space); el.set(qn('w:color'),colr); bdr.append(el)
    pPr.append(bdr)
    shd=OxmlElement('w:shd'); shd.set(qn('w:val'),'clear'); shd.set(qn('w:color'),'auto')
    shd.set(qn('w:fill'),T.BAR_HEX if level<=1 else T.SUBBAR_HEX)
    pPr.append(shd)
    p.paragraph_format.keep_with_next=True
    if en and T.same_in_both(mk, en): en=''              # the same in both languages (HPLC, 1,097) prints once
    mk=(num+" "+mk).strip(); sz=11 if level<=1 else 10
    if mk: pr.rin(p,mk,sz,pr.NAVY,bold=True)
    if en:
        if mk: pr.rin(p,"   ",8,pr.GREY)
        pr.rin(p,en,8,pr.GREY,ital=True)
    return p

def emit_banner(d, num, mk, en):
    _bar(d, num, mk, en, 1)

def emit_subbar(d, num, mk, en):
    _bar(d, num, mk, en, 2)

def _form_bulk(cell, lmk, len_, val):
    """Render a bulk-text field as a full-width stacked block: bold label heading, then the value
       as a justified paragraph spanning the whole cell."""
    pr.shade(cell, pr.LBL)
    p=cell.paragraphs[0]; p.text=''; p.alignment=WD_ALIGN_PARAGRAPH.LEFT; pr.sp(p,2,2)
    if len_ and T.same_in_both(lmk, len_): len_=''
    if lmk: pr.rin(p, lmk, 10, pr.BLACK, bold=True)
    if len_:
        if lmk: pr.rin(p, " | ", 8, pr.BLACK)
        pr.rin(p, len_, 8, pr.BLACK, ital=True)
    pv=cell.add_paragraph(); pv.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY; pr.sp(pv,1,2)
    vmk,ven=val.split(" | ",1) if " | " in val else (val,'')   # form values carry MK/EN as "MK | EN"
    if vmk.strip(): pr.rin(pv, vmk.strip(), 10, pr.BLACK)
    if ven.strip():
        if vmk.strip(): pr.rin(pv, "  |  ", 8, pr.BLACK)
        pr.rin(pv, ven.strip(), 8, pr.BLACK, ital=True)

def _lbl_cell(cell, lmk, len_):
    if len_ and T.same_in_both(lmk, len_): len_=''
    c=pr.cellfmt(cell, lmk, len_, sz=10, col=pr.BLACK, bold=True, fill=pr.LBL)
    c.paragraphs[0].alignment=WD_ALIGN_PARAGRAPH.LEFT

def emit_form(d, rows, mode=None):
    # single-select? -> status_grid
    opts=as_options(rows)
    if opts:
        pr.status_grid(d, opts, selected=opts.selected, ncols=min(2, len(opts))); return
    fields=[]
    for rd in rows:
        # A two-cell row 'Label MK~~Label EN ||| value' (a grammar DocEngine once taught its authors)
        # means the same field as the three-cell 'Label MK ||| Label EN ||| value'.
        if len(rd)==2 and '~~' in rd[0]: rd=[*cs(rd[0]), rd[1]]
        # 'Име ||| Петар': a Cyrillic label and a second cell with no Latin letter is a filled value, not an
        # English label (review 19.10.2026). 'Име ||| Name' and 'Датум ||| Date' stay label pairs.
        elif len(rd)==2 and re.search(r'[Ѐ-ӿ]', rd[0]) and not re.search(r'[A-Za-z]', rd[1]): rd=[rd[0], '', rd[1]]
        lmk=rd[0] if len(rd)>0 else ''; len_=rd[1] if len(rd)>1 else ''
        # Cells after the third are the value's other language (".. ||| Испорака ||| Delivery"), not dropped.
        vals=[x.strip() for x in rd[2:] if x.strip() and x.strip()!='_']
        if len(vals)==2 and T.same_in_both(vals[0], vals[1]): vals=vals[:1]   # the same in both languages: once
        val=" | ".join(vals)
        vlen=len(val.strip())
        kind='bulk' if vlen>110 else ('span' if vlen>20 else 'short')   # short = fits a half-page pair
        fields.append({'lmk':lmk,'en':len_,'val':val,'kind':kind})

    if mode!='grid':
        # DEFAULT one-field-per-row: compact label col (see notes above), bulk values span full width.
        t=d.add_table(rows=len(fields), cols=2); t.alignment=pr.WD_TABLE_ALIGNMENT.CENTER
        lw=2.0
        for f in fields:
            if f['kind']!='bulk': lw=max(lw, min(max(len(f['lmk']),len(f['en'])),34)*0.176+0.5)
        lw=min(lw, PAGE_W*0.45)
        for ri,f in enumerate(fields):
            if f['kind']=='bulk':
                _form_bulk(t.cell(ri,0).merge(t.cell(ri,1)), f['lmk'], f['en'], f['val'])
            else:
                _lbl_cell(t.cell(ri,0), f['lmk'], f['en'])
                pr.cellfmt(t.cell(ri,1), f['val'], None, sz=10, col=pr.BLACK)
        pr.fixed(t, weights=[lw, PAGE_W-lw], header_repeat=False); pr.borders(t); pr.keep_table(t, whole_max=5)   # a long form may break between rows
        return

    # GRID MODE: content-aware packing. Each field is measured on ITS OWN content — the label sized
    # to its own text, the value to what it holds (write-ins get a fixed minimum). Fields are then
    # packed greedily, as many per row as GENUINELY fit the page, and every column is sized to its own
    # content — no shared/global label or value width. Long values span; bulk values become a block.
    VMIN=2.6                                                   # minimum writable value width (cm)
    for f in fields:
        # Label sized to its OWN text: wide enough for the whole label (capped, may wrap at spaces),
        # but never below its longest single WORD — so a short label like "Датум" never breaks mid-word.
        toks=(f['lmk']+' '+f['en']).split()
        word=max((len(x) for x in toks), default=1); full=max(len(f['lmk']),len(f['en']))
        f['lw']=max(word*0.24+0.6, min(full*0.24+0.6, 5.8))
        vl=len(f['val'].strip())
        f['vw']=VMIN if vl==0 else max(vl*0.20+0.4, 1.4)       # value → its own text (write-in = VMIN)
        f['fw']=f['lw']+max(f['vw'],VMIN)+0.3                  # footprint if packed onto a shared row
        f['span']=(f['kind']!='bulk') and (f['vw']>4.6 or f['fw']>PAGE_W*0.62)  # too wide to pair

    plans=[]; cur=[]; curw=0.0                                 # greedy first-fit, order preserving
    def flush():
        nonlocal cur,curw
        if cur: plans.append(('pack',cur)); cur=[]; curw=0.0
    for f in fields:
        if f['kind']=='bulk': flush(); plans.append(('bulk',f)); continue
        if f['span']:         flush(); plans.append(('span',f)); continue
        if cur and curw+f['fw']>PAGE_W: flush()
        cur.append(f); curw+=f['fw']
    flush()

    made=[]                                                    # the form's row-tables, in order
    for pl in plans:
        if pl[0]=='bulk':
            t=d.add_table(rows=1, cols=1); t.alignment=pr.WD_TABLE_ALIGNMENT.CENTER
            _form_bulk(t.cell(0,0), pl[1]['lmk'], pl[1]['en'], pl[1]['val'])
            pr._apply_widths(t, [PAGE_W]); pr.keep_table(t); made.append(t)
        elif pl[0]=='span':
            f=pl[1]; t=d.add_table(rows=1, cols=2); t.alignment=pr.WD_TABLE_ALIGNMENT.CENTER
            _lbl_cell(t.cell(0,0), f['lmk'], f['en'])
            pr.cellfmt(t.cell(0,1), f['val'], None, sz=10, col=pr.BLACK)
            pr._apply_widths(t, [f['lw'], PAGE_W-f['lw']]); pr.keep_table(t); made.append(t)
        else:  # pack: N fields side by side; labels snug to content, values share the remainder
            fs=pl[1]; n=len(fs); t=d.add_table(rows=1, cols=2*n); t.alignment=pr.WD_TABLE_ALIGNMENT.CENTER
            slack=(PAGE_W-sum(f['lw'] for f in fs))/n           # each value = equal share of leftover
            widths=[]
            for j,f in enumerate(fs):
                _lbl_cell(t.cell(0,2*j), f['lmk'], f['en'])
                pr.cellfmt(t.cell(0,2*j+1), f['val'], None, sz=10, col=pr.BLACK)
                widths+=[f['lw'], max(slack, VMIN)]
            pr._apply_widths(t, widths); pr.keep_table(t); made.append(t)
    if len(made)<=5:                                           # a short form moves as one block:
        for t in made[:-1]:                                    # chain each row-table to the next
            for r in t.rows:
                for c in r.cells:
                    for par in c.paragraphs: par.paragraph_format.keep_with_next=True

def emit_box(d, rows, h_cm):
    """A marked, empty-or-filled space (e.g. for an example label): one dashed-bordered cell of at
       least h_cm height. The first row is the caption (MK ||| EN); further rows are content."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm
    t=d.add_table(rows=1, cols=1); t.alignment=pr.WD_TABLE_ALIGNMENT.CENTER
    c=t.cell(0,0)
    cap=rows[0] if rows else ["", ""]
    p=c.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER; pr.sp(p,2,4)
    pr.rin(p,"✎ "+(cap[0] if cap else ""),9,pr.NAVY,ital=True)
    if len(cap)>1 and cap[1]: pr.rin(p,"  |  ",8,pr.GREY); pr.rin(p,cap[1],8,pr.GREY,ital=True)
    for r in rows[1:]:
        q=c.add_paragraph(); q.alignment=WD_ALIGN_PARAGRAPH.LEFT; pr.sp(q,0,1)
        pr.rin(q,r[0],10,pr.BLACK, bold=False)
        if len(r)>1 and r[1]: pr.rin(q,"  |  ",8,pr.GREY); pr.rin(q,r[1],8,pr.GREY,ital=True)
    pr.fixed(t,[PAGE_W],header_repeat=False)
    tblPr=t._tbl.tblPr; b=OxmlElement('w:tblBorders')
    for e in ('top','left','bottom','right'):
        el=OxmlElement('w:'+e); el.set(qn('w:val'),'dashed'); el.set(qn('w:sz'),'8'); el.set(qn('w:space'),'0'); el.set(qn('w:color'),pr.BORDER); b.append(el)
    tblPr.append(b)
    trPr=t.rows[0]._tr.get_or_add_trPr()
    hh=OxmlElement('w:trHeight'); hh.set(qn('w:val'),str(int(h_cm*567))); hh.set(qn('w:hRule'),'atLeast'); trPr.append(hh)
    pr.keep_table(t)

def rpn_limits(mode):
    """[[TABLE:rpn=lo,hi]] sets the RPN bands; default below 50 low, 50–100 medium, above 100 high."""
    mo=re.search(r'rpn\s*=\s*([0-9.]+)\s*,\s*([0-9.]+)', mode or '')
    return (float(mo.group(1)), float(mo.group(2))) if mo else (50, 100)

def exec_rows(rows):
    """In an execution build a row that held example values keeps no verdict: the analyst writes it."""
    if T.MODE['build']!='execution': return rows
    out=[]
    for r in rows:
        if any(T.has_tokens(c) for c in r) and any('[[EX:' in c for c in r):
            r=[('[[FILL:]]' if pr.verdict_tone(T.plain(cs(c)[0])) else c) for c in r]
        out.append(r)
    return out

def emit_table(d, rows, mode=None):
    if not rows: return
    opts=as_options(rows)
    if opts:
        pr.status_grid(d, opts, selected=opts.selected, ncols=min(2, len(opts))); return
    rows=[rows[0]]+exec_rows(rows[1:])
    ncol=max(len(r) for r in rows)
    t=d.add_table(rows=len(rows), cols=ncol); t.alignment=pr.WD_TABLE_ALIGNMENT.CENTER
    for ri,rd in enumerate(rows):
        for ci in range(ncol):
            mk,en=cs(rd[ci]) if ci<len(rd) else ('','')
            if ri==0:
                pr.head_cell(t.cell(ri,ci), mk, en, sz=9)
            else:
                fill=pr.LBL if (ci==0 and mk) else ("F7FAFC" if ri%2==0 else None)
                pr.cellfmt(t.cell(ri,ci), mk, en, sz=9, col=pr.BLACK, fill=fill)
    pr.fixed(t, mode='full')   # annex forms: every data table spans the full width, like the bars
    pr.borders(t)
    pr.tint_table(t, rpn=rpn_limits(mode))
    pr.keep_table(t)

# ---- blocks added 04.11.2026 ----
def _shade_par(p, fill):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    shd=OxmlElement('w:shd'); shd.set(qn('w:val'),'clear'); shd.set(qn('w:color'),'auto'); shd.set(qn('w:fill'),fill)
    p._p.get_or_add_pPr().append(shd)

def _row_height(t, ri, cm):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    trPr=t.rows[ri]._tr.get_or_add_trPr()
    hh=OxmlElement('w:trHeight'); hh.set(qn('w:val'),str(int(cm*567))); hh.set(qn('w:hRule'),'atLeast'); trPr.append(hh)

def _label(cell, mk, en, hint=None, sz=9, fill=None, align=WD_ALIGN_PARAGRAPH.LEFT):
    if fill: pr.shade(cell, fill)
    p=cell.paragraphs[0]; p.text=''; p.alignment=align; pr.sp(p,1,0)
    if mk: pr.rin(p,mk,sz,pr.BLACK,bold=True)
    if en and not T.same_in_both(mk, en):
        if mk: pr.rin(p,"  ",sz,pr.BLACK)
        pr.rin(p,en,7,pr.GREY,ital=True)
    if hint:
        q=cell.add_paragraph(); q.alignment=align; pr.sp(q,0,1); pr.rin(q,hint,7,pr.GREY,ital=True)
    return cell

SIGN_FIELDS=(("Име и презиме","Full name",None),("Потпис","Signature",None),("Датум","Date","dd/mm/yyyy"),("Време","Time","hh:mm"))
def emit_sign(d, tier, mk, en):
    """A sign-off strip: the role as a lead-in, then Name | Signature | Date | Time over one empty writing row.
       The tier (analyst / peer / approver) tints the label row, so a cascade reads at a glance."""
    fill=T.TIER_HEX.get(tier, T.TIER_HEX['analyst'])
    if mk or en:
        p=d.add_paragraph(); pr.sp(p,4,2); p.paragraph_format.keep_with_next=True
        if mk: pr.rin(p,mk,10,pr.NAVY,bold=True)
        if en and not T.same_in_both(mk, en):
            if mk: pr.rin(p,"   ",8,pr.GREY)
            pr.rin(p,en,8,pr.GREY,ital=True)
    t=d.add_table(rows=2, cols=4); t.alignment=pr.WD_TABLE_ALIGNMENT.CENTER
    for j,(fm,fe,hint) in enumerate(SIGN_FIELDS):
        _label(t.cell(0,j), fm, fe, hint, sz=9, fill=fill)
        t.cell(1,j).paragraphs[0].text=''
    _row_height(t, 1, 0.9)
    w=PAGE_W; pr._apply_widths(t, [w*0.30, w*0.28, w*0.24, w*0.18]); pr.keep_table(t)
    for c in t.rows[0].cells:
        for par in c.paragraphs: par.paragraph_format.keep_with_next=True

TONES=('pass','fail','caution','info')
def emit_decision(d, rows):
    """One decision, its options side by side: ☐ option (MK, EN) over the rule that selects it, each in its colour
       (pass mint, fail rose, caution cream, info pale blue). A ☒ option is the chosen one."""
    rows=[r for r in rows if any(c.strip() for c in r)]
    if not rows: return
    t=d.add_table(rows=1, cols=len(rows)); t.alignment=pr.WD_TABLE_ALIGNMENT.CENTER
    fills={'pass':pr.GREENF,'fail':pr.REDF,'caution':pr.AMBERF,'info':T.BAR_HEX}
    for j,r in enumerate(rows):
        cells=list(r)
        tone=cells.pop().strip().lower() if len(cells)>1 and cells[-1].strip().lower() in TONES else None
        opt=cells[0] if cells else ''
        chosen=opt.lstrip().startswith('☒')
        mk=opt.lstrip().lstrip('☐☒').strip(); en=cells[1] if len(cells)>1 else ''
        if '~~' in mk and not en: mk,en=cs(mk)
        rule_mk,rule_en=cs(cells[2]) if len(cells)>2 else ('','')
        tone=tone or pr.verdict_tone(mk) or pr.verdict_tone(en) or ('pass','fail','caution')[min(j,2)]
        c=t.cell(0,j); pr.shade(c, fills[tone])
        try: c.vertical_alignment=pr.WD_ALIGN_VERTICAL.CENTER
        except Exception: pass
        p=c.paragraphs[0]; p.text=''; p.alignment=WD_ALIGN_PARAGRAPH.CENTER; pr.sp(p,3,0)
        pr.rin(p,('☒ ' if chosen else '☐ ')+mk,10,pr.BLACK,bold=True)
        if en and not T.same_in_both(mk, en):
            q=c.add_paragraph(); q.alignment=WD_ALIGN_PARAGRAPH.CENTER; pr.sp(q,0,0); pr.rin(q,en,8,pr.GREY,ital=True)
        if rule_mk or rule_en:
            q=c.add_paragraph(); q.alignment=WD_ALIGN_PARAGRAPH.CENTER; pr.sp(q,1,3)
            if rule_mk: pr.rin(q,rule_mk,7,pr.BLACK)
            if rule_en and rule_en!=rule_mk:
                if rule_mk: pr.rin(q,"  ",7,pr.GREY)
                pr.rin(q,rule_en,7,pr.GREY,ital=True)
    pr._apply_widths(t, [PAGE_W/len(rows)]*len(rows)); pr.keep_table(t)

WHERE=re.compile(r'^(каде|where)\b', re.I)
def emit_eq(d, rows):
    """A formula panel: the formulas centred in bold navy, then 'каде | where' and one line per symbol. Formulas are
       typed (Unicode ×, √, ², subscripts), so they print the same on every renderer and stay editable."""
    rows=[r for r in rows if any(c.strip() for c in r)]
    if not rows: return
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    t=d.add_table(rows=1, cols=1); t.alignment=pr.WD_TABLE_ALIGNMENT.CENTER
    c=t.cell(0,0); pr.shade(c, T.SUBBAR_HEX); first=True; legend=False
    for r in rows:
        if not legend and WHERE.match(r[0]):
            legend=True
            p=c.paragraphs[0] if first else c.add_paragraph(); first=False
            pr.sp(p,4,1); pr.rin(p,r[0].rstrip(':')+":",9,pr.GREY,ital=True)
            if len(r)>1 and r[1] and r[1]!=r[0]: pr.rin(p,"  "+r[1].rstrip(':')+":",8,pr.GREY,ital=True)
            continue
        p=c.paragraphs[0] if first else c.add_paragraph(); first=False
        if not legend:
            p.alignment=WD_ALIGN_PARAGRAPH.CENTER; pr.sp(p,3,3)
            whole=pr.PM.whole_formula(r[0])
            if whole:                                  # LaTeX: a native Word equation, display style, navy
                pr._math_or_text(p, whole[0], True, T.NAVY_HEX, True, 12)
            else:
                pr.rin(p,r[0],12,pr.NAVY,bold=True)
            if len(r)>1 and r[1] and r[1]!=r[0]:
                q=c.add_paragraph(); q.alignment=WD_ALIGN_PARAGRAPH.CENTER; pr.sp(q,0,3); pr.rin(q,r[1],8,pr.GREY,ital=True)
        else:
            p.alignment=WD_ALIGN_PARAGRAPH.LEFT; pr.sp(p,0,1); p.paragraph_format.left_indent=pr.Cm(0.6)
            if len(r)>=3:
                pr.rin(p,r[0],10,pr.NAVY,bold=True); pr.rin(p," = ",10,pr.BLACK); pr.rin(p,r[1],10,pr.BLACK)
                if r[2] and r[2]!=r[1]: pr.rin(p,"  "+r[2],8,pr.GREY,ital=True)
            else:
                pr.rin(p,r[0],10,pr.BLACK)
                if len(r)>1 and r[1] and r[1]!=r[0]: pr.rin(p,"  "+r[1],8,pr.GREY,ital=True)
    pr._apply_widths(t,[PAGE_W])
    tblPr=t._tbl.tblPr
    for old in tblPr.findall(qn('w:tblBorders')): tblPr.remove(old)
    b=OxmlElement('w:tblBorders')
    for e in ('top','left','bottom','right'):
        el=OxmlElement('w:'+e); el.set(qn('w:val'),'single'); el.set(qn('w:sz'),'8'); el.set(qn('w:space'),'0'); el.set(qn('w:color'),T.NAVY_HEX); b.append(el)
    tblPr.append(b); pr.keep_table(t)

CHECK_HEAD=(("#",""),("Ставка","Item"),("Датум","Date"),("Иниц.","Initials"),("Бел.","Note"))
def emit_checklist(d, rows):
    """A prerequisite checklist: # | ☐ item (MK, EN) | Date | Initials | Note, a writing row per item."""
    rows=[r for r in rows if any(c.strip() for c in r)]
    if not rows: return
    t=d.add_table(rows=1+len(rows), cols=5); t.alignment=pr.WD_TABLE_ALIGNMENT.CENTER
    for j,(mk,en) in enumerate(CHECK_HEAD): pr.head_cell(t.cell(0,j), mk, en or None, sz=9)
    for i,r in enumerate(rows,1):
        mk,en=(cs(r[0]) if '~~' in r[0] else (r[0], r[1] if len(r)>1 else ''))
        mk=mk.lstrip('☐☒ ').strip()
        pr.cellfmt(t.cell(i,0), str(i), None, sz=9, col=pr.BLACK, fill=pr.LBL)
        c=t.cell(i,1); p=c.paragraphs[0]; p.text=''; p.alignment=WD_ALIGN_PARAGRAPH.LEFT; pr.sp(p,2,2)
        pr.rin(p,"☐  "+mk,9,pr.BLACK)
        if en and not T.same_in_both(mk, en): pr.rin(p,"  "+en,7,pr.GREY,ital=True)
        for j in (2,3,4): t.cell(i,j).paragraphs[0].text=''
    w=PAGE_W; pr._apply_widths(t,[0.9, w-0.9-2.6-2.0-2.6, 2.6, 2.0, 2.6]); pr._repeat_header(t)
    pr.keep_table(t, whole_max=8)

def emit_key(d, src):
    """One line under the header naming the two value markups, printed only where the document uses them."""
    ex='[[EX:' in src and T.MODE['build']!='execution'; fill='[[FILL:' in src or ('[[EX:' in src and not ex)
    if not (ex or fill): return
    p=d.add_paragraph(); pr.sp(p,0,4); p.alignment=WD_ALIGN_PARAGRAPH.LEFT
    pr.rin(p,"Клуч  ",7,pr.GREY,bold=True); pr.rin(p,"Key:  ",7,pr.GREY,ital=True)
    if ex:
        pr.rin(p,"[[EX:…]]",7,pr.BLACK); pr.rin(p," пример вредност ",7,pr.GREY); pr.rin(p,"example value",7,pr.GREY,ital=True)
        if fill: pr.rin(p,"   ·   ",7,pr.GREY)
    if fill:
        pr.rin(p,"[[FILL:впиши]]",7,pr.BLACK); pr.rin(p," внеси вредност ",7,pr.GREY); pr.rin(p,"enter value",7,pr.GREY,ital=True)

def emit_end(d, hd):
    """— КРАЈ НА ДОКУМЕНТ — END OF DOCUMENT, chained to the block before it so it never stands alone on a page."""
    if (hd.get('end_mark') or '').strip().lower() in ('no','false','0'): return
    from docx.oxml.ns import qn
    body=d.element.body
    last=[e for e in body if e.tag in (qn('w:p'), qn('w:tbl'))]
    if last:
        e=last[-1]
        pars=(e.findall('.//'+qn('w:tr'))[-1].findall('.//'+qn('w:p')) if e.tag==qn('w:tbl') and e.findall('.//'+qn('w:tr')) else [e])
        from docx.text.paragraph import Paragraph
        for x in pars: Paragraph(x, d).paragraph_format.keep_with_next=True
    p=d.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; pr.sp(p,10,0)
    pr.rin(p,"— КРАЈ НА ДОКУМЕНТ —",10,pr.NAVY,bold=True); pr.rin(p,"   END OF DOCUMENT",8,pr.GREY,ital=True)

def emit_new(d, b):
    """Dispatch for the 04.11.2026 blocks (both the annex and the SOP path)."""
    if b[0]=='sign': emit_sign(d, b[1], b[2], b[3])
    elif b[0]=='decision': emit_decision(d, b[1])
    elif b[0]=='eq': emit_eq(d, b[1])
    elif b[0]=='checklist': emit_checklist(d, b[1])
NEW_BLOCKS=('sign','decision','eq','checklist')

WIDE_COLS = 10
BLOCKISH = ('form','table','box') + NEW_BLOCKS

def build_annex(hd, blocks, out):
    global PAGE_W
    # More than WIDE_COLS columns cannot be read on portrait A4 (about 1.2 cm a column at 15: words broke mid-syllable,
    # QCT026 20.10.2026), so such a form is laid out landscape whatever the header asked for.
    widest = max((max(len(r) for r in b[1]) for b in blocks if b[0] in ('table', 'form') and b[1]), default=0)
    land = hd.get('orient')=='landscape' or widest > WIDE_COLS
    # Fit tables/forms to the ACTUAL text width of the page: A4 portrait ≈ 18.46 cm, A4 landscape
    # ≈ 27.16 cm (both at the base-template 1.27 cm margins). The whole layout brain keys off this.
    PAGE_W = 27.16 if land else 18.46
    pr.PAGE_W = PAGE_W
    status=hd.get('status','draft')
    d=pf.new_annex(code=hd.get('code',''), version=hd.get('version','01'),
                   mk_title=hd.get('mk_title',''), en_title=hd.get('en_title',''),
                   orient='landscape' if land else 'portrait', status=status)
    # No title block in the body (Head of QC, 19.10.2026): the running header already carries the title, the code
    # and the version/status, so the code, title, "(code)" and DRAFT lines under it said it all twice.
    if hd.get('supersedes'):
        pr.note(d, "Заменува: "+hd['supersedes'], "Supersedes: "+hd['supersedes'])
    emit_key(d, hd.get('_src',''))
    TABLEISH=('h','form','table')
    prev=None
    for i,b in enumerate(blocks):
        # Vertical rhythm: a section bar gets a clear gap above it; any two table blocks in a row
        # get a small one (otherwise they fuse into one table); text before a table stays with it.
        if b[0]=='h' and prev not in (None,'pagebreak'):
            pf.spacer(d, 12 if b[1]==1 else 8)
        elif b[0] in BLOCKISH and prev in BLOCKISH:
            pf.spacer(d, 6)
        elif b[0] in BLOCKISH and prev in ('p','bullet'):
            pf.spacer(d, 6, keep=True)                 # lead-in text stays with its table
        elif b[0] in BLOCKISH and prev=='h':
            pf.spacer(d, 2, keep=True)                 # a bar stays with its table
        elif b[0] in ('p','bullet') and prev in BLOCKISH:
            pf.spacer(d, 4)
        prev=b[0]
        if b[0]=='h':
            (emit_banner if b[1]==1 else emit_subbar)(d, b[2], b[3], b[4])
        elif b[0]=='p':
            p=pr.body(d, b[1], b[2])
            if i+1<len(blocks) and blocks[i+1][0] in BLOCKISH:
                p.paragraph_format.keep_with_next=True
        elif b[0]=='bullet': pr.bullet(d, b[1], b[2])
        elif b[0]=='form': emit_form(d, b[1], mode=(b[2] if len(b)>2 else None))
        elif b[0]=='table': emit_table(d, b[1], (b[2] if len(b)>2 else None))
        elif b[0]=='box': emit_box(d, b[1], b[2])
        elif b[0] in NEW_BLOCKS: emit_new(d, b)
        elif b[0]=='pagebreak': d.add_page_break()
    emit_end(d, hd)
    PAGE_W = pr.PAGE_W = 18.46            # restore default for any subsequent build in-process
    pf.save(d, out)

# =========================== SOP ===========================
def _signatories(hd):
    """prepared_by / reviewed_by / approved_by from the HEADERDATA; None keeps the house default (the QC chain)."""
    keys = ("prepared_by", "reviewed_by", "approved_by")
    if not any(k in hd for k in keys):
        return None
    return tuple(hd.get(k, "—") or "—" for k in keys)

def build_sop(hd, blocks, out):
    status=hd.get('status','draft'); ver=hd.get('version','01')
    eff=hd.get('effective_date'); rev=hd.get('review_date')
    d=pf.new_sop(code=hd.get('code',''), version=ver,
                 mk_title=hd.get('mk_title',''), en_title=hd.get('en_title',''), status=status)
    # Title-page code line carries a controlled 'vNN' only once approved (see pf.header_version).
    pf.sop_titlepage(d, hd.get('code','')+" · "+pf.header_version(status, ver),
                     hd.get('mk_title',''), hd.get('en_title',''),
                     status=status, version=ver, effective_date=eff, review_date=rev,
                     signatories=_signatories(hd))
    pf.sop_toc(d)
    emit_key(d, hd.get('_src',''))
    t=None
    gap_after=False
    def ensure():
        nonlocal t, gap_after
        if t is None:
            if gap_after: pf.spacer(d, 6); gap_after=False   # air below a full-width table
            t=pf.sop_table(d)
        return t
    for i,b in enumerate(blocks):
        prev_heading = i>0 and blocks[i-1][0]=='h' and t is None
        if b[0]=='h' and i+1<len(blocks) and blocks[i+1][0] in ('table','form'):
            if t is not None: pf.sop_finalize(t); t=None      # heading directly above a table:
            pf.sop_heading_par(d, (b[2] or ''), b[3], b[4], level=b[1])   # keep it with that table
            gap_after=False
        elif b[0]=='h':
            pf.sop_section_row(ensure(), (b[2] or ''), b[3], b[4], level=b[1])
        elif b[0]=='p':
            pf.sop_body_row(ensure(), b[1], b[2])
        elif b[0]=='bullet':
            pf.sop_body_row(ensure(), "•  "+b[1], "•  "+b[2])
        elif b[0]=='pagebreak':
            # Printed nothing in an SOP until 14.10.2026 (the annex path had it); likewise [[BOX]] below.
            if t is not None: pf.sop_finalize(t); t=None
            d.add_page_break(); gap_after=False
        elif b[0]=='box':
            if t is not None: pf.sop_finalize(t); t=None
            pf.spacer(d, 6, keep=prev_heading); emit_box(d, b[1], b[2]); gap_after=True
        elif b[0] in NEW_BLOCKS:
            if t is not None: pf.sop_finalize(t); t=None
            pf.spacer(d, 6, keep=prev_heading); emit_new(d, b); gap_after=True
        elif b[0] in ('table','form'):
            if t is not None: pf.sop_finalize(t); t=None      # close two-col table; table goes full width
            rows=b[1]
            if not rows: continue
            pf.spacer(d, 6, keep=prev_heading)                 # air above; also stops the tables fusing
            gap_after=True
            if b[0]=='form':
                # A [[FORM]] in an SOP (a record template in §7) was drawn as a data table: its first field became
                # the navy header row and the '_' write-ins printed literally (review 19.10.2026). Same label | value
                # form as the annex path; the SOP page has the same 18.46 cm text width.
                emit_form(d, rows, mode=(b[2] if len(b)>2 else None)); continue
            headers=[cs(c) for c in rows[0]]
            ncol=len(headers)
            # A row longer than the header crashed the build (IndexError, no document); its extra cells now
            # join the last column so nothing is lost (review 14.10.2026).
            rows=[r if len(r)<=ncol else r[:ncol-1]+[" | ".join(x for x in r[ncol-1:] if x.strip())] for r in rows]
            data=[[cs(c) for c in r] for r in exec_rows(rows[1:])]
            bt=pf.sop_block_table(d, headers, data, [round(PAGE_W/ncol,2)]*ncol)
            pr.fixed(bt, mode='full')                          # full width, like the two-column body; repeat header
            pr.tint_table(bt, rpn=rpn_limits(b[2] if len(b)>2 else None))
    if t is not None: pf.sop_finalize(t)
    emit_end(d, hd)
    pf.save(d, out)

def main(src,out):
    md=open(src,encoding='utf-8').read()
    hd,blocks=parse(md)
    hd['_src']=md
    dt=hd.get('doctype','SOP').upper()
    # "build: execution" -> the copy that goes to the bench: example values become write-ins (pp_theme.MODE).
    T.MODE['build']='execution' if (hd.get('build') or '').strip().lower()=='execution' else 'simulation'
    try:
        (build_sop if dt=='SOP' else build_annex)(hd, blocks, out)
    finally:
        T.MODE['build']='simulation'
    print("WROTE", out, "("+dt+")")

if __name__=='__main__':
    main(sys.argv[1], sys.argv[2])
