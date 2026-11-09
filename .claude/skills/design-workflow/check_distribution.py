#!/usr/bin/env python3
"""Check what a design folder would hand on, before it is shared or published.

    python3 check_distribution.py ./design                     # a mockup you're working on
    python3 check_distribution.py ./design --purpose publish   # before it leaves your hands
    python3 check_distribution.py ./design --manifest files.json

new_project.py, sf_icons.py and export_figma.py all write into a design
folder. Most of what they write is this kit's own work or openly licensed
and only needs its licence beside it; some of it comes from the Mac it ran
on and may not be passed on at all. This lists every file, says where it
comes from and under what licence, and fails on:

  - SF Pro or another Apple font, recognised by its name table under any
    file name, whether as a file or embedded in a page (export_figma.py
    embeds fonts)
  - SF Symbols drawn on your Mac (sf_icons.py) or exported from the SF
    Symbols app
  - images from Apple's design resources, or hot-linked from Apple's sites
  - Inter, Roboto, Material Symbols or the kit's own files without the
    licence text that has to travel with them
  - with --purpose publish, any image or font whose origin isn't recorded

Two purposes:

  mockup   (the default) a design you are working on. SF Pro and SF Symbols
           from your own Mac are allowed in a mockup of an app for Apple's
           platforms, as long as git ignores them. On an Android, web or
           marketing design they fail.
  publish  anything leaving your hands: a public repo, a website, a zip you
           send. Apple's fonts and symbols fail whatever the platform, and so
           does any image or font whose origin isn't recorded.

Record what you added yourself in assets.json in the design folder:

    {"img/hero.jpg": {"source": "our own photo shoot", "licence": "own work"}}

It reads files, not contracts: it can tell that a font is Inter and that
Inter's licence is beside it, not that your use of a file is allowed. A
clean result means nothing it knows to look for was found.
"""

import argparse
import base64
import fnmatch
import hashlib
import io
import json
import os
import re
import struct
import subprocess
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.dirname(HERE)

APPLE_PLATFORMS = {"ios", "ipados", "macos", "watchos", "visionos", "tvos"}
NON_APPLE = {"android", "web", "marketing"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".next", "dist-cache"}
FONT_EXT = (".woff2", ".woff", ".ttf", ".otf", ".ttc", ".eot")
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".heic", ".bmp", ".tif",
             ".tiff", ".ico", ".svg", ".pdf", ".psd", ".sketch", ".fig")
TEXT_EXT = (".html", ".htm", ".css", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".vue",
            ".svelte", ".json", ".md", ".txt", ".xml", ".svg", ".swift", ".kt", ".dart",
            ".yml", ".yaml")
IGNORE_FILES = {".DS_Store", "Thumbs.db"}

# Apple's fonts, by family name and by file name.
APPLE_FAMILY = re.compile(r"^\.?SF ?NS\b|^\.?SF (Pro|Compact|Mono|Arabic|Armenian|Georgian|"
                          r"Hebrew|Camera)\b|^New York\b|^San Francisco\b", re.I)
APPLE_FONT_FILE = re.compile(r"sf-?pro|sf-?compact|sf-?mono|sf-?arabic|new-?york|sfns", re.I)
OFL = re.compile(r"Open Font License|openfontlicense\.org|scripts\.sil\.org/OFL", re.I)
APACHE_TEXT = re.compile(r"Apache License\s+Version 2\.0, January 2004", re.I)
OFL_TEXT = re.compile(r"SIL OPEN FONT LICENSE Version 1\.1", re.I)

# The fonts the kit ships, all under the SIL OFL: family|copyright holder.
KIT_FONTS = {"InterVariable": "Inter Variable|The Inter Project Authors",
             "roboto-": "Roboto|The Roboto Project Authors"}

# What sf_icons.py writes, and what the SF Symbols app exports.
SF_ICONS_MARK = "SF Symbols drawn on this Mac"
SF_RULE = re.compile(r"""data-sf-symbol=\\?["']([a-z0-9.]+)\\?["']\][^{}]*\{[^{}]*data:image/png;base64""")
SF_TEMPLATE = re.compile(r"(Template v\.\d|Generated from \S+).{0,4000}?(Requires Xcode|SF Symbols|"
                         r"Apple Native CoreSVG)|(Requires Xcode|Apple Native CoreSVG).{0,4000}?"
                         r"(Template v\.\d|Generated from \S+)", re.S)
SF_MODIFIERS = {"fill", "circle", "square", "slash", "rectangle", "badge", "plus", "minus",
                "left", "right", "up", "down", "forward", "backward", "bubble", "crop", "stack",
                "xmark", "checkmark", "and", "inset", "filled", "portrait", "landscape", "dashed",
                "trianglebadge", "exclamationmark", "questionmark", "ellipsis", "rtl", "ar", "hi"}
# Apple Design Resources name renderings by appearance and state.
KIT_RENDERING = re.compile(r"(^|[/_ ])(Light|Dark)_(Idle|Pressed|Disabled|Selected|Hover|Focused|"
                           r"Highlighted|Is On|Is Off)|UI Kit|Apple Design Resources", re.I)

DATA_URI = re.compile(r"data:([a-z]+/[a-z0-9.+-]+)(?:;[a-z0-9=.-]+)*;base64,([A-Za-z0-9+/=\s]{40,})", re.I)
APPLE_HOTLINK = re.compile(r"https?://(?:[a-z0-9-]+\.)*(?:apple\.com|cdn-apple\.com|mzstatic\.com)"
                           r"/[^\s\"')<>]+?\.(?:png|jpe?g|gif|webp|svg|heic|woff2?|ttf|otf|mp4|mov)\b", re.I)
SF_WEBFONT = re.compile(r"https?://[^\s\"')<>]*(?:sf-?pro|sfpro|sf-?compact|sfns|san-?francisco)"
                        r"[^\s\"')<>]*", re.I)
MATERIAL_INLINE = re.compile(r"<svg\b[^>]*\bdata-icon=[\"']([a-z0-9_]+)[\"']")


# ---------------------------------------------------------------- fonts

def font_names(data):
    """{nameID: text} from a font's name table, or None if it can't be read."""
    try:
        from fontTools.ttLib import TTFont
        font = TTFont(io.BytesIO(data), fontNumber=0, lazy=True)
        table = font["name"]
        names = {i: table.getDebugName(i) for i in (0, 1, 4, 7, 8, 9, 13, 14)}
        return {i: v for i, v in names.items() if v}
    except Exception:  # no fontTools, no brotli for WOFF2, or not a font
        pass
    return _sfnt_names(data)


def _sfnt_names(data):
    """The name table of a TrueType/OpenType/WOFF font, without fontTools."""
    try:
        if data[:4] == b"wOFF":
            for i in range(struct.unpack(">H", data[12:14])[0]):
                tag, off, clen, olen, _ = struct.unpack(">4sIIII", data[44 + 20 * i:64 + 20 * i])
                if tag == b"name":
                    raw = data[off:off + clen]
                    return _name_table(zlib.decompress(raw) if clen < olen else raw)
            return None
        base = struct.unpack(">I", data[12:16])[0] if data[:4] == b"ttcf" else 0
        if data[base:base + 4] not in (b"\x00\x01\x00\x00", b"OTTO", b"true"):
            return None
        for i in range(struct.unpack(">H", data[base + 4:base + 6])[0]):
            rec = base + 12 + 16 * i
            tag, _, off, length = struct.unpack(">4sIII", data[rec:rec + 16])
            if tag == b"name":
                return _name_table(data[off:off + length])
    except (struct.error, zlib.error, IndexError):
        return None
    return None


def _name_table(t):
    _, count, strings = struct.unpack(">HHH", t[:6])
    out = {}
    for i in range(count):
        pid, _, _, nid, length, off = struct.unpack(">HHHHHH", t[6 + 12 * i:18 + 12 * i])
        raw = t[strings + off:strings + off + length]
        text = raw.decode("utf-16-be", "replace") if pid in (0, 3) else raw.decode("latin-1")
        if nid not in out or pid == 3:
            out[nid] = text
    return out


def holder(copyright_line):
    """'Copyright 2016 The Inter Project Authors (url)' -> 'The Inter Project Authors'."""
    m = re.search(r"(?:Copyright|\(c\)|©)\s*(?:\(c\)|©)?\s*[\d\s,\-–]*\s*([^()\n]+?)\s*(?:\(|\.?$)",
                  copyright_line or "", re.I)
    return m.group(1).strip() if m else ""


def classify_font(data, name):
    """(kind, detail): kind is apple | ofl | apache | unknown."""
    names = font_names(data)
    if names is None:
        if APPLE_FONT_FILE.search(name):
            return "apple", "named like one of Apple's fonts"
        return "unknown", "its name table couldn't be read (pip install fonttools brotli reads WOFF2)"
    family = names.get(1) or names.get(4) or "?"
    maker = " ".join(names.get(i, "") for i in (0, 7, 8, 9))
    if APPLE_FAMILY.search(family) or re.search(r"\bApple\b", maker):
        return "apple", f"{family}, {(names.get(0) or names.get(8) or 'Apple').strip()[:60]}"
    licence = f"{names.get(13, '')} {names.get(14, '')}"
    if OFL.search(licence):
        return "ofl", f"{family}|{holder(names.get(0))}"
    if re.search(r"Apache", licence):
        return "apache", family
    return "unknown", f"{family}: no licence in its name table"


# ---------------------------------------------------------------- the kit

def sha(data):
    return hashlib.sha256(data).hexdigest()


def kit_index():
    """sha256 -> path in the skills, for every file a generator copies."""
    index = {}
    for skill in ("ui-kit-for-apple-platforms", "ui-kit-for-android", "design-workflow"):
        root = os.path.join(SKILLS, skill)
        for dirpath, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for f in files:
                if f.endswith((".css", ".js", ".json", ".txt", ".md")) or f.endswith(FONT_EXT) \
                        or f == "LICENSE":
                    p = os.path.join(dirpath, f)
                    with open(p, "rb") as fh:
                        index.setdefault(sha(fh.read()), os.path.relpath(p, SKILLS))
    return index


def material_paths():
    try:
        with open(os.path.join(SKILLS, "ui-kit-for-android", "icons", "material-symbols.json"),
                  encoding="utf-8") as fh:
            icons = json.load(fh)
        return {d for v in icons.values() for d in v.values()}
    except (OSError, ValueError):
        return set()


def sf_names():
    try:
        sys.path.insert(0, os.path.join(SKILLS, "hig-guide"))
        import sf_symbols
        db = sf_symbols.load()
        return set(db["symbols"]) | set(db["aliases"]) if db else None
    except Exception:
        return None


def looks_like_sf_png(name, known):
    if not name.lower().endswith(".png"):
        return False
    stem = name[:-4]
    if known is not None:
        return stem in known
    parts = stem.split(".")
    return (len(parts) > 1 and all(re.fullmatch(r"[a-z0-9]+", p) for p in parts)
            and any(p in SF_MODIFIERS for p in parts[1:]))


# ---------------------------------------------------------------- git

class Git:
    def __init__(self, root):
        self.root = root
        self.ok = subprocess.run(["git", "-C", root, "rev-parse", "--is-inside-work-tree"],
                                 capture_output=True, text=True).returncode == 0 \
            if self._has_git() else False
        self.patterns = []
        gi = os.path.join(root, ".gitignore")
        if os.path.isfile(gi):
            for line in open(gi, encoding="utf-8", errors="replace"):
                line = line.strip()
                if line and not line.startswith(("#", "!")):
                    self.patterns.append(line)

    @staticmethod
    def _has_git():
        try:
            subprocess.run(["git", "--version"], capture_output=True)
            return True
        except OSError:
            return False

    def ignored(self, rel):
        if self.ok:
            r = subprocess.run(["git", "-C", self.root, "check-ignore", "-q", "--", rel])
            if r.returncode in (0, 1):
                return r.returncode == 0
        parts = rel.split("/")
        for p in self.patterns:
            anchored = p.startswith("/")
            pat = p.strip("/")
            if p.endswith("/"):
                if any(fnmatch.fnmatch("/".join(parts[:i]), pat) or
                       (not anchored and fnmatch.fnmatch(parts[i - 1], pat))
                       for i in range(1, len(parts))):
                    return True
            elif fnmatch.fnmatch(rel, pat) or (not anchored and "/" not in pat
                                               and fnmatch.fnmatch(parts[-1], pat)):
                return True
        return False

    def tracked(self, rel):
        if not self.ok:
            return False
        return subprocess.run(["git", "-C", self.root, "ls-files", "--error-unmatch", "--", rel],
                              capture_output=True).returncode == 0


# ---------------------------------------------------------------- the audit

class Audit:
    def __init__(self, root, purpose, platform):
        self.root, self.purpose, self.platform = root, purpose, platform
        self.git = Git(root)
        self.items, self.inline = [], []
        self.fails, self.warns, self.oks = [], [], []
        self.kit = kit_index()
        self.material = material_paths()
        self.known_sf = sf_names()
        self.declared = self._declared()
        self.manifest = self._generator_manifest()
        self.licences = {"apache": [], "ofl": []}  # rel paths of licence texts found
        self.hashes = {}
        self.tag = None
        self.kit_fonts = {h: KIT_FONTS[k] for h, p in self.kit.items()
                          for k in KIT_FONTS if os.path.basename(p).startswith(k)}

    # -- inputs

    def _declared(self):
        p = os.path.join(self.root, "assets.json")
        if not os.path.isfile(p):
            return {}
        try:
            data = json.load(open(p, encoding="utf-8"))
        except ValueError as exc:
            self.fails.append(f"assets.json isn't valid JSON: {exc}")
            return {}
        return {k.strip("./"): v for k, v in data.items() if isinstance(v, dict)}

    def _generator_manifest(self):
        p = os.path.join(self.root, "vendor", "manifest.json")
        try:
            return json.load(open(p, encoding="utf-8")).get("files", {})
        except (OSError, ValueError, AttributeError):
            return {}

    # -- verdicts

    def apple_restricted(self, rel, what):
        """SF Pro or SF Symbols from the user's own Mac."""
        apple = self.platform in APPLE_PLATFORMS
        where = rel if rel else "?"
        if self.purpose == "publish":
            self.fails.append(f"{where}: {what}. Apple's licence doesn't allow passing it on; "
                              f"remove it before publishing (the design keeps working without it)")
            return "fail"
        if not apple and self.platform != "cross":
            plat = self.platform or "unknown"
            self.fails.append(f"{where}: {what} in a {plat} design. Apple's licence covers mockups "
                              f"of apps for Apple's platforms only; remove it"
                              + ("" if self.platform else ", or pass --platform if this is an "
                                 "Apple-platform design"))
            return "fail"
        if self.git.tracked(rel):
            self.fails.append(f"{where}: {what}, committed to git. Take it out of the repository "
                              f"(git rm --cached) and keep it ignored")
            return "fail"
        if not self.git.ignored(rel):
            self.fails.append(f"{where}: {what}, not in .gitignore, so the next commit takes it "
                              f"along. Add it to the design's .gitignore")
            return "fail"
        note = " -- keep the Apple builds' copy to Apple's platforms" if self.platform == "cross" else ""
        self.warns.append(f"{where}: {what}. Fine in this mockup and ignored by git; it fails "
                          f"--purpose publish, so it stays on your machine{note}")
        return "warn"

    def apple_asset(self, rel, what):
        """Apple's design-resource renderings or hot-linked Apple assets."""
        if self.purpose == "publish" or (rel and not self.git.ignored(rel) and what.startswith("an image")):
            self.fails.append(f"{rel}: {what}. It's Apple's to distribute, not this design's; "
                              f"remove it or replace it with your own")
            return "fail"
        self.warns.append(f"{rel}: {what}. Fails --purpose publish")
        return "warn"

    def unknown(self, rel, what):
        if self.purpose == "publish":
            self.fails.append(f"{rel}: {what}, origin unknown. Record its source and licence in "
                              f"assets.json, or remove it")
            return "fail"
        self.warns.append(f"{rel}: {what}, origin unknown; record it in assets.json before publishing")
        return "warn"

    def needs_licence(self, what, kind, rel, holder_name=None, prefer=None):
        found = self.licences[kind]
        if kind == "ofl" and holder_name:
            found = [p for p in found if holder_name.lower() in self._text(p).lower()]
        if found:
            named = [p for p in found if prefer and prefer.lower() in p.lower()]
            return (named or found)[0]
        msg = (f"{rel}: {what} without its licence. "
               + {"ofl": "The SIL Open Font License has to travel with the font: copy its "
                         "LICENSE file next to it",
                  "apache": "The Apache 2.0 licence has to travel with it: copy the licence "
                            "text into the design (new_project.py writes vendor/LICENSE-onplatform.txt)"}[kind])
        (self.fails if self.purpose == "publish" else self.warns).append(msg)
        return None

    def _text(self, rel):
        try:
            return open(os.path.join(self.root, rel), encoding="utf-8", errors="replace").read()
        except OSError:
            return ""

    # -- walking

    def files(self):
        out, skipped = [], []
        for dirpath, dirs, names in os.walk(self.root):
            for d in list(dirs):
                if d in SKIP_DIRS:
                    dirs.remove(d)
                    if d == "node_modules":
                        skipped.append(os.path.relpath(os.path.join(dirpath, d), self.root))
                elif d == ".visual-review":
                    # Screenshots render_review.py and stress_test.py took of
                    # this design: review output, not something it ships.
                    dirs.remove(d)
                    if self.purpose == "publish":
                        self.warns.append(".visual-review/: the review tools' screenshots of this design, "
                                          "not audited. Leave them out of what you publish; the "
                                          "scaffold's .gitignore keeps them out of commits")
            for n in names:
                if n not in IGNORE_FILES:
                    out.append(os.path.relpath(os.path.join(dirpath, n), self.root).replace(os.sep, "/"))
        for s in skipped:
            self.warns.append(f"{s}/: not audited. Its packages carry their own licences; check "
                              f"them with your package manager's licence report")
        return sorted(out)

    def run(self):
        files = self.files()
        blobs = {}
        for rel in files:
            with open(os.path.join(self.root, rel), "rb") as fh:
                blobs[rel] = fh.read()
            self.hashes[sha(blobs[rel])] = rel
            text = blobs[rel][:400000].decode("utf-8", "replace")
            if APACHE_TEXT.search(text):
                self.licences["apache"].append(rel)
            if OFL_TEXT.search(text):
                self.licences["ofl"].append(rel)
        for rel in files:
            self.item(rel, blobs[rel])
        for rel in self.declared:
            if rel not in blobs:
                self.warns.append(f"assets.json lists {rel}, which isn't in the design")
        return self

    def record(self, rel, data, kind, origin, licence, status, licence_file=None):
        self.items.append({"path": rel, "sha256": sha(data), "bytes": len(data), "type": kind,
                           "origin": origin, "licence": licence, "licence_file": licence_file,
                           "status": status})

    def item(self, rel, data):
        name = os.path.basename(rel)
        low = name.lower()
        kit = self.kit.get(sha(data)) or (self.manifest.get(rel) or {}).get("origin")
        if rel == "assets.json" or rel == "vendor/manifest.json":
            self.record(rel, data, "record", "this design", "-", "ok")
            return
        if low.endswith(FONT_EXT):
            self.font(rel, data, name, kit)
            return
        if kit:
            self.kit_file(rel, data, kit)
            return
        if low.endswith(".svg"):
            # A drawing: Apple's if it's an SF Symbols export, otherwise
            # whoever made it, which assets.json has to say.
            if self.scan(rel, data) == "ok":
                self.image(rel, data, name)
            return
        if low.endswith(IMAGE_EXT):
            self.image(rel, data, name)
            return
        if low.endswith(TEXT_EXT) or self._is_text(data):
            self.tag = None
            status = self.scan(rel, data)
            declared = self.declared.get(rel, {})
            origin, licence = self.tag or (declared.get("source", "this design"),
                                           declared.get("licence", "this design's own"))
            self.record(rel, data, "text", origin, licence, status)
            return
        declared = self.declared.get(rel, {})
        if declared.get("licence"):
            self.record(rel, data, "other", declared.get("source", "declared"), declared["licence"], "ok")
            return
        status = self.unknown(rel, "a binary file")
        self.record(rel, data, "other", "unknown", "unknown", status)

    @staticmethod
    def _is_text(data):
        return b"\x00" not in data[:4096]

    def font(self, rel, data, name, kit, embedded_in=None):
        kind, detail = classify_font(data, name)
        if kind == "unknown" and (kit or sha(data) in self.kit_fonts):
            # One of the kit's own fonts, known by its hash even where the
            # name table can't be read.
            kind, detail = "ofl", self.kit_fonts.get(sha(data), "?|")
        where = f"{embedded_in} (embedded font)" if embedded_in else rel
        if kind == "apple":
            status = self.apple_restricted(embedded_in or rel, f"Apple's font {detail}"
                                           + (" embedded in the page" if embedded_in else ""))
            if not embedded_in:
                self.record(rel, data, "font", "Apple", "Apple SF Pro licence (not redistributable)", status)
            return
        if kind == "ofl":
            family, who = detail.split("|", 1)
            lic = self.needs_licence(f"{family} (SIL OFL)", "ofl", where, who or family)
            if not embedded_in:
                self.record(rel, data, "font", kit or family, "OFL-1.1", "ok" if lic else "warn", lic)
            return
        if kind == "apache":
            lic = self.needs_licence(f"{detail} (Apache 2.0)", "apache", where)
            if not embedded_in:
                self.record(rel, data, "font", kit or detail, "Apache-2.0", "ok" if lic else "warn", lic)
            return
        if embedded_in:
            digest = sha(data)
            if digest in self.hashes:
                return  # the same file is in the design and gets its own verdict
            self.unknown(embedded_in, f"an embedded font ({detail})")
            return
        declared = self.declared.get(rel, {})
        if declared.get("licence"):
            self.record(rel, data, "font", declared.get("source", "declared"), declared["licence"], "ok")
            return
        status = self.unknown(rel, f"a font ({detail})")
        self.record(rel, data, "font", "unknown", "unknown", status)

    def image(self, rel, data, name):
        if KIT_RENDERING.search(rel):
            status = self.apple_asset(rel, "an image named like Apple's design-resource renderings")
            self.record(rel, data, "image", "Apple Design Resources?", "Apple (not redistributable)", status)
            return
        if looks_like_sf_png(name, self.known_sf):
            status = self.apple_restricted(rel, f"an SF Symbol drawing ({name[:-4]})")
            self.record(rel, data, "image", "SF Symbols", "Apple SF Symbols licence", status)
            return
        declared = self.declared.get(rel, {})
        if declared.get("licence"):
            self.record(rel, data, "image", declared.get("source", "declared"), declared["licence"], "ok")
            return
        status = self.unknown(rel, "an image")
        self.record(rel, data, "image", "unknown", "unknown", status)

    def kit_file(self, rel, data, kit):
        """A file a generator copied from the skills: this kit's Apache-2.0 work."""
        base = os.path.basename(kit)
        if base.startswith("LICENSE"):
            self.record(rel, data, "licence", kit, "licence text", "ok")
            return
        lic = self.needs_licence(f"the kit's {base}", "apache", rel, prefer="onplatform")
        self.record(rel, data, "kit", kit, "Apache-2.0", "ok" if lic else "warn", lic)

    def scan(self, rel, data):
        """What a text file carries inside it: drawings, fonts, images, links."""
        text = data.decode("utf-8", "replace")
        status = "ok"
        if os.path.basename(rel) in (".gitignore", "NOTICES.md"):
            return status  # they name what they keep out; they don't hold it
        sf_rules = len(SF_RULE.findall(text))
        if sf_rules or (SF_ICONS_MARK in text and rel.endswith((".css", ".html", ".htm"))):
            status = self.apple_restricted(rel, f"{sf_rules or 'some'} SF Symbol drawing(s) from your Mac")
            self.tag = ("SF Symbols, drawn on your Mac", "Apple SF Symbols licence")
        if SF_TEMPLATE.search(text):
            status = self.apple_restricted(rel, "an SF Symbols template exported from Apple's app")
            self.tag = ("SF Symbols app", "Apple SF Symbols licence")
        for m in APPLE_HOTLINK.finditer(text):
            if self.apple_asset(rel, f"a hot-link to Apple's {m.group(0)[:90]}") == "fail":
                status = "fail"
        for m in SF_WEBFONT.finditer(text):
            self.fails.append(f"{rel}: loads SF Pro from {m.group(0)[:90]}. Apple doesn't license "
                              f"SF Pro for the web; a host serving it is redistributing it")
            status = "fail"
        for m in DATA_URI.finditer(text):
            mime, payload = m.group(1).lower(), m.group(2)
            context = text[max(0, m.start() - 300):m.start()]
            if "data-sf-symbol" in context:
                continue  # counted with the SF Symbol rules above
            try:
                blob = base64.b64decode(re.sub(r"\s", "", payload), validate=False)
            except ValueError:
                continue
            if mime.startswith("font/") or "font" in mime or "woff" in mime or \
                    (mime == "application/octet-stream" and "@font-face" in context):
                self.font(rel, blob, "", None, embedded_in=rel)
            elif mime.startswith("image/") and len(blob) > 600:
                if sha(blob) in self.hashes:
                    continue  # the same image is a file in the design and has its own verdict
                if self.purpose == "publish":
                    self.fails.append(f"{rel}: an embedded {mime} ({len(blob) // 1024 or 1} KB), "
                                      f"origin unknown. Use a file listed in assets.json instead")
                    status = "fail"
                else:
                    self.warns.append(f"{rel}: an embedded {mime} ({len(blob) // 1024 or 1} KB), "
                                      f"origin unknown; record it before publishing")
        icons = set(MATERIAL_INLINE.findall(text))
        if not icons and self.material and "<path" in text:
            icons = {d for d in re.findall(r'\bd="([^"]{40,})"', text) if d in self.material}
        if icons:
            lic = self.needs_licence(f"{len(icons)} Material Symbols icon(s) (Apache 2.0, Google)",
                                     "apache", rel, prefer="material")
            self.inline.append({"path": rel, "what": "Material Symbols", "count": len(icons),
                                "licence": "Apache-2.0", "licence_file": lic})
        return status

    # -- output

    def report(self, quiet=False):
        kinds = {}
        for it in self.items:
            kinds[it["type"]] = kinds.get(it["type"], 0) + 1
        plat = self.platform or "unknown platform"
        print(f"{len(self.items)} files ({', '.join(f'{v} {k}' for k, v in sorted(kinds.items()))}) "
              f"-- {plat}, purpose {self.purpose}")
        if not quiet:
            for it in self.items:
                if it["type"] in ("font", "image", "other") or it["status"] != "ok":
                    lic = f" [{it['licence_file']}]" if it.get("licence_file") else ""
                    print(f"  {it['status']:<4} {it['path']}: {it['origin']}, {it['licence']}{lic}")
            for inl in self.inline:
                print(f"  {'ok' if inl['licence_file'] else 'warn':<4} {inl['path']}: {inl['count']} "
                      f"{inl['what']} inline, {inl['licence']}"
                      + (f" [{inl['licence_file']}]" if inl["licence_file"] else ""))
        for m in dict.fromkeys(self.warns):
            print(f"  warn {m}")
        for m in dict.fromkeys(self.fails):
            print(f"  FAIL {m}")
        if self.fails:
            print(f"\n{len(set(self.fails))} problem(s): not ready to "
                  + ("publish." if self.purpose == "publish" else "share."))
            return 1
        print("\nnothing found that can't go with this design"
              + (" to wherever it's published." if self.purpose == "publish"
                 else "; run with --purpose publish before it leaves your hands."))
        return 0

    def manifest_json(self):
        return {"purpose": self.purpose, "platform": self.platform, "files": self.items,
                "inline": self.inline, "problems": list(dict.fromkeys(self.fails)),
                "warnings": list(dict.fromkeys(self.warns))}


def detect_platform(root):
    """The platform new_project.py recorded: DESIGN.md's Platform mode, or README's kind."""
    for name, pattern in (("DESIGN.md", r"## Platform mode\s+`([a-z]+)`"),
                          ("README.md", r"kind:\s*`([a-z]+)`")):
        path = os.path.join(root, name)
        if os.path.isfile(path):
            m = re.search(pattern, open(path, encoding="utf-8", errors="replace").read())
            if m:
                return m.group(1)
    index = os.path.join(root, "index.html")
    if os.path.isfile(index):
        html = open(index, encoding="utf-8", errors="replace").read()
        if "material-components.css" in html:
            return "android"
        if "macos-components.css" in html:
            return "macos"
        if "ipados-components.css" in html:
            return "ipados"
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("design", help="the design folder")
    ap.add_argument("--purpose", choices=["mockup", "publish"], default="mockup")
    ap.add_argument("--platform", help="the platform the design is for, when DESIGN.md "
                    "doesn't say: ios, ipados, macos, watchos, visionos, tvos, android, web")
    ap.add_argument("--manifest", metavar="FILE", help="also write every file, its origin and "
                    "licence, as JSON")
    ap.add_argument("-q", "--quiet", action="store_true", help="only problems and warnings")
    a = ap.parse_args()
    root = os.path.abspath(a.design)
    if not os.path.isdir(root):
        sys.exit(f"not a folder: {a.design}")
    platform = (a.platform or detect_platform(root) or "").lower() or None
    audit = Audit(root, a.purpose, platform).run()
    code = audit.report(a.quiet)
    if a.manifest:
        with open(a.manifest, "w", encoding="utf-8") as fh:
            json.dump(audit.manifest_json(), fh, indent=1)
            fh.write("\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
