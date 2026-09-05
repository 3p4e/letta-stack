# -*- coding: utf-8 -*-
"""Merge a batch of page readings into reads.json. Reads JSON on stdin.

Refuses to overwrite a code already recorded with different values: a second reading
of the same page is either a confirmation or a mistake, and it must not be silent.
"""
import json, sys
p = "reads.json"
d = json.load(open(p, encoding="utf-8"))
new = json.load(sys.stdin)
for k, v in new.items():
    if k in d and d[k] != v:
        raise SystemExit(f"REFUSING {k}: already recorded as {d[k]}, now given {v}")
    d[k] = v
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{len(new)} added, {len(d)} recorded")
