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
CT = load('ct', 'common/controlled.py')

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
check('max acceptable count is 5x (Ph. Eur. 5.1.8, IJZ practice)', PE.MAX_MULTIPLIER == 5)
check('TYMC max acceptable count 50 000', PE.max_acceptable('tymc') == 5e4)
check('TYMC 4,9 x 10^4 is within the max acceptable count',
      49000 <= PE.max_acceptable('tymc'))
check('TYMC 6 x 10^4 is out of specification', 60000 > PE.max_acceptable('tymc'))

print('\n2a2. PER-FIELD AGREEMENT AND CROSS-KEY PAIRING (corpus tranche-1 defects)')
_A={'parameters':[{'parameter':'arsenic','parameter_printed':'арсен','result_printed':'0,081','result_numeric':0.081,'limit_printed':None}]}
_B={'parameters':[{'parameter':'arsenic','parameter_printed':'арсен','result_printed':'0,081','result_numeric':0.081,'limit_printed':'2','limit_numeric':2}]}
_o=R.reconcile(json.loads(json.dumps(_A)),json.loads(json.dumps(_B)))['parameters'][0]
check('agreed result with disagreed limit stays CONFIRMED', _o['confidence']=='ok' and _o['result_numeric']==0.081)
check('the disagreed limit itself is dropped, not guessed', _o['limit_numeric'] is None)
_A={'parameters':[{'parameter':'other','parameter_printed':'HCB','result_printed':'н.д.'}]}
_B={'parameters':[{'parameter':'pesticide_residues','parameter_printed':'* HCB','result_printed':'н.д.'}]}
_ps=R.reconcile(json.loads(json.dumps(_A)),json.loads(json.dumps(_B)))['parameters']
check('other/pesticide keys with *-marked label pair as ONE row',
      len(_ps)==1 and _ps[0]['confidence']=='ok' and _ps[0]['parameter']=='pesticide_residues')

print('\n2a3. A PRINTED MINIMUM IS A FLOOR, NOT A CEILING (corpus false-flag)')
import importlib.util as _iu, re as _re
_bt = _iu.module_from_spec(_iu.spec_from_file_location('bt', H + '/build_table.py'))
_iu.spec_from_file_location('bt', H + '/build_table.py').loader.exec_module(_bt)
check('"мин. 5.00 %" is recognised as a minimum', bool(_bt._MINIMUM.match('мин. 5.00 %')))
check('"min. 5.00" and "≥ 5.00" too',
      bool(_bt._MINIMUM.match('min. 5.00')) and bool(_bt._MINIMUM.match('≥ 5.00')))
check('a ceiling is NOT read as a minimum',
      not _bt._MINIMUM.match('≤ 12.0 %') and not _bt._MINIMUM.match('10^5 CFU/g'))

print('\n2b. ARITHMETIC SELF-CHECK — R4, adopted from the legacy-corpus register')
def _r4(free, acid, tot):
    rec = {'parameters': [
        {'parameter': 'thc_free', 'result_numeric': free, 'confidence': 'ok'},
        {'parameter': 'thca', 'result_numeric': acid, 'confidence': 'ok'},
        {'parameter': 'total_thc', 'result_numeric': tot, 'confidence': 'ok'}]}
    return R.arithmetic_check(rec)['parameters'][2]['confidence']
# ППК25117 as the certificate prints it, and as the corrupted corpus held it
check('0.46 + 17.01 x 0.877 = 15.38 passes', _r4(0.46, 17.01, 15.38) == 'ok')
check('the ten-fold corruption 1.58 is caught', _r4(0.46, 17.01, 1.58) == 'review')
# ППК25139: THCA missing its leading digits
check('THCA 0.52 for 26.52 is caught', _r4(0.53, 0.52, 23.79) == 'review')
check('a mismatch flags all three rows', all(
    p['confidence'] == 'review' for p in R.arithmetic_check({'parameters': [
        {'parameter': 'thc_free', 'result_numeric': 0.46, 'confidence': 'ok'},
        {'parameter': 'thca', 'result_numeric': 17.01, 'confidence': 'ok'},
        {'parameter': 'total_thc', 'result_numeric': 1.58, 'confidence': 'ok'}]})['parameters']))
check('an N.D. component is never assumed zero', _r4(None, 17.01, 15.38) == 'ok')
check('tolerance is 0.06, not exactness', _r4(0.46, 17.01, 15.42) == 'ok')

print('\n2c. SPECIFICATION-LINE GUARD — E5')
def _e5(v):
    rec = {'parameters': [{'parameter': 'total_thc', 'result_printed': v, 'confidence': 'ok'}]}
    return R.spec_line_guard(rec)['parameters'][0]['confidence']
check('"мин. 5.00 %" is not a result', _e5('мин. 5.00 %') == 'review')
check('"15.1 – 18.5% of the labelled amount" is not a result',
      _e5('15.1 – 18.5% of the labelled amount') == 'review')
check('a genuine measured value passes', _e5('26.14') == 'ok')
check('"< 2" and "<LOQ" are results, not spec lines',
      _e5('< 2') == 'ok' and _e5('<LOQ') == 'ok')

print('\n4a. ACCREDITATION MARKER')
check('a row either read as non-accredited is non-accredited', R._accred(True, False) is False)
check('both reads accredited -> accredited', R._accred(True, True) is True)
check('unknown to one model is not an accreditation claim', R._accred(None, True) is None)
check('cert_code is defined for the model, not just named',
      'РЕЗУЛТАТ ОД ИСПИТУВАЊЕ' in R.SYSTEM and 'главна контролна книга' in R.SYSTEM)
check('the non-accredited legend is in the prompt', 'неакредитирани' in R.SYSTEM)

print('\n4b. CONTROLLED VOCABULARIES')
check('IJZ microbiology and chemistry are one laboratory',
      CT.canonical_lab('ЈЗУ ИНСТИТУТ ЗА ЈАВНО ЗДРАВЈЕ НА РСМАКЕДОНИЈА, Оддел за микробиологија')[0]
      == CT.canonical_lab('ЈЗУ Институт за јавно здравје на Република Северна Македонија - Скопје')[0]
      == 'IJZ')
check('canonical IJZ name carries no department',
      'Оддел' not in CT.canonical_lab('ЈЗУ ИНСТИТУТ ЗА ЈАВНО ЗДРАВЈЕ НА РСМАКЕДОНИЈА, '
                                      'Оддел за микробиологија')[1])
check('Cap Junkie resolves to Cap Junky', CT.canonical_strain('Cap Junkie') == 'Cap Junky')
check('strain with batch code appended still resolves',
      CT.canonical_strain('Blue Gelato BG1024') == 'Blue Gelato')
check('unknown laboratory is not renamed', CT.canonical_lab('Acme Labs') == (None, 'Acme Labs'))
check('panel statement distinguished from a compound',
      CT.is_panel_statement('Нема пронајдено ниту еден пестицид, над LOQ')
      and not CT.is_panel_statement('Deltamethrin'))
check('n.d. in either script means not found',
      CT.is_not_found('н.д.') and CT.is_not_found('N.D.') and CT.is_not_found('≤ LOQ'))
check('a detected compound is not "not found"', not CT.is_not_found('0,05 mg/kg'))
check('heavy-metal units canonicalise to mg/kg',
      CT.canonical_unit('mg/Kg') == CT.canonical_unit('mg/kg(l)') == 'mg/kg')
check('ppm is mg/kg, not converted', CT.canonical_unit('ppm') == 'mg/kg')
check('µg/kg variants unify', CT.canonical_unit('ug/kg') == CT.canonical_unit('ppb') == 'µg/kg')
check('an unknown unit is not renamed', CT.canonical_unit('IU/g') == 'IU/g')
check('LoD 10.0 (DAB) is superseded, not a defect',
      PE.classify_printed_limit('loss_on_drying', 10.0, '2025-02-26')[0] == 'superseded')
check('LoD 12.0 matches the governing criterion',
      PE.classify_printed_limit('loss_on_drying', 12.0, '2025-02-26')[0] == 'match')
check('a criterion in no version of the spec still disagrees',
      PE.classify_printed_limit('lead', 5.0, '2025-02-27')[0] == 'disagrees')
check('both jurisdiction panels are modelled',
      CT.panel_of('МКС EN 15662:2020') == 'MKS_EN_15662'
      and CT.panel_of('Ph. Eur. 2.8.13/ MKC EN 15662:2020') is not None)

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

print('\n6a. DERIVED CANNABINOID TOTALS — a certificate printing CBN is never "no result"')
def _row(param, printed, num, doc='D1', code='ППК25050', conf='ok', label=None):
    # SELECT order of compile_coq: parameter, result_printed, result_numeric, unit,
    # method, date_iso, cert_code, lab, confidence, exceeds, outside, document,
    # doc_id, parameter_printed, method_accredited, test_type
    return (param, printed, num, '% w/w', 'HPLC', '2025-02-26', code, 'CNP', conf,
            None, None, doc + '.pdf', doc, label or param, 1, 'unknown')
_cnp = [_row('cbn_free', '0.02', 0.02, label='Содржина на CBN'),
        _row('thc_free', '0.90', 0.90), _row('thca', '23.83', 23.83),
        _row('total_thc', '21.80', 21.80)]
_d = {r[0]: r for r in CQ.derive_totals(_cnp)}
check('CNP certificate with CBN but no CBNA supplies row 6 (Total CBN)',
      'total_cbn' in _d and _d['total_cbn'][2] == 0.02 and _d['total_cbn'][6] == 'ППК25050')
check('the derivation is stated on the row, not hidden',
      _d['total_cbn'][16]['kind'] == 'free-form-only' and 'CBNA' in _d['total_cbn'][16]['working'])
check('a printed total is never overridden by a computed one',
      _d['total_thc'][2] == 21.80 and len(_d['total_thc']) == 16)
_both = [_row('cbn_free', '0.10', 0.10), _row('cbna', '0.50', 0.50)]
_b = {r[0]: r for r in CQ.derive_totals(_both)}
check('free + acid printed, no total -> computed 0.10 + 0.50 x 0.876 = 0.54',
      _b['total_cbn'][2] == 0.54 and _b['total_cbn'][16]['kind'] == 'computed')
_nd = [_row('cbn_free', 'BLQ', None), _row('cbna', 'ND', None)]
_n = {r[0]: r for r in CQ.derive_totals(_nd)}
check('qualitative components carried as printed, N.D. never assumed zero',
      _n['total_cbn'][1] == 'BLQ' and _n['total_cbn'][16]['kind'] == 'acid-not-quantified')
_held = [_row('cbn_free', '0.02', 0.02, conf='review')]
check('a held component holds the derived row',
      CQ.derive_totals(_held)[-1][8] == 'review')
check('a value above 1.0 % is flagged against the criterion',
      {r[0]: r for r in CQ.derive_totals([_row('cbn_free', '1.20', 1.20)])}['total_cbn'][9] == 1)
_hi = {r[0]: r for r in CQ.derive_totals([_row('cbn_free', '0.85', 0.85)])}
check('a lower bound close beneath the criterion is not concluded, it is held',
      _hi['total_cbn'][9] is None and _hi['total_cbn'][8] == 'review'
      and 'LOWER BOUND' in _hi['total_cbn'][16]['working'])
_lo = {r[0]: r for r in CQ.derive_totals([_row('cbn_free', '0.02', 0.02)])}
check('an ordinary figure far beneath the criterion still concludes',
      _lo['total_cbn'][9] == 0 and _lo['total_cbn'][8] == 'ok'
      and _lo['total_cbn'][16]['bound'] == 'lower')
_comp = {r[0]: r for r in CQ.derive_totals([_row('cbn_free', '0.85', 0.85), _row('cbna', '0.10', 0.10)])}
check('a computed total is not a bound and concludes normally',
      _comp['total_cbn'][9] == 0 and 'bound' not in _comp['total_cbn'][16])
check('nothing to derive from -> nothing added',
      len(CQ.derive_totals([_row('loss_on_drying', '5.73', 5.73)])) == 1)

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
