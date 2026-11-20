#!/usr/bin/env python3
"""Fail if material this repo has no right to pass on gets into it.

Apple's Human Interface Guidelines, its design resources and its fonts
stay out of this repo, and so does anything like them. It checks what git
tracks (or, outside a checkout, what's on disk):

  - known paths for copies of Apple's text and images
  - images and fonts that aren't listed in NOTICE
  - SF Pro and Apple's other fonts, under any name
  - raster images embedded as base64 in text files
  - images hot-linked from Apple's documentation servers, the mark of a
    page converted from Apple's site

    python3 scripts/provenance_guard.py            # what CI runs
    python3 scripts/provenance_guard.py --corpus ~/hig-copy/content

--corpus also compares every text file against a private copy of the HIG
you keep outside the repo, and fails any file with runs of eight or more
words of Apple's prose. It isn't part of CI, because CI has no such copy
and this repo can't ship one; run it before a release. Matching words is
a floor, not a clearance: a close paraphrase passes it.
"""

import argparse
import glob
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FORBIDDEN = [
    "content/",
    "ios-27-ui-kit_assets/",
    ".claude/skills/hig-guide/assets/",
    ".claude/skills/hig-guide/references/pages/",
    ".claude/skills/hig-guide/references/rules.md",
    ".claude/skills/hig-guide/references/platform-diffs.md",
    ".claude/skills/hig-guide/references/specs.md",
    ".claude/skills/hig-guide/references/components.md",
    ".claude/skills/hig-guide/references/assets-index.md",
]

# Every image and font the repo may hold, and why. NOTICE says where each
# comes from; add a file there and here together.
ALLOWED = [
    re.compile(r"^docs/(iphone|ipad|mac|android)\.png$"),          # our own renders
    re.compile(r"^\.claude-plugin/icon\.png$"),                       # our own drawing
    re.compile(r"^\.claude/skills/ui-kit-for-apple-platforms/fonts/InterVariable(-Italic)?\.woff2$"),  # SIL OFL
    re.compile(r"^\.claude/skills/ui-kit-for-android/fonts/roboto-[a-z-]+\.woff2$"),         # SIL OFL
]
BINARY = re.compile(r"\.(png|jpe?g|gif|webp|heic|tiff?|bmp|ico|pdf|psd|sketch|fig|"
                    r"ttf|otf|woff2?|eot|mp4|mov)$", re.I)
APPLE_FONT = re.compile(r"sf-?pro|sf-?compact|sf-?mono|sf-?arabic|new-?york|sfns", re.I)
RASTER_B64 = re.compile(r"data:image/(?:png|jpe?g|gif|webp);base64,[A-Za-z0-9+/=]{800,}")
APPLE_IMAGES = re.compile(r"(?:docs-assets\.developer\.apple\.com|developer\.apple\.com/"
                          r"tutorials/images)/[^\s)\"']+\.(?:png|jpe?g|svg)", re.I)
TEXT = re.compile(r"\.(md|py|js|ts|tsx|jsx|css|html|json|swift|kt|xml|dart|txt|sh|ya?ml)$", re.I)
# This file names the patterns it looks for.
SELF = {"scripts/provenance_guard.py"}


def tracked():
    try:
        out = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True,
                             text=True, check=True).stdout.splitlines()
        return [p for p in out if os.path.exists(os.path.join(REPO, p))]
    except (OSError, subprocess.CalledProcessError):
        files = []
        for root, dirs, names in os.walk(REPO):
            dirs[:] = [d for d in dirs if d not in (".git", "node_modules")]
            files += [os.path.relpath(os.path.join(root, n), REPO) for n in names]
        return files


DOC_LINK = re.compile(r"\[[^\]]*\]\(https://developer\.apple\.com/documentation[^)]*\)")


def words(text):
    # The title of an Apple documentation entry, as link text, is its name.
    text = DOC_LINK.sub(" ", text)
    return re.findall(r"[a-z0-9']+", re.sub(r"https?://\S+", " ", text).lower())


UNITS = {"pt", "px", "x", "2x", "3x", "mm", "in", "na", "n", "a"}


def prose(gram):
    # A run of figures and units is a fact shared with Apple, not wording.
    return sum(1 for w in gram if w.isalpha() and w not in UNITS) >= 5


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--corpus", help="folder holding a private copy of the HIG as text")
    ap.add_argument("--max-runs", type=int, default=20,
                    help="copied 8-word runs a file may hold before it fails (titles and "
                         "labels match too; prose fails well above this)")
    ap.add_argument("-q", "--quiet", action="store_true")
    a = ap.parse_args()

    files = tracked()
    bad = []
    for p in files:
        if any(p == f or p.startswith(f) for f in FORBIDDEN):
            bad.append(f"{p}: a known path for copies of Apple's text or images")
        elif BINARY.search(p) and not any(rx.match(p) for rx in ALLOWED):
            bad.append(f"{p}: an image or font not listed in NOTICE")
        if BINARY.search(p) and APPLE_FONT.search(os.path.basename(p)):
            bad.append(f"{p}: looks like one of Apple's fonts")
    for p in files:
        if p in SELF or not TEXT.search(p):
            continue
        try:
            text = open(os.path.join(REPO, p), encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            continue
        if RASTER_B64.search(text):
            bad.append(f"{p}: a raster image embedded as base64")
        hits = APPLE_IMAGES.findall(text)
        if hits:
            bad.append(f"{p}: {len(hits)} image(s) linked from Apple's documentation servers")

    if a.corpus:
        corpus = set()
        for f in glob.glob(os.path.join(os.path.expanduser(a.corpus), "**", "*.md"), recursive=True):
            w = words(open(f, encoding="utf-8").read())
            corpus.update(tuple(w[i:i + 8]) for i in range(len(w) - 7))
        if not corpus:
            sys.exit(f"no .md files under {a.corpus}")
        for p in files:
            if p in SELF or not TEXT.search(p):
                continue
            try:
                w = words(open(os.path.join(REPO, p), encoding="utf-8").read())
            except (UnicodeDecodeError, OSError):
                continue
            n = sum(1 for i in range(len(w) - 7)
                    if tuple(w[i:i + 8]) in corpus and prose(w[i:i + 8]))
            if n > a.max_runs:
                bad.append(f"{p}: {n} runs of eight words copied from the HIG")

    for b in bad:
        print("  FAIL", b)
    if not a.quiet:
        print(f"provenance: {len(files)} files checked, {len(bad)} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
