#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract QC parameter results from each certificate's parsed text.

Values are captured EXACTLY as printed on the certificate (as_printed), so the
register can render the same number of decimal places the lab actually printed
— per the owner's instruction. A parallel numeric value is derived only where
the printed form is genuinely a number; qualifiers (N.D., <LOQ, Absent,
Одговара) stay text because they are not numbers and must not be invented into
one.
"""
import json, os, subprocess, sys, tempfile, concurrent.futures as cf

SCRATCH = os.path.dirname(os.path.abspath(__file__))
MODEL = os.environ.get("EXTRACT_MODEL", "gpt-4o-mini")

SCHEMA_FIELDS = """
total_thc_pct          Total Delta9-THC (Вкупно Δ9-THC / Total Δ9-THC), percent
total_cbd_pct          Total CBD (Вкупно CBD), percent
total_cbn_pct          Total CBN (Вкупно CBN), percent
loss_on_drying_pct     Loss on drying (Губиток со сушење), percent
foreign_matter_pct     Foreign matter (Страни материи), percent
macroscopic_id         Macroscopic identification (Макроскопија) result
microscopic_id         Microscopic identification (Микроскопија) result
hptlc_id               HPTLC / chromatographic identity (Идентификација) result
tamc                   Total aerobic microbial count (TAMC)
tymc                   Total yeast/mould count (TYMC)
bile_tolerant_gnb      Bile-tolerant gram-negative bacteria
salmonella             Salmonella
e_coli                 Escherichia coli
aflatoxins_total       Total aflatoxins (sum B1+B2+G1+G2)
aflatoxin_b1           Aflatoxin B1
ochratoxin_a           Ochratoxin A
pb                     Lead / Олово (Pb)
cd                     Cadmium / Кадмиум (Cd)
arsenic                Arsenic / Арсен (As)
hg                     Mercury / Жива (Hg)
pesticides             Pesticide residues overall outcome
"""

PROMPT = f"""You are reading a pharmaceutical QC certificate of analysis for medical cannabis flower (Macedonian/English). Extract ONLY parameters that are actually present in this document.

Fields:
{SCHEMA_FIELDS}

CRITICAL RULES:
- Copy each value EXACTLY as printed, including decimals, symbols and notation: "12.39", "0.08", "<2", "N.D.", "ND", "<LOQ", "1.6x10^4", "Одговара", "Не одговара", "Absent".
- Do NOT convert units, do NOT round, do NOT normalise, do NOT translate result words.
- Do NOT include the unit in the value (no "%", no "mg/kg", no "CFU/g").
- If a parameter is NOT in this document, omit the key entirely. Never guess or carry over a value from another document.
- Return ONLY a JSON object, no prose, no markdown fence.

Also return:
- "batch_printed": the batch/series number exactly as printed (Серија / Сериски број / Batch No)
- "doc_code": the report/certificate number exactly as printed
- "is_stability": true only if the sample description mentions стабилност (stability), else false
"""


def call_openai(text, key):
    payload = {
        "model": MODEL, "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": text[:18000]},
        ],
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tf:
        json.dump(payload, tf); tp = tf.name
    try:
        r = subprocess.run(
            ["curl", "-sS", "https://api.openai.com/v1/chat/completions",
             "-H", f"Authorization: Bearer {key}",
             "-H", "Content-Type: application/json", "-d", f"@{tp}"],
            capture_output=True, text=True, timeout=120)
        d = json.loads(r.stdout)
        if "choices" not in d:
            return {"_error": str(d)[:300]}
        return json.loads(d["choices"][0]["message"]["content"])
    except Exception as e:
        return {"_error": str(e)[:300]}
    finally:
        os.path.exists(tp) and os.remove(tp)


def main():
    key = os.environ["OPENAI_API_KEY"]
    docs = json.load(open(f"{SCRATCH}/all_cert_texts.json"))
    print("docs to extract:", len(docs), flush=True)

    out_path = f"{SCRATCH}/extracted_params.json"
    done = {}
    if os.path.exists(out_path):
        done = {d["id"]: d for d in json.load(open(out_path))}
        print("resuming, already done:", len(done), flush=True)

    todo = [d for d in docs if d["id"] not in done]
    results = list(done.values())

    def work(doc):
        if not doc["text"].strip():
            return {**{k: doc[k] for k in ("id", "name")}, "meta": doc["meta"],
                    "params": {"_error": "no parsed text"}}
        p = call_openai(doc["text"], key)
        return {"id": doc["id"], "name": doc["name"], "meta": doc["meta"], "params": p}

    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        for i, res in enumerate(ex.map(work, todo), 1):
            results.append(res)
            if i % 20 == 0:
                print(f"{i}/{len(todo)}", flush=True)
                json.dump(results, open(out_path, "w"), ensure_ascii=False)

    json.dump(results, open(out_path, "w"), ensure_ascii=False)
    errs = sum(1 for r in results if "_error" in r.get("params", {}))
    print(f"DONE extracted={len(results)} errors={errs}", flush=True)


if __name__ == "__main__":
    main()
