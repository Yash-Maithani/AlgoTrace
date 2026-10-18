"""Extract the teaching part of each reference program into a lesson file.

    python tools/extract_code.py           write static/js/lessons/code/<algo>.js
    python tools/extract_code.py --check   exit 1 if any of them is out of date

The source of truth is reference_code/ (see reference_code/README.md for the
markers). Each generated file holds, per language and per variant, the same
{id, text, indent} lines a lesson's Python listing has, so the Code tab can
show any language and keep the highlight on the same line id.

Never edit the generated files by hand: tests/test_reference_code.py fails
when they no longer match what this script would write.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, 'reference_code')
OUT = os.path.join(ROOT, 'static', 'js', 'lessons', 'code')

# Lesson id -> Java class name. The C and C++ files are named after the id.
ALGORITHMS = {
    'bubble_sort': 'BubbleSort',
    'selection_sort': 'SelectionSort',
    'insertion_sort': 'InsertionSort',
    'merge_sort': 'MergeSort',
    'quick_sort': 'QuickSort',
    'heap_sort': 'HeapSort',
    'linear_search': 'LinearSearch',
    'binary_search': 'BinarySearch',
}

LANGUAGES = ('c', 'cpp', 'java')
INDENT = 4

START = re.compile(r'^(?P<pad> *)// lesson:start\s*$')
END = re.compile(r'^ *// lesson:end\s*$')
VARIANTS = re.compile(r'^ *// lesson:variants\s+(?P<ids>.+?)\s*$')
TAGS = re.compile(r'\s*//\s*(?P<tags>@\S+(?:\s+@\S+)*)\s*$')
LINE_ID = re.compile(r'^[a-z][a-z0-9-]*$')


class SourceError(Exception):
    pass


def source_path(algo, language):
    if language == 'java':
        return os.path.join(REF, 'java', ALGORITHMS[algo] + '.java')
    return os.path.join(REF, language, '%s.%s' % (algo, language))


def parse(path):
    """Return {variant: [{id, text, indent}]} for one source file."""
    try:
        rel = os.path.relpath(path, ROOT).replace(os.sep, '/')
    except ValueError:
        # A file on another drive, as a test's temporary file can be.
        rel = path.replace(os.sep, '/')
    with open(path, encoding='utf-8') as fh:
        lines = fh.read().splitlines()

    variants = None
    for line in lines:
        m = VARIANTS.match(line)
        if m:
            variants = m.group('ids').split()
    variants = variants or ['default']
    listings = {v: [] for v in variants}

    inside = False
    base = 0
    hidden_depth = 0
    blocks = 0
    for number, raw in enumerate(lines, 1):
        where = '%s:%d' % (rel, number)
        m = START.match(raw)
        if m:
            if inside:
                raise SourceError('%s: lesson:start inside a block' % where)
            inside, blocks = True, blocks + 1
            base = len(m.group('pad')) // INDENT
            hidden_depth = 0
            continue
        if END.match(raw):
            if not inside:
                raise SourceError('%s: lesson:end without lesson:start' % where)
            if hidden_depth:
                raise SourceError('%s: a hidden brace is still open at lesson:end' % where)
            inside = False
            continue
        if not inside:
            continue

        tags = []
        code = raw.rstrip()
        m = TAGS.search(code)
        if m:
            tags = m.group('tags').split()
            code = code[:m.start()].rstrip()
        stripped = code.strip()
        if not stripped or stripped.startswith(('//', '/*', '*')):
            continue

        hide = '@hide' in tags
        only = None
        line_id = None
        for tag in tags:
            if tag == '@hide':
                continue
            if tag.startswith('@only:'):
                only = tag[len('@only:'):].split(',')
                unknown = [v for v in only if v not in listings]
                if unknown:
                    raise SourceError('%s: @only names %s, not declared in lesson:variants'
                                      % (where, ', '.join(unknown)))
                continue
            name = tag[1:]
            if not LINE_ID.match(name):
                raise SourceError('%s: %r is not a line id' % (where, tag))
            if line_id:
                raise SourceError('%s: two line ids on one line' % where)
            line_id = name
        if hide and (line_id or only):
            raise SourceError('%s: a hidden line cannot carry an id or @only' % where)

        if hide:
            # A hidden brace only picks a variant at run time. The lines it
            # wraps read one level out, as in a program with that variant only.
            if stripped.startswith('}'):
                hidden_depth -= 1
            if stripped.endswith('{'):
                hidden_depth += 1
            if hidden_depth < 0:
                raise SourceError('%s: a hidden brace closes more than it opened' % where)
            continue

        pad = len(code) - len(code.lstrip(' '))
        if '\t' in code[:pad + 1] or pad % INDENT:
            raise SourceError('%s: indent with multiples of %d spaces' % (where, INDENT))
        indent = pad // INDENT - base - hidden_depth
        if indent < 0:
            raise SourceError('%s: line sits left of its lesson block' % where)
        entry = {'id': line_id, 'text': stripped, 'indent': indent}
        for variant in (only or variants):
            listings[variant].append(entry)

    if inside:
        raise SourceError('%s: lesson:start never closed' % rel)
    if not blocks:
        raise SourceError('%s: no lesson:start block' % rel)
    return rel, listings


def render(algo):
    """The text of static/js/lessons/code/<algo>.js."""
    out = [
        '/* Generated by tools/extract_code.py from reference_code/. Do not edit:',
        '   change the source file and run `python tools/extract_code.py`. */',
        'window.LESSON_CODE = window.LESSON_CODE || {};',
        'window.LESSON_CODE.%s = {' % algo,
    ]
    for k, language in enumerate(LANGUAGES):
        rel, listings = parse(source_path(algo, language))
        out.append('    %s: {' % language)
        out.append('        source: %s,' % json.dumps(rel))
        out.append('        listings: {')
        for j, (variant, lines) in enumerate(listings.items()):
            out.append('            %s: [' % json.dumps(variant))
            for i, line in enumerate(lines):
                comma = ',' if i < len(lines) - 1 else ''
                out.append('                { id: %s, text: %s, indent: %d }%s' % (
                    json.dumps(line['id']), json.dumps(line['text']), line['indent'], comma))
            out.append('            ]%s' % (',' if j < len(listings) - 1 else ''))
        out.append('        }')
        out.append('    }%s' % (',' if k < len(LANGUAGES) - 1 else ''))
    out.append('};')
    return '\n'.join(out) + '\n'


def target(algo):
    return os.path.join(OUT, algo + '.js')


def stale():
    """Algorithms whose generated file is missing or differs."""
    out = []
    for algo in sorted(ALGORITHMS):
        try:
            # Universal newlines: a checkout with core.autocrlf turns these
            # into CRLF, which is not a change worth failing over.
            with open(target(algo), encoding='utf-8') as fh:
                current = fh.read()
        except FileNotFoundError:
            current = None
        if current != render(algo):
            out.append(algo)
    return out


def main(argv):
    try:
        if '--check' in argv:
            out_of_date = stale()
            for algo in out_of_date:
                print('out of date: %s' % os.path.relpath(target(algo), ROOT))
            if out_of_date:
                print('run: python tools/extract_code.py')
                return 1
            print('ok: %d generated code files are up to date' % len(ALGORITHMS))
            return 0
        os.makedirs(OUT, exist_ok=True)
        for algo in sorted(ALGORITHMS):
            with open(target(algo), 'w', encoding='utf-8', newline='\n') as fh:
                fh.write(render(algo))
        print('wrote %d files to %s' % (len(ALGORITHMS), os.path.relpath(OUT, ROOT)))
        return 0
    except SourceError as error:
        print('error: %s' % error)
        return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
