"""
Compare old (truncated) vs new (fixed) option text for every question.
Produces a list of all options that changed after the parser fix.
"""
import json
import re

import pdfplumber

PDF_PATH = r"G:\My Drive\Sync\Docs\MLA-C01.pdf"
NEW_JSON  = r"G:\My Drive\Sync\Docs\MLA-C01.json"


# ── Old (buggy) parser ────────────────────────────────────────────────────────
_OLD_OPT = re.compile(
    r"^([A-E])\.\s*(.+?)(?=^[A-E]\.|$)", re.MULTILINE | re.DOTALL
)
_NEW_OPT = re.compile(
    r"^([A-E])\.\s*(.+?)(?=^[A-E]\.|\Z)", re.MULTILINE | re.DOTALL
)

def _parse_opts(pattern, text):
    opts = {}
    for m in pattern.finditer(text):
        opts[m.group(1)] = re.sub(r"\s+", " ", m.group(2).strip())
    return opts


def extract_all_text(pdf_path):
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                pages.append(t)
    return "\n".join(pages)


def split_into_questions(full_text):
    pattern = re.compile(r"(?=Question:\s*(\d+)\s+Deep Dumps)", re.MULTILINE)
    splits  = list(pattern.finditer(full_text))
    blocks  = []
    for i, m in enumerate(splits):
        start = m.start()
        end   = splits[i + 1].start() if i + 1 < len(splits) else len(full_text)
        blocks.append((int(m.group(1)), full_text[start:end]))
    return blocks


# ── Main ──────────────────────────────────────────────────────────────────────
print("Extracting PDF text…")
full_text = extract_all_text(PDF_PATH)

print("Splitting into question blocks…")
blocks = split_into_questions(full_text)

print(f"Found {len(blocks)} question blocks\n")

# Load the fixed JSON for comparison
with open(NEW_JSON, encoding="utf-8") as f:
    fixed_data = json.load(f)

fixed_map = {q["question_number"]: q for q in fixed_data["questions"]}

changes = []   # (q_num, letter, old_text, new_text)

for num, block in blocks:
    # Only look at the part before Answer:
    question_part = re.split(r"\nAnswer:", block, maxsplit=1)[0]

    old_opts = _parse_opts(_OLD_OPT, question_part)
    new_opts = _parse_opts(_NEW_OPT, question_part)

    for letter in sorted(set(old_opts) | set(new_opts)):
        old_val = old_opts.get(letter, "")
        new_val = new_opts.get(letter, "")
        if old_val != new_val:
            changes.append((num, letter, old_val, new_val))

print(f"Total options changed: {len(changes)}\n")
print("=" * 80)

for q_num, letter, old_val, new_val in changes:
    print(f"Q{q_num} [{letter}]")
    print(f"  BEFORE: {old_val}")
    print(f"  AFTER : {new_val}")
    print()
