#!/usr/bin/env python3
"""The plugin holds together: manifests, commands, agents, hooks.

- The marketplace and plugin manifests agree with each other and with the
  installer's version, and `claude plugin validate --strict`-level problems
  are absent (run when the claude command is installed; CI installs it).
- Every command (skills/*/SKILL.md) and agent (agents/*.md) has the
  frontmatter it needs, and every ${CLAUDE_PLUGIN_ROOT} path any of them, or
  hooks.json, names exists.
- The SwiftUI hook reports a seeded file's violations, says nothing about a
  clean one, a non-Swift file or a repeat, and never fails.
- The commit guard denies a commit or push that would take SF Pro along,
  allows it once git ignores the font, ignores commands that aren't commits
  or pushes, finds the repository through `git -C` and `cd`, and turns off
  with ONPLATFORM_COMMIT_GUARD=off.

Needs fontTools, for the stand-in SF Pro.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(__file__))
from test_check_distribution import fake_font  # noqa: E402

SCAFFOLD = os.path.join(ROOT, ".claude", "skills", "design-workflow", "new_project.py")
FAILED = []


def expect(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'} {label}")
    if not ok:
        FAILED.append(label)
        if detail:
            print("       " + str(detail).strip().replace("\n", "\n       ")[-1500:])


def frontmatter(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        return None, text
    fields = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            fields[k.strip()] = v.strip().strip('"')
    return fields, m.group(2)


def plugin_paths(text):
    return re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}(/[\w./-]+)", text)


def hook(script, event, env=None):
    e = dict(os.environ, CLAUDE_PLUGIN_ROOT=ROOT, **(env or {}))
    p = subprocess.run([sys.executable, os.path.join(ROOT, "hooks", script)],
                       input=json.dumps(event) if isinstance(event, dict) else event,
                       capture_output=True, text=True, env=e)
    return p.returncode, p.stdout.strip()


def git(cwd, *args):
    return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, check=True)


def main():
    print("manifests:")
    plugin = json.load(open(os.path.join(ROOT, ".claude-plugin", "plugin.json")))
    market = json.load(open(os.path.join(ROOT, ".claude-plugin", "marketplace.json")))
    entry = next((p for p in market["plugins"] if p["name"] == plugin["name"]), None)
    expect("the marketplace lists the plugin, from this repository", entry and entry["source"] == "./",
           market)
    expect("the version lives in plugin.json only", entry and "version" not in entry)
    installer = re.search(r'^VERSION="v([^"]+)"', open(os.path.join(ROOT, "install.sh")).read(), re.M)
    expect("plugin.json's version matches install.sh's",
           installer and installer.group(1) == plugin["version"],
           f"plugin.json {plugin['version']}, install.sh {installer and installer.group(1)}")
    expect("the five skills load from .claude/skills",
           plugin.get("skills") == ["./.claude/skills/"]
           and all(os.path.isfile(os.path.join(ROOT, ".claude", "skills", s, "SKILL.md"))
                   for s in ("hig-guide", "design-workflow", "ui-kit-for-apple-platforms", "motion-for-apple-platforms",
                             "ui-kit-for-android")))

    # Claude Code cuts a skill's description at 1,536 characters in the list
    # it chooses skills from, so anything past that never reaches the model.
    for d in sorted(os.listdir(os.path.join(ROOT, ".claude", "skills"))):
        fields, _ = frontmatter(os.path.join(ROOT, ".claude", "skills", d, "SKILL.md"))
        n = len((fields or {}).get("description", ""))
        expect(f"{d}'s description fits the 1,536-character listing ({n})", 0 < n <= 1536)

    print("commands and agents:")
    named = []
    commands = sorted(os.listdir(os.path.join(ROOT, "skills")))
    for c in commands:
        path = os.path.join(ROOT, "skills", c, "SKILL.md")
        fields, body = frontmatter(path)
        ok = bool(fields and fields.get("description") and fields.get("argument-hint")
                  and fields.get("disable-model-invocation") == "true")
        expect(f"/onplatform:{c} has a description, an argument hint, and runs only when called", ok, fields)
        named += plugin_paths(body)
    for a in sorted(os.listdir(os.path.join(ROOT, "agents"))):
        fields, body = frontmatter(os.path.join(ROOT, "agents", a))
        supported = {"name", "description", "model", "effort", "maxTurns", "tools",
                     "disallowedTools", "skills", "memory", "background", "isolation", "color"}
        # The reviewer and the critic report; only the designer writes.
        writes = fields and fields.get("name") == "designer"
        ok = bool(fields and fields.get("name") and fields.get("description")
                  and fields.get("tools") and set(fields) <= supported
                  and (writes or ("Edit" not in fields["tools"] and "Write" not in fields["tools"])))
        expect(f"agent onplatform:{fields and fields.get('name')}: named, described, "
               + ("can write the design" if writes else "read-only"), ok, fields)
        named += plugin_paths(body)
    hooks_text = open(os.path.join(ROOT, "hooks", "hooks.json")).read()
    json.loads(hooks_text)
    named += plugin_paths(hooks_text)
    missing = sorted({p for p in named if not os.path.exists(ROOT + p)})
    expect(f"all {len(set(named))} ${{CLAUDE_PLUGIN_ROOT}} paths exist", not missing, missing)

    if shutil.which("claude"):
        p = subprocess.run(["claude", "plugin", "validate", ROOT], capture_output=True, text=True)
        expect("claude plugin validate passes", p.returncode == 0 and "Validation passed" in p.stdout,
               p.stdout + p.stderr)
    else:
        print("  skip claude plugin validate (the claude command isn't installed)")

    print("eval cases:")
    # An unquoted YAML value holding ": " reads as a second key, and the
    # case silently fails to load when the suite runs.
    bad = []
    for d in sorted(os.listdir(os.path.join(ROOT, "evals"))):
        for name in ("case.yaml", "prompt.md"):
            path = os.path.join(ROOT, "evals", d, name)
            if not os.path.isfile(path):
                continue
            text = open(path, encoding="utf-8").read()
            head = text.split("---")[1] if name == "prompt.md" else text
            for line in head.splitlines():
                m = re.match(r"^\s*[\w-]+: (.*)$", line)
                if m and not m.group(1).startswith(("\"", "'", "[", "{")) and ": " in m.group(1):
                    bad.append(f"{d}/{name}: {line.strip()[:60]}")
    cases = [d for d in os.listdir(os.path.join(ROOT, "evals"))
             if os.path.isfile(os.path.join(ROOT, "evals", d, "prompt.md"))]
    expect(f"all {len(cases)} eval cases parse (no unquoted ': ')", cases and not bad, bad)
    for d in cases:
        graders = os.path.join(ROOT, "evals", d, "graders")
        expect(f"eval {d} has graders", os.path.isdir(graders) and os.listdir(graders))

    print("SwiftUI hook:")
    data = tempfile.mkdtemp(prefix="hig-data-")
    seeded = os.path.join(ROOT, "scripts", "eval", "reallife", "fixture", "ContentView.swift")
    event = {"session_id": "t1", "cwd": ROOT, "tool_name": "Edit", "tool_input": {"file_path": seeded}}
    rc, out = hook("swiftui_check.py", event, {"CLAUDE_PLUGIN_DATA": data})
    ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"] if out else ""
    expect("a seeded file's violations come back, violations first",
           rc == 0 and "violation(s)" in ctx and ctx.split("\n")[1].startswith("- violation"), out)
    rc, out = hook("swiftui_check.py", event, {"CLAUDE_PLUGIN_DATA": data})
    expect("the same findings again stay quiet", rc == 0 and out == "", out)
    clean = os.path.join(data, "Clean.swift")
    open(clean, "w").write('import SwiftUI\n\nstruct V: View {\n    var body: some View {\n'
                           '        Text("Hello").font(.body)\n    }\n}\n')
    rc, out = hook("swiftui_check.py", {"tool_input": {"file_path": clean}})
    expect("a clean file stays quiet", rc == 0 and out == "", out)
    rc, out = hook("swiftui_check.py", {"tool_input": {"file_path": os.path.join(ROOT, "README.md")}})
    expect("a non-Swift file stays quiet", rc == 0 and out == "", out)
    rc, out = hook("swiftui_check.py", "not json")
    expect("bad input never fails the edit", rc == 0 and out == "", out)
    rc, out = hook("swiftui_check.py", dict(event, session_id="t2"), {"ONPLATFORM_SWIFTUI_HOOK": "off"})
    expect("ONPLATFORM_SWIFTUI_HOOK=off turns it off", rc == 0 and out == "", out)
    shutil.rmtree(data, ignore_errors=True)

    print("commit guard:")
    base = tempfile.mkdtemp(prefix="hig-guard-")
    try:
        repo = os.path.join(base, "app")
        sf = fake_font(os.path.join(base, "SF-Pro.ttf"), "SF Pro",
                       "Copyright © 2015-2026 Apple Inc. All rights reserved.")
        subprocess.run([sys.executable, SCAFFOLD, "--name", "Pantry", "--brand", "#C1552E",
                        "--kind", "ios", "--model", "tabs", "--sf", sf,
                        "-o", os.path.join(repo, "design")], check=True, capture_output=True)
        git(base, "init", "-q", repo)
        # The scaffold keeps SF Pro out of git; this repo forgets to.
        open(os.path.join(repo, "design", ".gitignore"), "w").write("")
        commit = {"cwd": repo, "tool_name": "Bash", "tool_input": {"command": "git commit -am wip"}}
        rc, out = hook("design_guard.py", commit)
        decision = json.loads(out)["hookSpecificOutput"] if out else {}
        expect("a commit that would take SF Pro along is denied",
               rc == 0 and decision.get("permissionDecision") == "deny"
               and "SF-Pro.ttf" in decision.get("permissionDecisionReason", ""), out)
        rc, out = hook("design_guard.py", dict(commit, tool_input={"command": "git -c core.pager=cat push origin main"}))
        expect("so is a push", rc == 0 and '"deny"' in out, out)
        rc, out = hook("design_guard.py", dict(commit, cwd=base,
                                               tool_input={"command": f"git -C {repo} commit -m x"}))
        expect("git -C <repo> is followed to the repository", rc == 0 and '"deny"' in out, out)
        rc, out = hook("design_guard.py", dict(commit, cwd=base,
                                               tool_input={"command": "cd app && git commit -m x"}))
        expect("so is a leading cd", rc == 0 and '"deny"' in out, out)
        rc, out = hook("design_guard.py", dict(commit, tool_input={"command": "git status"}))
        expect("git status passes untouched", rc == 0 and out == "", out)
        rc, out = hook("design_guard.py", commit, {"ONPLATFORM_COMMIT_GUARD": "off"})
        expect("ONPLATFORM_COMMIT_GUARD=off turns it off", rc == 0 and out == "", out)
        open(os.path.join(repo, "design", ".gitignore"), "w").write("vendor/fonts/SF-Pro.ttf\n")
        rc, out = hook("design_guard.py", commit)
        expect("once git ignores the font, the commit goes ahead", rc == 0 and out == "", out)
        git(repo, "add", "-f", "design/vendor/fonts/SF-Pro.ttf")
        rc, out = hook("design_guard.py", commit)
        expect("a font already staged is caught even though it's ignored", rc == 0 and '"deny"' in out, out)
        rc, out = hook("design_guard.py", dict(commit, cwd=base))
        expect("outside a repository it stays out of the way", rc == 0 and out == "", out)
    finally:
        shutil.rmtree(base, ignore_errors=True)

    print("GitHub Action:")
    action = os.path.join(ROOT, "scripts", "action_checks.py")
    work = tempfile.mkdtemp(prefix="hig-action-")
    try:
        os.makedirs(os.path.join(work, "clean"))
        open(os.path.join(work, "clean", "V.swift"), "w").write(
            'import SwiftUI\n\nstruct V: View {\n    var body: some View {\n'
            '        Text("Hello").font(.body)\n    }\n}\n')
        subprocess.run([sys.executable, SCAFFOLD, "--name", "Pantry", "--brand", "#C1552E", "--kind",
                        "android", "-o", os.path.join(work, "design")], check=True, capture_output=True)

        def act(**env):
            e = {k: v for k, v in os.environ.items() if not k.startswith("ONPLATFORM_")}
            e.update(env, GITHUB_STEP_SUMMARY=os.path.join(work, "summary.md"))
            return subprocess.run([sys.executable, action], capture_output=True, text=True, env=e)

        p = act(ONPLATFORM_SWIFTUI=os.path.join(work, "clean"), ONPLATFORM_DESIGNS=os.path.join(work, "design"))
        expect("clean SwiftUI and a fresh design pass", p.returncode == 0, p.stdout + p.stderr)
        expect("...and the run gets a summary",
               "## onplatform checks" in open(os.path.join(work, "summary.md")).read())
        seeded_dir = os.path.join("scripts", "eval", "reallife", "fixture")
        p = subprocess.run([sys.executable, action], capture_output=True, text=True, cwd=ROOT,
                           env=dict({k: v for k, v in os.environ.items() if not k.startswith("ONPLATFORM_")},
                                    ONPLATFORM_SWIFTUI=seeded_dir))
        expect("the seeded app fails, each finding annotated at its file and line",
               p.returncode == 1 and re.search(r"^::error file=scripts/eval/reallife/fixture/\w+\.swift,"
                                               r"line=\d+,title=HIG violation", p.stdout, re.M), p.stdout[-800:])
        p = act(ONPLATFORM_SWIFTUI=os.path.join(ROOT, seeded_dir), ONPLATFORM_FAIL_ON="none")
        expect("fail-on: none only reports", p.returncode == 0, p.stdout[-400:])
        open(os.path.join(work, "design", "vendor", "sf-symbols.css"), "w").write(
            "/* SF Symbols drawn on this Mac by sf_icons.py. */")
        p = act(ONPLATFORM_DESIGNS=os.path.join(work, "design"))
        expect("a design carrying SF Symbols fails, annotated", p.returncode == 1 and "::error file=" in p.stdout,
               p.stdout[-800:])
        p = act(ONPLATFORM_SWIFTUI="x", ONPLATFORM_PURPOSE="sometimes")
        expect("a bad input is refused", p.returncode == 2, p.stdout)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    if FAILED:
        print(f"\n{len(FAILED)} failed")
        return 1
    print("\nall passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
