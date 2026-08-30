import os, json, urllib.request

B = os.environ['RAGFLOW_API_SERVER'].rstrip('/'); K = os.environ['RAGFLOW_API_KEY']
AID = 'c83609aea3fd11f1858cf58865604f65'
VLM = 'gpt-4.1@openai-vlm@OpenAI'
CHAT = 'kimi-k2.6@MOONSHOT_API@Moonshot'
FAST = 'moonshot-v1-128k@MOONSHOT_API@Moonshot'
HERE = os.path.dirname(os.path.abspath(__file__))

def req(path, data=None, method='GET'):
    r = urllib.request.Request(B + path, data=json.dumps(data).encode() if data is not None else None,
        method=method, headers={'Authorization': 'Bearer ' + K, 'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(r, timeout=180))

SPEC = """SPECIFICATION REFERENCE - Purely Plant GmbH, Dry Cannabis Flower (Cannabis flos,
Ph. Eur. 3028). Section 02 of the product specification is IDENTICAL across all grades;
only the Total THC target band changes by grade (Section 01 of the spec, not the certificate).

USE THIS TABLE FOR LABEL RECOGNITION ONLY. It tells you which printed label - in English,
in Macedonian Cyrillic, or abbreviated - corresponds to which canonical parameter key, and
which method strings to expect. The limits below are the SPECIFICATION's limits.
NEVER emit a limit from this table. limit_printed and limit_numeric come ONLY from what is
printed on the certificate row in front of you. A certificate may print a TIGHTER limit than
the specification (this happens), and that printed limit is the one that governs. If no limit
is printed on the row, both limit fields are null - never fall back to this table, never fall
back to Ph. Eur. from memory.

key | English label | Macedonian label | expected method | spec limit (REFERENCE ONLY)
identification_a_macroscopic | Identification A, Appearance, Macroscopic | Идентиф. A, Изглед, Макроскопски | Ph. Eur. mon. 3028 | Conforms to monograph / Соодветствува со монографијата
identification_b_microscopic | Identification B, Microscopic | Идентиф. Б, Микроскопски | Ph. Eur. 2.8.23 | Conforms to monograph
identification_c_hplc | Identification C, HPLC/HPTLC | Идентиф. Ц, HPLC/HPTLC | Ph. Eur. 2.2.29 (3028) | Conforms to monograph
total_thc | Assay - Total delta-9-THC | Анализа - вкупен Δ⁹-THC | Ph. Eur. 2.2.29 (HPLC) | per grade, see Section 01
total_cbd | Assay - Total CBD | Анализа - вкупен CBD | Ph. Eur. 2.2.29 (HPLC), CBD + CBDA x 0.877 | <= 1.0 % w/w
total_cbn | Total CBN | Вкупен CBN | Ph. Eur. 2.2.29 (HPLC), CBN + CBNA x 0.876 | <= 1.0 % w/w
foreign_matter | Foreign Matter | Страни материи | Ph. Eur. 2.8.2 / in-house, интерна | <= 2.0 % per 25-50 g; < 1 cm leaves (листови); no seeds (без семки)
loss_on_drying | Loss on Drying | Губиток при сушење | Ph. Eur. 2.2.32 (3028), 40 C, 24 h, 15-25 mbar | <= 12.0 %
tamc | TAMC, Total aerobic microbial count | Вкупен аеробен микробен број, ТАМС | Ph. Eur. 2.6.12 cat. C | <= 10^5 CFU/g
tymc | TYMC, Total yeasts and moulds | Вкупен број квасци/мувли, ТУМС/ТYMC | Ph. Eur. 2.6.12 cat. C | <= 10^4 CFU/g
bile_tolerant_gram_negative | Bile-tolerant gram-negative | Жолчно-толерантни грам-нег. | Ph. Eur. 2.6.31 cat. C | <= 10^4 CFU/g
salmonella | Salmonella | Салмонела | Ph. Eur. 2.6.31 cat. C | Absence / Отсуство in 25 g
escherichia_coli | Escherichia coli | Ешерихија коли | Ph. Eur. 2.6.13 cat. C | Absence / Отсуство in 1 g
pseudomonas_aeruginosa | Pseudomonas aeruginosa (upon request) | По барање | Ph. Eur. 2.6.13 cat. C | Absence in 1 g
staphylococcus_aureus | Staphylococcus aureus (upon request) | По барање | Ph. Eur. 2.6.13 cat. C | Absence in 1 g
aflatoxin_b1 | Aflatoxin B1 | Афлатоксин B1 | Ph. Eur. 2.8.18 (HPLC-FLD) | <= 2 ug/kg
aflatoxins_total | Aflatoxins sum (B1+B2+G1+G2) | Афлатоксини ∑ | Ph. Eur. 2.8.18 (HPLC-FLD) | <= 4 ug/kg
ochratoxin_a | Ochratoxin A | Охратоксин A | Ph. Eur. 2.8.22 (HPLC-FLD) | <= 20 ug/kg
lead | Lead (Pb) | Олово (Pb) | Ph. Eur. 2.4.27 (ICP-MS) | <= 0.5 mg/kg
cadmium | Cadmium (Cd) | Кадмиум (Cd) | Ph. Eur. 2.4.27 (ICP-MS) | <= 0.3 mg/kg
arsenic | Arsenic (As) | Арсен (As) | Ph. Eur. 2.4.27 (ICP-MS) | <= 0.2 mg/kg
mercury | Mercury (Hg) | Жива (Hg) | Ph. Eur. 2.4.27 (ICP-MS) | <= 0.1 mg/kg
pesticide_residues | Pesticide Residues, Ph. Eur. panel | Остатоци од пестициди, Ph. Eur. панел | Ph. Eur. 2.8.13 (LC-MS/MS) | <= LOQ per Ph. Eur. 2.8.13
pesticide_residues_cumcs | Pesticide Residues, CUMCS Equivalency panel (upon request) | По барање | Ph. Eur. 2.8.13 (LC-MS/MS), CUMCS Equivalency | <= LOQ per CUMCS Equivalency

IDENTIFICATION A / B / C - COLLECTIVE COVERAGE
Identification A (macroscopic), B (microscopic) and C (HPLC/HPTLC) are three separate
specification parameters, but laboratories do not always report them as three rows.

- Some certificates (CNP among them) report all three explicitly, one row each. Transcribe
  each row on its own and set coverage to "explicit".
- Some certificates cover all three with ONE method statement. Farmahem / Pharmachem (FHM)
  certificates typically print a method such as "Identification and Qualitative and
  Quantitative Determination of Cannabinoids" (or its Macedonian equivalent). A statement of
  that kind satisfies Identification A, B and C together. In that case emit all three keys,
  give each the SAME printed result and the SAME printed method verbatim, and set coverage
  to "collective" with covered_by holding the method text exactly as printed.
- Some certificates do not address identification at all. Then emit nothing for these three
  keys. An absent test is not a passing test. Never invent a row to complete the set.

coverage exists so a reviewer can see at a glance which identification results were printed
as such and which were derived from one collective method statement. Never set coverage to
"explicit" for a row you derived. For every parameter other than these three, coverage is
always "explicit".

DOCUMENT LANGUAGE AND TYPE
The document is a laboratory certificate that may be written in Macedonian Cyrillic, in
English, or bilingually with the two side by side or stacked in one cell. It may be an
eCoA, an iCoA, a Certificate of Quality (CoQ), a Report of Analysis, or an in-house QC
record. Read whichever language is printed; when both are present they say the same thing -
transcribe the value once and use the canonical key from the table above.

READING SUPERSCRIPT EXPONENTS
Microbiological counts are printed with a superscript exponent: 4,2 x 10^4 may appear as
"4,2 x 10" with a raised 4, and the multiplication sign may be Cyrillic х or Latin x.
A misread exponent is a factor of ten and turns a failing batch into a passing one. Read the
raised digit deliberately. If it is not legible with certainty, set result_numeric to null and
exponent_uncertain to true. Never guess. Never default to 3."""

PARAMS = """PARAMETER VOCABULARY - map every printed row onto exactly one of these keys.
identification_a_macroscopic | identification_b_microscopic | identification_c_hplc
total_thc | total_cbd | total_cbn | foreign_matter | loss_on_drying
tamc | tymc | bile_tolerant_gram_negative | salmonella | escherichia_coli
pseudomonas_aeruginosa | staphylococcus_aureus
aflatoxin_b1 | aflatoxins_total | ochratoxin_a
lead | cadmium | arsenic | mercury | pesticide_residues
Use "other" only when a printed row matches none of the above; then put the printed
label verbatim in parameter_printed."""

META = f"""You transcribe a pharmaceutical Certificate of Analysis into JSON.
This is a GMP record. A wrong number here becomes a wrong batch release decision.

Output ONLY a valid JSON object. No prose, no markdown fence, no commentary.

ABSOLUTE RULES
1. Transcribe only what is printed. Never infer, never estimate, never complete a pattern.
2. Never carry a value from one parameter to another. Each row stands alone.
3. Read the EXPONENT with care. Microbiological counts are written as
   "1,2 x 10^4", "4,2 x 10^4" (the multiplication sign may be Cyrillic x), "1.2E4".
   The exponent is often a superscript and is the difference between a pass and a
   failure. If the exponent is not legible with certainty, set result_numeric to null
   and exponent_uncertain to true. Never guess an exponent. Never default to 3.
4. Capture the acceptance limit PRINTED ON THE SAME ROW as the result. Never copy a
   limit from a column header, another row, or your own knowledge of Ph. Eur.
5. Preserve qualifiers verbatim: "N.D.", "BLQ", "<LOQ", "<2", "Conforms",
   "Odgovara", "Otsustvo", "Absence", and their Cyrillic originals.
6. Do not convert units. Do not round. Do not normalise decimal separators.
   Record the number exactly as printed in result_printed, and the same value as a
   plain number in result_numeric (decimal point, exponent expanded) when it is a
   measurement. If it is not a measurement, result_numeric is null.
7. If a field is not printed, output null. Never guess.
8. Read test_type and the sample description from the certificate itself, never from a
   filename. Distinguish a release test from a stability timepoint and from a retest:
   a stability result over limit is data, a release result over limit is a deviation.
9. Cyrillic and Latin letters are mixed. TAMC and TYMC appear in both scripts and are
   the same parameters. Batch codes may use Cyrillic K where Latin K is meant. Record
   the batch exactly as printed in batch_printed and the Latin-folded form in
   batch_canonical.

{PARAMS}

{SPEC}

SCHEMA
{{
  "batch_printed": string|null,
  "batch_canonical": string|null,
  "p_number": string|null,
  "strain": string|null,
  "cert_code": string|null,
  "date_of_issue": string|null,
  "date_of_sampling": string|null,
  "lab": string|null,
  "test_type": "release"|"retest"|"stability"|"in_process"|"unknown",
  "overall_conclusion": string|null,
  "parameters": [
    {{"parameter": string, "parameter_printed": string,
      "result_printed": string|null, "result_numeric": number|null,
      "unit": string|null, "operator": "="|"<"|"<="|">"|">="|null,
      "limit_printed": string|null, "limit_numeric": number|null,
      "method": string|null, "exponent_uncertain": boolean,
      "coverage": "explicit"|"collective", "covered_by": string|null}}
  ]
}}
Emit one object for the certificate content in this chunk. If the chunk contains no
certificate data, emit {{"parameters": []}} with all other fields null."""

Q = """Write the questions this chunk can answer, one per line, no numbering, no preamble,
no commentary. Substitute the real values printed in the chunk - never leave a placeholder,
and never write a question whose answer is not in this chunk.

Work through these five, in this order, skipping any the chunk cannot answer:
1. What is the tested sample ID number and/or batch number?
2. What is the strain name of the tested batch?
3. What is the certificate document code and its date of issue?
4. What parameters are tested in this certificate <doc code, date of issue> for batch <batch number>?
5. What are the analysis results for the tested parameters in this certificate for batch <batch number>?

Write each question twice: once in English, once in Macedonian. Put the literal batch code,
P-number and certificate code into the question text exactly as printed, and where the batch
code uses Cyrillic letters also write a variant using the Latin-folded form, so both spellings
match at retrieval.

Output only the question lines."""

KW = """Output one line: retrieval keywords separated by commas. No preamble, no explanation,
no labels, and never repeat any wording from these instructions.

Take the keywords only from the certificate text you are given. Include, where present:
the batch code in every spelling that appears, the Latin-folded form of that batch code, the
P-number, the strain name, the certificate/laboratory number, the issuing laboratory name, and
the printed name of every analytical parameter, in both English and Macedonian.

If the text is unreadable or contains none of these, output nothing at all."""

PDF = {'parse_method': VLM, 'output_format': 'json', 'lang': 'Bulgarian',
       'remove_header_footer': False, 'remove_toc': False,
       'enable_multi_column': False, 'flatten_media_to_text': False,
       'vlm': {'llm_id': VLM}}
EXTRACTORS = {'Extractor:eCoAMetadata': ('metadata', META, CHAT),
              'Extractor:eCoAQuestions': ('questions', Q, FAST),
              'Extractor:eCoAKeywords': ('keywords', KW, FAST)}
CHUNKER = {'chunk_token_size': 2048, 'overlapped_percent': 0,
           'table_context_size': 1, 'image_context_size': 1}
TOKENIZER = {'fields': ['text', 'metadata', 'questions', 'keywords'],
             'search_method': ['embedding', 'full_text'], 'filename_embd_weight': 0.3}

def patch_setups_dict(s):
    s['pdf'].update(PDF)
    s['image'].update({'parse_method': VLM, 'output_format': 'json', 'lang': 'Bulgarian'})
    for kk in ('doc', 'docx', 'markdown', 'spreadsheet'):
        if kk in s:
            s[kk]['vlm'] = {'llm_id': VLM}
            s[kk].setdefault('lang', 'Bulgarian')
            if 'flatten_media_to_text' in s[kk]: s[kk]['flatten_media_to_text'] = False
    if 'spreadsheet' in s: s['spreadsheet']['parse_method'] = 'DeepDOC'

def patch_setups_list(lst):
    for e in lst:
        ff = e.get('fileFormat')
        if ff == 'pdf':
            e.update(PDF)
        elif ff == 'image':
            e.update({'parse_method': VLM, 'output_format': 'json', 'lang': 'Bulgarian'})
        else:
            e['vlm'] = {'llm_id': VLM}
            e.setdefault('lang', 'Bulgarian')
            if 'flatten_media_to_text' in e: e['flatten_media_to_text'] = False
            if ff == 'spreadsheet': e['parse_method'] = 'DeepDOC'

d = req('/api/v1/agents/' + AID)['data']
json.dump(d, open(HERE + '/agent_before_full.json', 'w'), ensure_ascii=False, indent=1)
dsl = d['dsl']

# ---------- 1. components (execution) ----------
C = dsl['components']
patch_setups_dict(C['Parser:eCoAParse']['obj']['params']['setups'])
C['TokenChunker:eCoACert']['obj']['params'].update(CHUNKER)
for node, (field, sysmsg, mdl) in EXTRACTORS.items():
    p = C[node]['obj']['params']
    p.update({'llm_id': mdl, 'temperature': 0, 'field_name': field, 'sys_prompt': sysmsg,
              'prompts': [{'role': 'user',
                           'content': 'Certificate content:\n{TokenChunker:eCoACert@chunks}'}],
              'max_tokens': 8192, 'maxTokensEnabled': True,
              'frequency_penalty': 0, 'frequencyPenaltyEnabled': False,
              'presence_penalty': 0, 'presencePenaltyEnabled': False,
              'top_p': 1, 'topPEnabled': False})
C['Tokenizer:eCoAIndex']['obj']['params'].update(TOKENIZER)

# ---------- 2. graph.nodes[].data.form (what the canvas renders and re-saves) ----------
for n in dsl['graph']['nodes']:
    nid = n.get('id'); form = (n.get('data') or {}).get('form')
    if form is None: continue
    if nid == 'Parser:eCoAParse':
        s = form.get('setups')
        patch_setups_list(s) if isinstance(s, list) else patch_setups_dict(s)
    elif nid == 'TokenChunker:eCoACert':
        form.update(CHUNKER)
    elif nid in EXTRACTORS:
        field, sysmsg, mdl = EXTRACTORS[nid]
        form.update({'llm_id': mdl, 'temperature': 0, 'field_name': field, 'sys_prompt': sysmsg,
                     'prompts': [{'role': 'user',
                                  'content': 'Certificate content:\n{TokenChunker:eCoACert@chunks}'}],
                     'max_tokens': 8192, 'maxTokensEnabled': True,
                     'frequency_penalty': 0, 'frequencyPenaltyEnabled': False,
                     'presence_penalty': 0, 'presencePenaltyEnabled': False,
                     'top_p': 1, 'topPEnabled': False})
        if 'temperatureEnabled' in form: form['temperatureEnabled'] = True
    elif nid == 'Tokenizer:eCoAIndex':
        form.update(TOKENIZER)

print(req('/api/v1/agents/' + AID, {'title': d['title'], 'dsl': dsl}, 'PUT'))
