#!/usr/bin/env python3
"""Create CoQ_PIPE — the ingestion pipeline for Purely Plant's own approved Certificates of Quality — and point the
PP_COQs dataset at it.

    python3 create_coq_pipe.py            # create (or update) the agent, set the dataset's pipeline
    python3 create_coq_pipe.py --dry-run  # print what would be sent

Why a pipeline of its own: eCOA_PIPE's prompts are written for outsourced-laboratory Certificates of Analysis
(lab, laboratory document code, accreditation, rows marked * for non-accredited methods). A CoQ is Purely Plant's own
certificate: its identity is the CoQ code + issue date, it cites the external and internal certificates behind each
parameter (section 03), and it may supersede an earlier CoQ. The parser, chunker and indexer are eCOA_PIPE's
(Claude Haiku 5.5 vision via the KVM4 gateway, whole certificate in one chunk); only the two extractor prompts differ.

The agent is made through the API, from eCOA_PIPE's live DSL, with the prompts written into BOTH the components (what
runs) and graph.nodes[].data.form (what the editor shows). Keep the editor closed on it: an open editor re-saves its
stale form copy every ~20 s and breaks every ingest (see CORPUS_RUN_PLAN.md, "editor trap").
Needs RAGFLOW_API_SERVER / RAGFLOW_API_KEY."""
import copy, json, os, sys, urllib.request

B = os.environ["RAGFLOW_API_SERVER"].rstrip("/")
K = os.environ["RAGFLOW_API_KEY"]
BASE_AGENT = "405267c4b4a311f1a370a99b32e82467"       # eCOA_PIPE
DATASET = "02dbd0d6cb6611f1a114bdd109af559f"          # PP_COQs
TITLE = "CoQ_PIPE"

QUESTIONS = """Write the questions this chunk can answer, one per line, no numbering, no preamble,
no commentary. Substitute the real values printed in the chunk - never leave a placeholder,
and never write a question whose answer is not in this chunk.

The chunk is a Purely Plant Certificate of Quality (CoQ). Work through these, in this order,
skipping any the chunk cannot answer:
1. What is the certificate of quality code and its date of issue?
2. Which batch, P-number and product (strain) is this certificate of quality for?
3. Which earlier certificate of quality does it supersede, and from what date?
4. What is the result for <parameter> for batch <batch number> (for example Total THC, CBD, loss on drying,
   TAMC, TYMC, heavy metals, mycotoxins, pesticides)?
5. Which certificate (laboratory and document code) is cited as the source of <parameter> for batch <batch number>,
   and which internal certificate of analysis (iCoA) is cited?
6. What is the specification and conformity statement of this certificate of quality for batch <batch number>?

The CoQ code and every other code is the one printed on the page, exactly (for example CoQ-PP_26-085,
iCoA-PP_26-098, ППК25050, 752/2025). Never correct, complete or normalise a printed value.

Write each question twice: once in English, once in Macedonian. Put the literal batch code,
P-number and certificate code into the question text exactly as printed."""

KEYWORDS = """Output one line: retrieval keywords separated by commas. No preamble, no explanation,
no labels, and never repeat any wording from these instructions.

Take the keywords only from the certificate text you are given. Include, where present:
the certificate of quality code (CoQ-PP_..) and its issue date, the superseded CoQ code, the batch code in every
spelling that appears, the P-number, the strain / product name as printed, the internal certificate of analysis code
(iCoA-PP_..), the document code of every external certificate cited (for example 752/2025, ППК25050, 220-31-К-26),
the name of every laboratory cited and its accreditation number where printed (for example ЛТ-005, ЛТ-083), the
specification reference, and the printed name of every analytical parameter, in both English and Macedonian.

Batch-code identity rules, so every spelling of the same batch retrieves together:
- A trailing star is part of the batch code's identity. If a code ends in an ASCII '*' or a fullwidth '＊', output
  BOTH the starred and the bare form as separate keywords.
- A separator inside a sub-lot code ('_', '-', '/') is part of the identity; output the form as printed.

If the text is unreadable or contains none of these, output nothing at all."""


def req(path, data=None, method=None):
    body = json.dumps(data, ensure_ascii=False).encode() if data is not None else None
    r = urllib.request.Request(B + path, data=body, method=method or ("POST" if body is not None else "GET"),
                               headers={"Authorization": "Bearer " + K, "Content-Type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(r, timeout=90))
    except urllib.error.HTTPError as e:
        return {"HTTPError": e.code, "body": e.read()[:400].decode("utf8", "replace")}


def agents():
    d = req("/api/v1/agents?page_size=100").get("data") or {}
    return d.get("canvas", []) if isinstance(d, dict) else d


def build():
    src = req("/api/v1/agents/" + BASE_AGENT)["data"]
    dsl = src["dsl"] if not isinstance(src["dsl"], str) else json.loads(src["dsl"])
    dsl = copy.deepcopy(dsl)
    for comp, prompt, user in (("Extractor:eCoAQuestions", QUESTIONS, "Certificate content:\n{TokenChunker:eCoACert@chunks}"),
                               ("Extractor:eCoAKeywords", KEYWORDS, "Certificate content:\n{Extractor:eCoAQuestions@chunks}")):
        flat = [{"role": "user", "content": user}]
        p = dsl["components"][comp]["obj"]["params"]
        p["sys_prompt"], p["prompts"] = prompt, flat
        for n in dsl["graph"]["nodes"]:
            if n["id"] == comp:
                n["data"]["form"]["sys_prompt"], n["data"]["form"]["prompts"] = prompt, flat
    return {"title": TITLE, "canvas_category": "dataflow_canvas", "description": (
        "Ingestion pipeline for Purely Plant's own approved Certificates of Quality (dataset PP_COQs). Same parser, "
        "chunker and indexer as eCOA_PIPE (Claude Haiku 5.5 vision via the KVM4 gateway, one chunk per certificate); "
        "the extractors ask CoQ questions - code and issue date, batch and product, superseded CoQ, parameter results, "
        "cited laboratory and internal certificates - and index CoQ/iCoA/lab document codes as keywords. "
        "Printed values are never corrected or normalised."), "dsl": dsl}


def main():
    spec = build()
    if "--dry-run" in sys.argv:
        print(json.dumps({k: (v if k != "dsl" else "<dsl>") for k, v in spec.items()}, ensure_ascii=False, indent=1))
        return
    found = [a for a in agents() if a.get("title") == TITLE]
    if found:
        aid = found[0]["id"]
        print("update", aid, req("/api/v1/agents/" + aid, spec, "PUT"))
    else:
        r = req("/api/v1/agents", spec, "POST")
        print("create", r)
        aid = (r.get("data") or {}).get("id") or next(
            (a["id"] for a in agents() if a.get("title") == TITLE), None)
    print("agent", aid)
    print("dataset", req("/api/v1/datasets/" + DATASET, {"parse_type": 2, "pipeline_id": aid}, "PUT"))


if __name__ == "__main__":
    main()
