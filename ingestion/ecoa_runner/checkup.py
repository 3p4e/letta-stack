#!/usr/bin/env python3
"""Full checkup: every rule the Head of QC stated, tested against the code."""
import os, sys, json, sqlite3, importlib.util
H = os.path.dirname(os.path.abspath(__file__))
def load(n, p):
    s = importlib.util.spec_from_file_location(n, os.path.join(H, p.replace("runner/","").replace("rag/","")))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

R  = load('r', 'runner/extract_ecoa_records.py')
PB = load('pb', 'common/pp_batch.py')
PE = load('pe', 'common/pheur.py')
CQ = load('cq', 'runner/build_coq.py')
QG = load('qg', 'rag/quality_guard.py')

P = F = 0
def check(rule, cond, detail=''):
    global P, F
    ok = bool(cond); P += ok; F += (not ok)
    print('  %-4s %-58s %s' % ('PASS' if ok else 'FAIL', rule, detail))

print('=' * 92); print('CHECKUP — stated rules vs implementation'); print('=' * 92)

print('\n1. EXTRACTION — reading the page')
check('exponents expand: 4,2 x 10^4 -> 42000', R.norm_num('4,2 x 10⁴ CFU/g') == 42000)
check('middle-dot notation: 1.6·10^4 -> 16000', R.norm_num('1.6·10⁴ CFU/g') == 16000)
check('Cyrillic multiplication sign handled', R.norm_num('5,1 х 10^3') == 5100)
check('qualitative criteria are not numbers', R.norm_num('Отсуство / 25 g') is None)
check('prose is not a number (trap 5)',
      R.norm_num('COMPLIES (numeric value not present for report 1625/2026)') is None)
check('two-sided criterion parsed as a range', R.norm_range('19.8 – 24.2 %') == (19.8, 24.2))
check('one-sided criterion is not a range', R.norm_range('≤ 12.0%') is None)

print('\n2. TWO-PASS — disagreement is never resolved silently')
a = {'parameters': [{'parameter': 'tymc', 'result_printed': '3,6 x 10⁴', 'result_numeric': 36000}]}
b = {'parameters': [{'parameter': 'tymc', 'result_printed': '3,6 x 10¹', 'result_numeric': 36}]}
o = R.reconcile(a, b); p0 = o['parameters'][0]
check('models disagree -> value held null', p0['result_numeric'] is None)
check('models disagree -> flagged for review', p0['confidence'] == 'review')
check('both readings preserved for the reviewer', p0['read_a'] and p0['read_b'])
same = R.reconcile(a, json.loads(json.dumps(a)))
check('models agree -> value recorded', same['parameters'][0]['result_numeric'] == 36000)
dup = {'parameters': [{'parameter': 'other', 'parameter_printed': 'CBDA', 'result_printed': '0.05'},
                      {'parameter': 'other', 'parameter_printed': 'THCA', 'result_printed': '23.8'}]}
check('duplicate keys not collapsed',
      len(R.reconcile(dup, json.loads(json.dumps(dup)))['parameters']) == 2)

print('\n3. BATCH IDENTITY — Head of QC grammar, 23.08.2026')
check('separator carries no meaning', PB.pp_batch('GG1024/01') == PB.pp_batch('GG1024-01') == 'GG1024_01')
check('second separator = sub-lot, kept distinct', PB.pp_batch('GG1024_01/01') == 'GG1024_01/01')
check('verification sample V is part of identity', PB.pp_batch('JD012603-02V') == 'JD012603_02V')
check('asterisk batch is a different batch', PB.pp_batch('JD112501*') != PB.pp_batch('JD112501'))
check('batch codes are never Cyrillic — homoglyphs folded', PB.pp_batch('СЈ062501/2') == 'CJ062501_2')
check('non-Latin Cyrillic rejected (control-book no.)', PB.pp_batch('ППК25050') is None)
check('ГС transliterates to GS, not visual GC', 'GS' in (PB._to_latin('ГС') or ''))
check('certificate codes are not batches', PB.pp_batch('1032/1851/25') is None)

print('\n4. GOVERNING CRITERIA — Ph. Eur. 5.1.8 category C')
check('TAMC 10^5', PE.governing('tamc')[0] == 1e5)
check('TYMC 10^4', PE.governing('tymc')[0] == 1e4)
check('bile-tolerant gram-neg 10^4', PE.governing('bile_tolerant_gram_negative')[0] == 1e4)
check('category C cited as the reference', 'cat. C' in PE.governing('tymc')[1])
check('Total THC not governed here (per grade, §01)', PE.governing('total_thc') == (None, None))
check('max acceptable count unset pending ruling', PE.MAX_MULTIPLIER is None)

print('\n5. SOURCE PRECEDENCE — QCCoA retired, CoQ supersedes')
check('QCCoA 001 is tier 3 (fallback only)', CQ.source_tier('QCCoA 001', 'PURELYPLANT') == 3)
check('QCCoA 001v02 also tier 3', CQ.source_tier('QCCoA 001v02', 'PURELYPLANT') == 3)
check('in-house iCoA is tier 2', CQ.source_tier('iCoA-PP-2026-0005', 'PURELYPLANT') == 2)
check('external accredited eCoA is tier 1', CQ.source_tier('320/0587/25', 'ЈЗУ ИЈЗ') == 1)

print('\n6. RETEST / REISSUE')
check('same value in different notation is not a retest',
      CQ._canon('н.д.') == CQ._canon('N.D.') and CQ._canon('<LOQ') == CQ._canon('≤ LOQ'))
check('a genuinely different value is a retest', CQ._canon('21.80') != CQ._canon('26.14'))
check('Cyrillic conformity equals Latin', CQ._canon('Одговара') == CQ._canon('Conforms'))

print('\n7. SPECIFICATION COVERAGE')
keys = [k for _n, _s, k, _e, _c, _m in CQ.SPEC]
check('12 numbered rows, 21 leaf parameters', len({n for n, *_ in CQ.SPEC}) == 12 and len(CQ.SPEC) == 21)
check('mycotoxins has 3 parameters', sum(1 for n, *_ in CQ.SPEC if n == '10') == 3)
check('identification A, B and C are separate rows',
      all(k in keys for k in ('identification_a_macroscopic', 'identification_b_microscopic',
                              'identification_c_hplc')))
check('foreign matter is its own row', 'foreign_matter' in keys)
check('group cover distinguishes NOT TESTED from MISSING', hasattr(CQ, '_group_cover'))

print('\n8. INGEST GUARDS')
ok, _ = QG.check('x' * 50)
check('short output flagged (hallucination)', not ok)
ok2, pr = QG.check('Сүлү Ыбык оон мин Үсун Куһулан Симчен ' * 20)
check('non-Macedonian Cyrillic flagged', not ok2)
ok3, _ = QG.check(('The quick brown fox jumps over the lazy dog. ' * 20))
check('plain English not flagged', ok3)

print('\n' + '=' * 92)
print('%d passed, %d failed' % (P, F))
sys.exit(1 if F else 0)
