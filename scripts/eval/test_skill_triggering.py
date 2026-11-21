#!/usr/bin/env python3
"""Measure whether the HIG skills actually get consulted, and which one.

Skills are pull-based: Claude decides whether to reach for one. For a
reference corpus that competes with what the model already believes it
knows, that decision is the whole ballgame -- perfect content nobody
consults is worth nothing. This measures the decision.

It installs the real skills into a throwaway project and runs `claude -p`
against realistic queries, recording which skill (if any) was invoked.

    python3 scripts/eval/test_skill_triggering.py                # default cases
    python3 scripts/eval/test_skill_triggering.py --cases my.json

Cases file is a list of {"query": ..., "expect": "<skill name>" | null},
where null means no skill should fire.

See README.md in this directory for the two measurement traps this avoids.
"""

import argparse
import concurrent.futures as cf
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKILLS_SRC = os.path.join(REPO, ".claude", "skills")
DEFAULT_MODEL = "claude-opus-5"
DEFAULT_TIMEOUT = 600

DEFAULT_CASES = [
    # Platform questions all land on hig-guide: the per-platform skills were
    # folded into hig-guide, so there is one skill to win them.
    {"query": "my mac app's toolbar just feels off compared to native apps, 9 icon "
              "buttons crammed up top and a search box on the left. what am i doing wrong",
     "expect": "hig-guide"},
    {"query": "adding a watchOS companion to our fitness app. what can i actually put "
              "on the watch face and how much info fits in a complication",
     "expect": "hig-guide"},
    {"query": "porting our iPad app to Vision Pro. where should windows go in space and "
              "does the navigation need to change",
     "expect": "hig-guide"},
    {"query": "building a reading app for iphone + ipad, 7 top level sections. tab bar "
              "or sidebar on the iPad specifically",
     "expect": "hig-guide"},
    {"query": "our designer used a fixed 13pt font everywhere in the iOS app and QA "
              "flagged it as an accessibility problem. whats the minimum we should support",
     "expect": "hig-guide"},
    # A product rather than a control: the design skill should start it.
    {"query": "i want an app for splitting bills with friends. add a bill, split it, "
              "see who owes what, settle up",
     "expect": "design-workflow"},
    # Apple's look on a target with no system palette.
    {"query": "make this react settings page look like an iOS settings screen, right "
              "now it's just default browser buttons and checkboxes",
     "expect": "ui-kit-for-apple-platforms"},
    {"query": "my swiftui sheet slides up with a linear 0.3s animation and it feels "
              "dead. how should it move",
     "expect": "motion-for-apple-platforms"},
    # Android has its own kit; it should win over the Apple skills. A whole
    # Android app is a product, so design-workflow starts it and brings the kit in.
    {"query": "we need the android version of our recipe app, same screens as the iphone "
              "one but it should feel like a pixel app",
     "expect": "design-workflow"},
    {"query": "what height should a material 3 top app bar be and what colour role does "
              "it turn when content scrolls under it",
     "expect": "ui-kit-for-android"},
    # Near-misses: Apple-adjacent but not UI design. A skill that fires here is
    # interrupting work it can't help with, which is its own kind of failure.
    {"query": "xcode 26 keeps failing my archive with 'no profiles for com.acme.app "
              "were found'. how do i fix code signing for a team distribution build",
     "expect": None},
    {"query": "our core data migration from v3 to v4 is losing the relationship between "
              "Order and LineItem. do i need a mapping model",
     "expect": None},
]


def make_project():
    root = tempfile.mkdtemp(prefix="hig-eval-")
    dst = os.path.join(root, ".claude", "skills")
    os.makedirs(dst)
    installed = []
    for d in sorted(os.listdir(SKILLS_SRC)):
        # Every skill the repo ships. This once matched an "apple-" prefix,
        # which no skill has carried since the rename, so it installed none.
        if os.path.isfile(os.path.join(SKILLS_SRC, d, "SKILL.md")):
            shutil.copytree(os.path.join(SKILLS_SRC, d), os.path.join(dst, d))
            installed.append(d)
    return root, installed


def probe(query, root, model, timeout, expect=None):
    """Skills invoked for one query. Distinguishes timeout from non-trigger --
    conflating them makes a slow run look like a dead skill.

    Stops as soon as the expected skill fires. A product brief goes on to
    scaffold a whole project after routing, and waiting for that measures
    the build rather than the decision -- it timed out at 600s with the
    right skill already chosen."""
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    p = subprocess.Popen(
        ["claude", "-p", query, "--output-format", "stream-json",
         "--verbose", "--model", model],
        cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        text=True, start_new_session=True,
    )
    expired = threading.Event()

    def stop():
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    timer = threading.Timer(timeout, lambda: (expired.set(), stop()))
    timer.start()
    picked = []
    try:
        for line in p.stdout:
            try:
                ev = json.loads(line)
            except Exception:
                continue
            msg = ev.get("message")
            if not isinstance(msg, dict):
                continue
            for b in msg.get("content") or []:
                if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Skill":
                    s = str(b.get("input", {}).get("skill", ""))
                    if s and s not in picked:
                        picked.append(s)
            if expect and expect in picked:
                stop()
                return picked
        p.wait()
    finally:
        timer.cancel()
    if expired.is_set():
        return picked + ["TIMEOUT"]
    if p.returncode != 0:
        return picked + [f"ERROR(rc={p.returncode})"]
    return picked


def run_case(case, model, timeout):
    """One project per case, so a build in one can't leak files into another."""
    root, _ = make_project()
    try:
        return probe(case["query"], root, model, timeout, case["expect"])
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--runs", type=int, default=1,
                    help="ask each query this many times; one answer is a coin toss")
    args = ap.parse_args()

    cases = json.load(open(args.cases)) if args.cases else DEFAULT_CASES
    installed = [d for d in sorted(os.listdir(SKILLS_SRC))
                 if os.path.isfile(os.path.join(SKILLS_SRC, d, "SKILL.md"))]
    print(f"installing {len(installed)} skills per case: {', '.join(installed)}\n")

    # Keyed by position, not query, so a repeated query keeps every answer.
    cases = [c for c in cases for _ in range(args.runs)]
    results = {}
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(run_case, c, args.model, args.timeout): i for i, c in enumerate(cases)}
        for f in cf.as_completed(futs):
            results[futs[f]] = f.result()

    good = 0
    for i, c in enumerate(cases):
        got = results[i]
        expect = c["expect"]
        fired = [g for g in got if g.split(":")[-1] in installed]
        if expect is None:
            ok = not fired
        else:
            ok = expect in fired
        good += ok
        label = "ok  " if ok else "FAIL"
        shown = ",".join(got) if got else "none"
        print(f"[{label}] expect={expect or 'no skill':22} got={shown}")
        print(f"        {c['query'][:86]}")

    print(f"\n{good}/{len(cases)} cases correct")
    return 0 if good == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
