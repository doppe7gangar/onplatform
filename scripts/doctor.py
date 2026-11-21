#!/usr/bin/env python3
"""Check every claim in this repo that has a computable ground truth.

Written after finding the same class of bug four rounds running, one
instance at a time: a hardcoded 949 where the kit holds 947, a SKILL.md
still claiming 2,280 rules after a re-scrape made it 2,326, instructions
naming build_web_tokens.py months after it was renamed, a checker whose
documented path did not exist once the skill was installed. Each was
fixed on its own. None of them should have needed finding by hand,
because every one is a number or a path that can be resolved and
compared.

So this resolves them. It is the difference between "I fixed the stale
count" and "a stale count cannot ship".

    python3 scripts/doctor.py         # exits non-zero on any problem
    python3 scripts/doctor.py -v      # show every check
    python3 scripts/doctor.py --fast  # skip the browser run

build_design_tokens.py calls --fast on every rebuild,
so a regenerated file that no longer matches what the docs claim fails
at the moment it is written rather than months later in a test round.

What it will not catch: whether the values are *correct*. A confidently
wrong measurement stated consistently everywhere passes this cleanly.
That is what verify_web_ui.py and the eval runs are for.
"""

import argparse
import json
import glob
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SKILLS = os.path.join(REPO, ".claude", "skills")


class Doctor:
    def __init__(self, verbose):
        self.bad = []
        self.n = 0
        self.verbose = verbose

    def check(self, ok, label, detail=""):
        self.n += 1
        if ok:
            if self.verbose:
                print(f"  ok    {label}  {detail}")
        else:
            print(f"  FAIL  {label}  {detail}")
            self.bad.append(label)


def read(p):
    return open(p, encoding="utf-8", errors="replace").read()


def skill_docs():
    """Every SKILL.md plus the repo-level docs that make claims."""
    out = []
    for sk in sorted(os.listdir(SKILLS)):
        p = os.path.join(SKILLS, sk, "SKILL.md")
        if os.path.exists(p):
            out.append((sk, p))
    # The Apple kit's references are its SKILL.md split up, with paths still
    # relative to the skill folder, so they're checked the same way.
    kit = "ui-kit-for-apple-platforms"
    for ref in sorted(glob.glob(os.path.join(SKILLS, kit, "references", "*.md"))):
        out.append((kit, ref))
    for name in ("TESTING.md", "README.md", "AGENTS.md"):
        p = os.path.join(REPO, name)
        if os.path.exists(p):
            out.append((None, p))
    return out


def truth():
    """Ground truth, derived rather than declared."""
    t = {}
    hig = os.path.join(SKILLS, "hig-guide")
    refs = os.path.join(hig, "references")

    topics = os.path.join(refs, "topics.md")
    if os.path.exists(topics):
        t["topics"] = len(re.findall(r"^\| [^|]+ \| \[", read(topics), re.M))
    fi = os.path.join(refs, "framework-index.json")
    if os.path.exists(fi):
        t["components"] = len(json.load(open(fi)))
    api = os.path.join(refs, "api-map.md")
    if os.path.exists(api):
        t["frameworks"] = read(api).count("\n### ")

    kit = os.path.join(SKILLS, "ui-kit-for-apple-platforms", "ui-kit-tokens.json")
    if os.path.exists(kit):
        t["measurements"] = len(json.load(open(kit)))
    return t


# Claim patterns -> the key in truth() they must equal. Written to match
# how the docs actually phrase things, not how I wish they did.
# Each pattern must pin the claim to the whole corpus. A bare "N rules"
# also matches "11 rules on destructive actions across 8", which is a
# true statement about a subset -- flagging it as a stale total was the
# checker being wrong, not the doc.
CLAIMS = [
    (r"Guidelines, (\d[\d,]*) of them", "topics"),
    (r"(\d[\d,]*) (?:SwiftUI, UIKit and AppKit components|system components|symbols across)", "components"),
    (r"(\d+)\+ Apple frameworks", "frameworks"),
    (r"(\d+)\+ other frameworks", "frameworks"),
    (r"(\d+)\+ frameworks including", "frameworks"),
    (r"(\d[\d,]*) renderings", "measurements"),
]


def check_counts(d, facts):
    for sk, path in skill_docs():
        text = read(path)
        rel = os.path.relpath(path, REPO)
        for pat, key in CLAIMS:
            if key not in facts:
                continue
            for m in re.finditer(pat, text):
                claimed = int(m.group(1).replace(",", ""))
                actual = facts[key]
                # "32+ frameworks" is a floor, not an equality.
                ok = claimed <= actual if "+" in m.group(0) else claimed == actual
                d.check(ok, f"{rel}: {key} count",
                        f"says {claimed}, actual {actual}")


# Each kit verifier and the skill it ships in.
VERIFIERS = {"verify_web_ui.py": "ui-kit-for-apple-platforms", "verify_mac_ui.py": "ui-kit-for-apple-platforms",
             "verify_ipad_ui.py": "ui-kit-for-apple-platforms", "verify_android_ui.py": "ui-kit-for-android"}


def verifier_for(sk, line):
    """Whose count a line quotes. Everything in ui-kit-for-android's own
    SKILL.md is its verifier's; elsewhere a line about Android or Material
    is, a line about the iPad is verify_ipad_ui.py's, a line about the Mac
    kit is verify_mac_ui.py's, and any other is verify_web_ui.py's."""
    if sk == "ui-kit-for-android" or (sk is None and re.search(
            r"verify_android_ui|\bandroid\b|material", line, re.I)):
        return "verify_android_ui.py"
    if re.search(r"verify_ipad_ui|\bipad(os)?\b", line, re.I):
        return "verify_ipad_ui.py"
    if re.search(r"verify_mac_ui|\bmac(os)?\b|Mac kit", line, re.I):
        return "verify_mac_ui.py"
    return "verify_web_ui.py"


def check_verifier_count(d):
    """The docs quote how many checks each kit verifier runs. Run them and see."""
    claims = {name: [] for name in VERIFIERS}
    for sk, path in skill_docs():
        for line in read(path).splitlines():
            for m in re.finditer(r"(\d+) checks\b", line):
                claims[verifier_for(sk, line)].append(
                    (os.path.relpath(path, REPO), int(m.group(1))))
    for name, found in claims.items():
        if not found:
            continue
        script = os.path.join(SKILLS, VERIFIERS[name], name)
        if not os.path.exists(script):
            d.check(False, f"{name} present")
            continue
        try:
            out = subprocess.run([sys.executable, script], capture_output=True,
                                 text=True, timeout=900).stdout
        except Exception as e:
            d.check(False, f"{name} runs", str(e))
            continue
        m = re.search(r"(\d+)/(\d+) checks passed", out)
        if not m:
            d.check(False, f"{name} reports a total", out[-200:])
            continue
        actual = int(m.group(2))
        d.check(m.group(1) == m.group(2), f"{name} all pass", f"{m.group(1)}/{actual}")
        for rel, claimed in found:
            d.check(claimed == actual, f"{rel}: {name} check count",
                    f"says {claimed}, actual {actual}")


def check_script_refs(d):
    """Every .py a doc tells you to run has to be where it says.

    Two forms, because scripts live in two places. `scripts/foo.py` is
    repo-relative and only ever run from the root. A bare `foo.py` in a
    SKILL.md means the script ships inside that skill -- which is the
    only form that still works once someone copies the skill into
    ~/.claude/skills/, and so the form the skills should prefer.

    The bare case went unchecked until design-workflow's instructions moved
    off `scripts/` and onto its own bundled tools: coverage of that skill
    silently dropped by three checks, and a rename would have broken the
    documented command with nothing to catch it.
    """
    names = set(os.listdir(HERE))
    for sk, path in skill_docs():
        rel = os.path.relpath(path, REPO)
        text = read(path)
        for m in re.finditer(r"scripts/([\w.]+\.py)", text):
            d.check(m.group(1) in names, f"{rel}: scripts/{m.group(1)} exists")
        # A repo-level doc's invocations resolve from the repo root.
        # TESTING.md pointed at ../skilltest/projtest.py -- a harness that
        # lived outside the tree entirely, so the documented command was
        # broken for everyone but me. Same class as the two before it,
        # and unchecked because this loop skipped the repo-level docs.
        base = os.path.join(SKILLS, sk) if sk else REPO
        # Only invocations -- `python3 foo.py`. A bare mention in prose
        # ("doctor.py fails the build if...") is describing a tool, not
        # telling anyone to run it from here, and flagging those made the
        # check cry wolf on ui-kit-for-apple-platforms's perfectly correct sentence.
        for m in re.finditer(
                r"python3\s+((?:\.\./)?[\w./-]*[\w-]+\.py)\b", text):
            ref = m.group(1)
            # `scripts/foo.py` in a SKILL.md is repo-relative and already
            # handled above -- but only when it is a bare filename. A
            # nested one like scripts/eval/projtest.py matched neither
            # pattern and sailed through both, which is how a doc came to
            # point at a harness outside the tree. Resolve nested paths
            # from the repo root wherever they appear.
            if ref.startswith("scripts/"):
                if "/" not in ref[len("scripts/"):]:
                    continue
                where, label = REPO, "repo"
            else:
                where, label = base, (sk or "repo")
            d.check(os.path.exists(os.path.join(where, ref)),
                    f"{label}: {ref} present when installed")


def check_skill_paths(d):
    """A skill must not name a file it won't have once installed."""
    for sk, path in skill_docs():
        if sk is None:
            continue
        base = os.path.join(SKILLS, sk)
        text = read(path)
        # Any backticked directory/file path, not only the four known
        # prefixes. hig-guide's SKILL.md pointed at https://developer.apple.com/design/human-interface-guidelines/buttons
        # ten times over, including the routing table that decides which
        # page to open -- correct inside references/, where those files
        # live, and dead from the skill root where SKILL.md sits. The
        # prefix-limited pattern could not see it.
        # `../hig-guide/...` is how one skill points into a sibling, the
        # same form design-workflow already uses for ui-kit-for-apple-platforms. Resolved
        # against the skills root so the reference is checked rather than
        # skipped -- a cross-skill path is exactly the kind that rots.
        for m in re.finditer(r"`((?:\.\./)?[\w-]+/[\w./ -]*[\w-]+\.\w+)`", text):
            p = m.group(1)
            if "<" in p or p.startswith("scripts/"):
                continue
            d.check(os.path.exists(os.path.join(base, p)),
                    f"{sk}: {p} present when installed")


WORDNUM = {"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,
           "eight":8,"nine":9,"ten":10,"eleven":11,"twelve":12}


def check_reference_count(d):
    """"Nine references" has to match how many are actually there.

    Added after shipping a framework-index and leaving the sentence above
    it reading "Eight references" -- the one stale count in this file
    that nothing else was watching, because it is spelled as a word.
    """
    for sk, path in skill_docs():
        if sk is None:
            continue
        refs = os.path.join(SKILLS, sk, "references")
        if not os.path.isdir(refs):
            continue
        actual = len([f for f in os.listdir(refs) if f.endswith(".md")])
        for m in re.finditer(r"\b(\w+) references,", read(path)):
            claimed = WORDNUM.get(m.group(1).lower())
            if claimed:
                d.check(claimed == actual, f"{sk}: reference count",
                        f"says {m.group(1)} ({claimed}), actual {actual}")


def check_placeholders(d):
    """Generated files must not ship an unsubstituted placeholder."""
    for sk in sorted(os.listdir(SKILLS)):
        for dirpath, _, files in os.walk(os.path.join(SKILLS, sk)):
            for f in files:
                if not f.endswith((".md", ".css", ".json")):
                    continue
                p = os.path.join(dirpath, f)
                if os.path.getsize(p) > 5_000_000:
                    continue
                text = read(p)
                # Strip fenced code first. "{{" was flagging JSX inline
                # style -- style={{ x }} -- which is ordinary code, not an
                # unsubstituted template. Only genuinely ours count.
                prose = re.sub(r"^```.*?^```", "", text, flags=re.M | re.S)
                for ph in ("{TOTAL}", "TODO:", "FIXME", "XXX:"):
                    if ph in prose:
                        d.check(False,
                                f"{os.path.relpath(p, REPO)}: placeholder",
                                ph)


def check_provenance(d):
    """Apple's text and images stay out; see scripts/provenance_guard.py."""
    out = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "provenance_guard.py"), "-q"],
                         capture_output=True, text=True)
    problems = [l.strip()[5:] for l in out.stdout.splitlines() if l.strip().startswith("FAIL")]
    d.check(out.returncode == 0, "no Apple material in the repo",
            "; ".join(problems[:3]) or out.stderr[-200:])


def check_corroboration(d, min_components=2):
    """Every measured colour should appear in more than one component.

    doctor otherwise proves only that the repo agrees with itself. This
    is the one check that says something about whether a value is
    *right*: a measurement error in one PNG cannot make the same hex turn
    up in fifteen unrelated components. #0088FF appears in nine, #1A1A1A
    in fifteen -- which is stronger evidence than the fact that they
    disagree with the palette circulating online.

    A value found in a single component is not necessarily wrong. It does
    mean nothing else in the kit backs it up, so it should be checked by
    hand before being trusted.
    """
    tokens = os.path.join(SKILLS, "ui-kit-for-apple-platforms", "tokens", "ios-tokens.css")
    kit = os.path.join(SKILLS, "ui-kit-for-apple-platforms", "ui-kit-tokens.json")
    if not (os.path.exists(tokens) and os.path.exists(kit)):
        return
    # Strip CSS comments first. The header explains that the accent is
    # #0088FF "not #007AFF", so scraping the raw file picks up the
    # superseded value and then reports it as uncorroborated -- which is
    # true, and entirely beside the point.
    css = re.sub(r"/\*.*?\*/", "", read(tokens), flags=re.S)
    wanted = sorted({m.group(0).upper()
                     for m in re.finditer(r"#[0-9A-Fa-f]{6}", css)})
    rows = json.load(open(kit))

    # Values Apple publishes outright, in the Color page's swatch alt
    # text, do not need corroborating against the kit -- a stated value
    # beats an inferred one. Several of them (pink, orange, yellow, two
    # greys) simply never appear in the components that were rendered.
    palette = os.path.join(SKILLS, "ui-kit-for-apple-platforms", "tokens", "apple-system-palette.json")
    published = set()
    if os.path.exists(palette):
        data = json.load(open(palette))
        for group in ("system", "grays"):
            for values in data[group].values():
                published.update(v.upper() for v in values)

    for hexv in wanted:
        if hexv in published:
            d.check(True, f"colour {hexv} published by Apple", "Color page")
            continue
        comps = {r["component"] for r in rows
                 for c in r["colours"]
                 if c["hex"].upper() == hexv and c["alpha"] >= 0.99}
        if not comps:
            continue  # translucent or geometry-only; not a flat fill
        d.check(len(comps) >= min_components,
                f"colour {hexv} corroborated",
                f"{len(comps)} component(s)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("--fast", action="store_true",
                    help="skip the browser run; everything else is instant, "
                         "so the build can call this on every rebuild")
    args = ap.parse_args()

    d = Doctor(args.verbose)
    facts = truth()
    print("ground truth:", ", ".join(f"{k}={v}" for k, v in sorted(facts.items())))
    print()

    check_counts(d, facts)
    check_script_refs(d)
    check_skill_paths(d)
    check_placeholders(d)
    check_reference_count(d)
    check_provenance(d)
    check_corroboration(d)
    if not args.fast:
        check_verifier_count(d)

    print(f"\n{d.n - len(d.bad)}/{d.n} checks passed")
    if d.bad:
        print("failed: " + ", ".join(sorted(set(d.bad))))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
