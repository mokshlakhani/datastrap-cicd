"""Turn a plain-text test log into a JUnit XML file that Jenkins can show.

Usage: python ci/to_junit.py <suite-name> <log-file> <exit-code> <output.xml>

The npm tests print one line per check ("ok   name" or "FAIL name").
If a log has no such lines, the whole run counts as one test that passes
when the exit code is 0.
"""
import sys
from xml.sax.saxutils import quoteattr


def main(suite, log_path, exit_code, out_path):
    with open(log_path, errors="replace") as fh:
        lines = [ln.rstrip("\n") for ln in fh]
    cases = []  # (name, passed)
    for ln in lines:
        word, _, name = ln.partition(" ")
        if word in ("ok", "FAIL") and name.strip():
            cases.append((name.strip(), word == "ok"))
    if not cases:
        cases = [(suite + " (whole run)", int(exit_code) == 0)]
    elif int(exit_code) != 0 and all(ok for _, ok in cases):
        cases.append((suite + " (process exit code)", False))  # crashed after printing "ok" lines
    failures = sum(1 for _, ok in cases if not ok)
    with open(out_path, "w") as out:
        out.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        out.write(f'<testsuite name={quoteattr(suite)} tests="{len(cases)}" failures="{failures}">\n')
        for name, ok in cases:
            out.write(f'  <testcase classname={quoteattr(suite)} name={quoteattr(name)}>')
            if not ok:
                out.write('<failure message="test failed; see the console log"/>')
            out.write('</testcase>\n')
        out.write('</testsuite>\n')


if __name__ == "__main__":
    main(*sys.argv[1:5])
