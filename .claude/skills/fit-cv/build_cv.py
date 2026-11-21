"""Make a tailored copy of Andrea's CV (.docx exported from his Google Doc): same layout,
only the texts change. No CV text lives here: it comes from the exported file.

Usage: python build_cv.py <master.docx> <spec.json> <out.docx>

spec.json:
  {"headline": "...", "summary": "...",
   "roles": [["bullet", ...], ...],      one list per role, in the CV's order
   "skills": [["Label:", "value"], ...]} one pair per skills line, in the CV's order
"""
import hashlib
import json
import re
import sys
import zipfile
from xml.sax.saxutils import escape

PARA = re.compile(r'<w:p[ >].*?</w:p>', re.S)
TEXT = re.compile(r'(<w:t(?: [^>]*)?>)(.*?)(</w:t>)', re.S)  # <w:t>, not <w:tab/> or <w:top>


def plain(p):
    return ''.join(m.group(2) for m in TEXT.finditer(p)).strip()


def set_texts(p, texts):
    """Put texts[i] into the i-th text piece of paragraph p; pieces after them become empty."""
    i = 0

    def rep(m):
        nonlocal i
        new = escape(texts[i]) if i < len(texts) else ''
        i += 1
        return m.group(1) + new + m.group(3)
    return TEXT.sub(rep, p)


def build(master, spec, out):
    z = zipfile.ZipFile(master)
    doc = z.read('word/document.xml').decode('utf-8')
    paras = PARA.findall(doc)
    texts = [plain(p) for p in paras]
    is_list = ['<w:numPr>' in p for p in paras]
    head = {t.upper(): i for i, t in enumerate(texts) if t and t == t.upper() and not is_list[i]}
    summary_at, work_at = head['PROFESSIONAL SUMMARY'], head['WORK EXPERIENCE']
    skills_at = head['SKILLS']
    new = list(paras)

    # 1. Headline: the line under the name. 2. Summary: the paragraph under its heading.
    new[1] = set_texts(paras[1], [spec['headline']])
    new[summary_at + 1] = set_texts(paras[summary_at + 1], [spec['summary']])

    # 3. Each role's bullets, rebuilt from the role's first bullet (keeps the bullet style).
    blocks, i = [], work_at + 1
    while i < skills_at:
        if is_list[i]:
            start = i
            while i < skills_at and is_list[i]:
                i += 1
            blocks.append((start, i))
        else:
            i += 1
    if len(blocks) != len(spec['roles']):
        sys.exit(f"the CV has {len(blocks)} roles, the spec {len(spec['roles'])}")
    for (start, end), bullets in zip(blocks, spec['roles']):
        if not bullets:
            sys.exit("every role keeps at least one bullet")
        new[start] = ''.join(set_texts(paras[start], [b]) for b in bullets)
        for k in range(start + 1, end):
            new[k] = ''

    # 4. Skills lines ("Label: values"), in order.
    lines = [k for k in range(skills_at + 1, len(paras)) if ':' in texts[k] and texts[k] != texts[k].upper()]
    for k, (label, value) in zip(lines, spec['skills']):
        new[k] = set_texts(paras[k], [label, ' ' + value])

    for old, nw in zip(paras, new):
        doc = doc.replace(old, nw, 1)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as o:
        for item in z.infolist():
            o.writestr(item, doc.encode('utf-8') if item.filename == 'word/document.xml' else z.read(item.filename))
    # The upload tool needs the file's SHA-256.
    print(out, hashlib.sha256(open(out, 'rb').read()).hexdigest())


if __name__ == '__main__':
    build(sys.argv[1], json.load(open(sys.argv[2], encoding='utf-8')), sys.argv[3])
