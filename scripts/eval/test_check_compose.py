#!/usr/bin/env python3
"""Does check_compose.py find what's there, and only what's there?

No model, no Android Studio:

1. A screen seeded with one of each defect produces exactly those findings,
   at those lines, of those kinds.
2. A correct screen, with a string and a comment that read like defects,
   produces nothing.
3. A theme file, where literal colours define the scheme, produces nothing.
4. The exit status is 1 with a violation and 0 without.

    python3 scripts/eval/test_check_compose.py
"""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHECK = os.path.normpath(os.path.join(HERE, "..", "..", ".claude", "skills", "ui-kit-for-android",
                                      "check_compose.py"))

BAD = '''\
package app
import androidx.compose.material.Button
import androidx.compose.material.icons.Icons
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable

@Composable
fun Bad() {
    // fontSize = 8.sp in a comment doesn't count
    Text("Tiny", fontSize = 9.sp, color = Color(0xFF6750A4))
    Text("Fixed", fontSize = 16.sp, color = Color.Red)
    IconButton(onClick = {}) {
        Icon(Icons.Filled.Search, contentDescription = null)
    }
    Box(Modifier.size(24.dp).clickable { })
}
'''

GOOD = '''\
package app
import androidx.compose.material3.*
import androidx.compose.runtime.Composable

@Composable
fun Good() {
    Text("Title", style = MaterialTheme.typography.titleLarge, color = MaterialTheme.colorScheme.primary)
    Box(Modifier.background(Color.Transparent))
    IconButton(onClick = {}) {
        Icon(Icons.Filled.Search, contentDescription = "Search")
    }
    Button(onClick = {}) { Icon(Icons.Filled.Add, contentDescription = null); Text("Add") }
    Box(Modifier.size(24.dp).minimumInteractiveComponentSize().clickable { })
    Text("Color(0xFF000000) in a string")
}
'''

THEME = '''\
package app
import androidx.compose.material3.lightColorScheme
val Light = lightColorScheme(primary = Color(0xFF8F4C33))
@androidx.compose.runtime.Composable fun T() {}
'''

# (line, kind, words the message must hold)
EXPECTED = [
    (2, "api", "Material 2"),
    (10, "violation", "under label-small"),
    (10, "violation", "colour written into a component"),
    (11, "guidance", "fixed 16 sp"),
    (11, "violation", "Color.Red"),
    (12, "violation", "TalkBack has nothing to read"),
    (15, "violation", "clickable 24 dp"),
]

failures = 0


def expect(label, ok, detail=""):
    global failures
    print(("ok   " if ok else "FAIL ") + label)
    if not ok:
        failures += 1
        if detail:
            print("     " + str(detail)[:600])


def run(name, text):
    d = tempfile.mkdtemp(prefix="compose-check-")
    path = os.path.join(d, name)
    open(path, "w").write(text)
    p = subprocess.run([sys.executable, CHECK, "--json", path], capture_output=True, text=True)
    return p.returncode, json.loads(p.stdout or "[]")


def main():
    rc, found = run("Bad.kt", BAD)
    got = sorted((f["line"], f["kind"], f["message"]) for f in found)
    for line, kind, words in EXPECTED:
        hit = any(l == line and k == kind and words.lower() in m.lower() for l, k, m in got)
        expect(f"seeded: line {line} {kind}: {words}", hit, got)
    expect(f"seeded: nothing beyond the {len(EXPECTED)} expected ({len(got)})",
           len(got) == len(EXPECTED), got)
    expect("seeded: every finding links its page", all(f["page"].startswith("https://") for f in found))
    expect("seeded: exits 1 on a violation", rc == 1, rc)

    rc, found = run("Good.kt", GOOD)
    expect("correct screen, strings and comments: nothing", not found, found)
    expect("correct screen: exits 0", rc == 0, rc)

    rc, found = run("Theme.kt", THEME)
    expect("theme file's literal colours: nothing", not found, found)

    print("\ncheck_compose test " + ("passed" if not failures else f"failed ({failures})"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
