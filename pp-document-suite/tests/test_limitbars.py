import os, sys, subprocess, tempfile, docx
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.join(HERE, '..', 'scripts'); sys.path.insert(0, S)
import pp_limitbars as lb

def test_parse_value():
    assert lb.parse_value('2.7 × 10⁴')[1] == 27000
    assert lb.parse_value('< 10')[1] == 10
    assert lb.parse_value('10³–10⁴')[1] == 10000
    assert lb.parse_value('> 10 000 MPN/g = 100000')[1] == 100000
    assert lb.parse_value('-')[2] == 'nr'
    assert lb.parse_value('Absent')[2] == 'abs'
    assert lb.parse_value('Detected in 1 g')[2] == 'det'

def test_colour():
    assert lb.colour(lb.fraction(10, 1e4, 'log'), False, .75) == lb.GREEN
    assert lb.colour(lb.fraction(1e4, 1e4, 'log'), False, .75) == lb.AMBER
    assert lb.colour(1, True, .75) == lb.RED

MD = """<!--HEADERDATA
mk_title: Тест
en_title: Test
code: PP-QC-RPT-XXX/26
version: 01
doctype: ANNEX
{feat}-->
# 1. РЕЗУЛТАТИ | RESULTS
[[LIMITS]]
@col TAMC ~~ ≤ 10⁵ | 100000 | log
@col E. coli ~~ absent | absent | qual
@group P0 ~~ test
01.01.2026 ~~ IPH 1 ||| 2 × 10³ ||| Absent
@ext 02.01.2026 ~~ Ext ||| - ||| Detected
[[/LIMITS]]
"""
def build(feat=''):
    d = tempfile.mkdtemp(); src = os.path.join(d, 'a.md'); out = os.path.join(d, 'a.docx')
    open(src, 'w').write(MD.format(feat=feat))
    subprocess.run([sys.executable, os.path.join(S, 'build_from_md.py'), src, out], check=True, capture_output=True)
    return docx.Document(out)

def nested(doc): return sum(len(c.tables) for t in doc.tables for r in t.rows for c in r.cells)

def test_bars_on_and_off():
    assert nested(build()) >= 3
    assert nested(build('features: limit_bars=off\n')) == 0
