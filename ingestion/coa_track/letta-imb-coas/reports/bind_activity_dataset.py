#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bind the QC activity dataset from the session transcript.

The activity report is a data-driven document, so under the document suite's §6B rule it
may not carry a single hand-typed figure: every number it prints has to be computed from a
bound dataset at build time, and the dataset has to carry its own provenance. This produces
that dataset.

The source is the Claude Code session transcript — a JSONL append log, one object per
event, each stamped in UTC. It is the only record of when work was actually requested and
performed, and it is written as the work happens rather than reconstructed afterwards.

Three things are separated out, because they answer different questions:

  prompts   turns the QC Manager actually typed. The transcript files a great deal else
            under the same "user" role — tool results, system reminders, webhook events,
            the hourly PR check-ins this session schedules for itself — and counting those
            as human input would roughly triple the apparent prompt count. They are
            filtered by role heuristics and by an explicit pattern list.
  events    every timestamped entry of any kind. These bound *activity*: work that
            continued after the last prompt of a block still shows up here, which is how
            a task that was handed over at 11:04 and finished at 12:00 gets its true
            duration rather than zero.
  meta      transcript path, SHA-256, size and the timezone the report renders in.

Timestamps are converted to Europe/Skopje. The transcript is UTC; the report is read by
people who worked those hours locally, and an activity report that says 04:11 when the
person remembers 06:11 is worse than no report.
"""
import datetime
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "qc_activity_dataset.json")

TRANSCRIPT = ("/root/.claude/projects/-home-user-letta-stack/"
              "4877ce6e-ae82-551e-bf35-5698c379c3be.jsonl")

TZ_NAME = "Europe/Skopje (UTC+02:00)"
TZ = datetime.timezone(datetime.timedelta(hours=2))

# Turns the harness files under the "user" role that no person typed.
NOT_HUMAN = re.compile(
    r"^(Self check-in for|<system-reminder>|Caveat:|<command-name>|<local-command|"
    r"This session is being continued|<github-webhook-activity>|\[SYSTEM NOTIFICATION|"
    r"<task-notification>|Your task is to complete)", re.I)

# Task blocks, keyed by the local time of the prompt that opened each one. A block runs
# until the next one opens; its duration is measured from the event stream, not assumed.
# The titles and descriptions are editorial; every number attached to them is computed.
BLOCKS = [
    ("2026-08-10T19:22", "QC-01"),
    ("2026-08-10T20:26", "QC-02"),
    ("2026-08-10T21:28", "QC-03"),
    ("2026-08-11T00:19", "QC-04"),
    ("2026-08-11T01:56", "QC-05"),
    ("2026-08-11T02:42", "QC-06"),
    ("2026-08-11T03:23", "QC-07"),
    ("2026-08-11T04:11", "QC-08"),
    ("2026-08-11T05:53", "QC-09"),
    ("2026-08-11T06:02", "QC-10"),
    ("2026-08-11T06:16", "QC-11"),
    ("2026-08-11T06:35", "QC-12"),
    ("2026-08-11T06:58", "QC-13"),
    ("2026-08-11T09:54", "QC-14"),
    ("2026-08-11T10:50", "QC-15"),
    ("2026-08-11T11:04", "QC-16"),
]
# The reporting period closes when the QC Manager asked for this report; work after that
# point belongs to the next period.
PERIOD_START = "2026-08-10T00:00"
PERIOD_END = "2026-08-11T12:56"


def local(iso_utc):
    return datetime.datetime.fromisoformat(
        iso_utc.replace("Z", "+00:00")).astimezone(TZ)


def main():
    if not os.path.exists(TRANSCRIPT):
        sys.stderr.write("transcript not found: %s\n" % TRANSCRIPT)
        return 1

    h = hashlib.sha256()
    with open(TRANSCRIPT, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)

    prompts, events, skipped = [], [], 0
    with open(TRANSCRIPT, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except ValueError:
                skipped += 1
                continue
            ts = d.get("timestamp")
            if not ts:
                continue
            t = local(ts)
            events.append(t.isoformat())
            if d.get("type") != "user" or d.get("toolUseResult") is not None:
                continue
            if d.get("isMeta"):
                continue
            c = (d.get("message") or {}).get("content")
            if isinstance(c, list):
                if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in c):
                    continue
                text = " ".join(b.get("text", "") for b in c
                                if isinstance(b, dict) and b.get("type") == "text")
            else:
                text = c if isinstance(c, str) else ""
            text = re.sub(r"\s+", " ", (text or "")).strip()
            if not text or NOT_HUMAN.search(text) or text.startswith("<"):
                continue
            prompts.append({"t": t.isoformat(), "text": text})

    events.sort()
    prompts.sort(key=lambda p: p["t"])

    data = {
        "meta": {
            "source": TRANSCRIPT,
            "sha256": h.hexdigest(),
            "bytes": os.path.getsize(TRANSCRIPT),
            "timezone": TZ_NAME,
            "unparseable_lines": skipped,
            "period_start": PERIOD_START,
            "period_end": PERIOD_END,
        },
        "blocks": [{"opens": a, "code": c} for a, c in BLOCKS],
        "prompts": prompts,
        "events": events,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)

    print("bound %s" % os.path.relpath(OUT, HERE))
    print("  transcript sha256 %s" % h.hexdigest()[:16])
    print("  events %d   human prompts %d   unparseable %d"
          % (len(events), len(prompts), skipped))
    print("  span %s -> %s" % (prompts[0]["t"][:16], prompts[-1]["t"][:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
