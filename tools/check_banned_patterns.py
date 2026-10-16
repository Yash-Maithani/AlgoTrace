"""Find banned patterns however they are written.

REBUILD_PLAN bans em dashes and emoji. A literal character scan misses them
when the source escapes them, which JavaScript source does freely, so this
decodes the escaped forms before looking:

    \\u2014 and \\u{1F680}        JavaScript escapes
    surrogate pairs              \\uD83D\\uDE80 is one emoji
    &mdash; &#8212; &#x2014;      HTML entities
"""
import glob
import html
import os
import re
import sys

BS = chr(92)

JS_SHORT = re.compile(BS * 2 + r'u([0-9a-fA-F]{4})')
JS_LONG = re.compile(BS * 2 + r'u\{([0-9a-fA-F]{1,6})\}')
ENTITY = re.compile(r'&(#[0-9]{1,7}|#x[0-9a-fA-F]{1,6}|[a-zA-Z][a-zA-Z0-9]{1,31});')

EMOJI_RANGES = [
    (0x1F000, 0x1FAFF),   # pictographs, emoticons, symbols
    (0x2600, 0x27BF),     # misc symbols and dingbats
    (0x2B00, 0x2BFF),     # arrows and stars used as emoji
    (0xFE0F, 0xFE0F),     # variation selector 16
    (0x1F1E6, 0x1F1FF),   # regional indicators
]

# Typography that is allowed: the infinity label, the arrow used in paths,
# the non breaking space, the middle dot, curly quotes.
ALLOWED = {0x221E, 0x2192, 0x00A0, 0x00B7, 0x2018, 0x2019, 0x201C, 0x201D,
           0x2026, 0x00AD, 0x2212, 0x00D7, 0x2264, 0x2265, 0x2260, 0x00B0,
           0x00B2, 0x00B3, 0x2070, 0x207F}

DASHES = {0x2014: 'em dash', 0x2013: 'en dash'}


def is_emoji(code):
    if code in ALLOWED:
        return False
    return any(low <= code <= high for low, high in EMOJI_RANGES)


def decode_escapes(text):
    """Yield (codepoint, how_it_was_written) for every escaped character."""
    out = []
    for match in JS_SHORT.finditer(text):
        out.append((int(match.group(1), 16), match.group(0)))
    for match in JS_LONG.finditer(text):
        out.append((int(match.group(1), 16), match.group(0)))
    for match in ENTITY.finditer(text):
        decoded = html.unescape(match.group(0))
        if len(decoded) == 1 and decoded != match.group(0):
            out.append((ord(decoded), match.group(0)))
    # Surrogate pairs: a high surrogate followed by a low one is one emoji.
    pairs = re.findall(BS * 2 + r'u(D[89ABab][0-9a-fA-F]{2})' + BS * 2 + r'u(D[C-Fc-f][0-9a-fA-F]{2})', text)
    for high, low in pairs:
        code = 0x10000 + ((int(high, 16) - 0xD800) << 10) + (int(low, 16) - 0xDC00)
        out.append((code, BS + 'u' + high + BS + 'u' + low))
    return out


# A file that documents these patterns, like the plan's definition of done or
# this check's own tests, says so once and is skipped. Explicit, greppable,
# and it keeps the check from flagging the description of itself.
PRAGMA = 'banned-check: documents-the-patterns'


def problems_in(path):
    with open(path, encoding='utf-8') as fh:
        text = fh.read()

    if PRAGMA in text:
        return []

    found = []
    for line_no, line in enumerate(text.split(chr(10)), 1):
        # literal characters
        for ch in line:
            code = ord(ch)
            if code in DASHES:
                found.append((line_no, DASHES[code], 'U+%04X' % code))
            elif is_emoji(code):
                found.append((line_no, 'emoji', 'U+%04X' % code))
        # escaped and entity forms
        for code, written in decode_escapes(line):
            if code in DASHES:
                found.append((line_no, DASHES[code] + ' (escaped)', written))
            elif is_emoji(code):
                found.append((line_no, 'emoji (escaped)', written))
    return found


SKIP_DIRS = {'.git', '__pycache__', 'venv', '.venv', 'node_modules',
             '.pytest_cache', 'project_documentation', '.agents', '.claude',
             '.vscode'}

# Documents that carried these before the rule existed. They are reported
# separately rather than hidden, and they do not fail the check, so the gate
# stays usable for the thing it is for: catching what a phase introduces.
# REDESIGN_PLAN.md and DESIGN_SYSTEM.md are superseded by REBUILD_PLAN.md and
# DESIGN.md. README.md is live and still wants cleaning.
LEGACY = {'README.md', 'DESIGN_SYSTEM.md', 'REDESIGN_PLAN.md'}
SUFFIXES = ('.py', '.html', '.js', '.css', '.md', '.json', '.txt')


def main(root):
    total = 0
    legacy_total = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in sorted(filenames):
            if not name.endswith(SUFFIXES):
                continue
            path = os.path.join(dirpath, name)
            # This scanner names the patterns it hunts, so it would flag itself.
            if os.path.basename(path) == os.path.basename(__file__):
                continue
            hits = problems_in(path)
            if not hits:
                continue
            rel = os.path.relpath(path, root)
            if os.path.basename(path) in LEGACY:
                legacy_total += len(hits)
                continue
            for line_no, kind, written in hits:
                print('%s:%d  %-22s %s' % (rel, line_no, kind, written))
                total += 1
    print()
    if legacy_total:
        print('%d in documents that predate the rule (%s). Not counted.'
              % (legacy_total, ', '.join(sorted(LEGACY))))
    print('TOTAL BANNED PATTERNS:', total)
    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else '.'))
