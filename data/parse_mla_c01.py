import pdfplumber
import re
import json

PDF_PATH = r"G:\My Drive\Sync\Docs\MLA-C01.pdf"
OUT_PATH = r"G:\My Drive\Sync\Docs\MLA-C01.json"


def extract_all_text(pdf_path):
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return "\n".join(pages)


def split_into_questions(full_text):
    """Split the full text on 'Question: N' boundaries."""
    pattern = re.compile(r"(?=Question:\s*(\d+)\s+Deep Dumps)", re.MULTILINE)
    splits = list(pattern.finditer(full_text))
    blocks = []
    for i, match in enumerate(splits):
        start = match.start()
        end = splits[i + 1].start() if i + 1 < len(splits) else len(full_text)
        blocks.append((int(match.group(1)), full_text[start:end]))
    return blocks


def detect_question_type(block):
    if re.search(r"HOTSPOT\s*[-–]?", block, re.IGNORECASE) and "HOTSPOT" in block.upper():
        return "hotspot"
    if re.search(r"Case Study\s*-", block, re.IGNORECASE):
        return "case_study"
    if re.search(r"DRAG DROP\s*-", block, re.IGNORECASE):
        return "drag_drop"
    if re.search(r"SIMULATION\s*-", block, re.IGNORECASE):
        return "simulation"
    return "multiple_choice"


def parse_bullet_options(text):
    """Extract •-delimited options from HOTSPOT question text.

    Returns only the actual option items, skipping any prefix text that
    appears before the first bullet character.  Continuation lines (text
    that wraps onto the next line within a bullet) are joined, while
    trailing instruction paragraphs (starting with keywords like "Select",
    "Order", "Note", "Correct", "Answer", etc.) are dropped.
    """
    # Patterns that indicate an instruction/header line rather than option text
    _INSTRUCTION = re.compile(
        r"^(Select|Order|Note|Correct|Answer|Choose|Each|You|The\s+correct|"
        r"Drag|Drop|Click|Check|Place|Match|Refer\s+to)",
        re.IGNORECASE,
    )

    # Normalise different bullet chars to \n• so we can split cleanly
    raw = re.sub(r"[•·]", "\n•", text)
    parts = raw.split("\n•")
    # parts[0] is everything before the first bullet (question stem / header) – skip it
    items = []
    for part in parts[1:]:          # skip index 0
        part = part.strip().lstrip("•").strip()
        lines = part.splitlines()
        kept = []
        for line in lines:
            line = line.strip()
            if not line:
                break  # blank line ends the bullet
            if _INSTRUCTION.match(line):
                break  # instruction paragraph – stop here
            kept.append(line)
        combined = " ".join(kept).strip()
        if combined:
            items.append(re.sub(r"\s+", " ", combined))
    return items if items else []


def parse_mc_options(text):
    """Extract A/B/C/D/E letter options from multiple-choice text."""
    # Use \Z (true end-of-string) instead of $ so the lazy .+? captures across
    # line breaks rather than stopping at the first newline ($ with MULTILINE
    # matches end-of-line, not end-of-string).
    option_pattern = re.compile(r"^([A-E])\.\s*(.+?)(?=^[A-E]\.|\Z)", re.MULTILINE | re.DOTALL)
    options = {}
    for m in option_pattern.finditer(text):
        letter = m.group(1)
        content = re.sub(r"\s+", " ", m.group(2).strip())
        options[letter] = content
    return options


def parse_answer(text):
    """Extract answer letter(s) after 'Answer:' for multiple-choice questions."""
    m = re.search(r"Answer:\s*([A-E,\s]+?)(?:\n|Explanation:)", text, re.IGNORECASE | re.DOTALL)
    if m:
        raw = m.group(1).strip()
        letters = re.findall(r"[A-E]", raw)
        if letters:
            return letters if len(letters) > 1 else letters[0]
        return raw
    return None


def parse_explanation(text):
    """Extract raw explanation text after 'Explanation:' (newlines preserved)."""
    m = re.search(r"Explanation:\s*(.*?)(?=Question:\s*\d+\s+Deep Dumps|$)", text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return None


# ---------------------------------------------------------------------------
# HOTSPOT answer extraction from explanation text
# ---------------------------------------------------------------------------

def _hotspot_detect_subtype(exp_text, question_text):
    """Classify the HOTSPOT subtype from the explanation."""
    if re.search(r"Step\s+\d+\s*:", exp_text, re.IGNORECASE):
        return "ordering"
    if re.search(r"\d+\s*[)\.]\s*.{5,100}?→", exp_text):
        return "matching"
    if re.search(r"\d+\s*[)\.]\s*.{5,100}?\s*:[\s\w]", exp_text):
        return "matching"
    # Ordering phrasing in the question
    if re.search(r"select and order", question_text, re.IGNORECASE):
        return "ordering"
    return "selection"


def _parse_ordering_answer(exp_text):
    """Return ordered list of chosen items from a Step-based explanation."""
    # Match 'Step N: <chosen item text>' (the first sentence/phrase after the colon)
    pattern = re.compile(r"Step\s+(\d+)\s*:\s*(.+?)(?=Step\s+\d+\s*:|$)", re.DOTALL | re.IGNORECASE)
    steps = {}
    for m in pattern.finditer(exp_text):
        n = int(m.group(1))
        # The chosen item is typically the first sentence before a period+newline or before reasoning
        raw = m.group(2).strip()
        # Take only the first sentence (the item name), not the full explanation
        first_sent = re.split(r"\.\s+[A-Z]|\.\s*$", raw)[0].strip()
        # Normalize
        first_sent = re.sub(r"\s+", " ", first_sent).rstrip(".")
        steps[n] = first_sent
    if steps:
        return [steps[k] for k in sorted(steps)]
    return None


def _parse_matching_answer(exp_text):
    """Return list of {statement, answer} pairs from a matching explanation."""
    # Pattern: '1) "some statement" → Answer text'   (arrow must be on the same line)
    arrow_pattern = re.compile(
        r'^\s*\d+\s*[)\.]\s*[\u201c\u201d"]?(.{5,150}?)[\u201c\u201d"]?\s*\u2192\s*(.+?)\s*$',
        re.MULTILINE,
    )
    # Pattern: '1. some statement : Answer text.'  (colon separator, anchored to line start)
    colon_pattern = re.compile(
        r"^\s*\d+\s*[)\.]\s*(.{5,200}?)\s*:\s*([A-Za-z][^.\n]{2,80})\.",
        re.MULTILINE,
    )

    pairs = []
    for m in arrow_pattern.finditer(exp_text):
        stmt = re.sub(r"\s+", " ", m.group(1).strip()).strip('"').strip()
        ans = re.sub(r"\s+", " ", m.group(2).strip()).split(".")[0].strip()
        pairs.append({"statement": stmt, "answer": ans})

    if not pairs:
        for m in colon_pattern.finditer(exp_text):
            stmt = re.sub(r"\s+", " ", m.group(1).strip()).strip('"').strip()
            ans = re.sub(r"\s+", " ", m.group(2).strip()).strip()
            pairs.append({"statement": stmt, "answer": ans})

    return pairs if pairs else None


def _parse_selection_answer(exp_text, bullet_options):
    """Return list of chosen items by matching explanation against bullet options."""
    if not bullet_options:
        return None
    chosen = []
    for opt in bullet_options:
        # Check if the option (or a significant substring) appears in the explanation
        key = re.escape(opt[:30])
        if re.search(key, exp_text, re.IGNORECASE):
            chosen.append(opt)
    return chosen if chosen else None


def _try_parse_description_matching(exp_text, bullet_options):
    """Q8-style: 'N. [description] [option_term]. [more explanation]'
    Each numbered item ends its first sentence with one of the bullet options.
    Returns list of {statement, answer} pairs, or None if pattern not found.
    """
    if not bullet_options:
        return None
    # Sort longest first so more specific options match before substrings
    opts_clean = sorted([o.rstrip('.').strip() for o in bullet_options], key=len, reverse=True)
    pairs = []
    item_pat = re.compile(r'(?m)^(\d+)\.\s+(.+?)(?=\n\d+\.|\Z)', re.DOTALL)
    for m in item_pat.finditer(exp_text.strip()):
        body = m.group(2).strip()
        # First sentence: description + option appear before the first period followed by space+capital
        first_sent_m = re.match(r'^(.+?)\.\s', body, re.DOTALL)
        first_sent = first_sent_m.group(1) if first_sent_m else body[:200]
        matched_opt = None
        opt_pos = -1
        for opt in opts_clean:
            pos = first_sent.lower().find(opt.lower())
            if pos > 5 and (matched_opt is None or pos < opt_pos):
                matched_opt = opt
                opt_pos = pos
        if matched_opt and opt_pos > 5:
            desc = first_sent[:opt_pos].strip().rstrip('.,;:')
            desc = re.sub(r'\s+', ' ', desc).strip()
            if len(desc) > 10:
                pairs.append({"statement": desc, "answer": matched_opt})
    return pairs if len(pairs) >= 2 else None


def parse_hotspot_answer(exp_text, question_text, bullet_options):
    """Dispatch to the right HOTSPOT answer parser. Returns (answer, subtype) tuple."""
    if not exp_text:
        return None, None
    subtype = _hotspot_detect_subtype(exp_text, question_text)
    if subtype == "ordering":
        return _parse_ordering_answer(exp_text), "ordering"
    if subtype == "matching":
        return _parse_matching_answer(exp_text), "matching"
    # Try Q8-style description matching before falling back to selection
    desc_match = _try_parse_description_matching(exp_text, bullet_options)
    if desc_match:
        return desc_match, "matching"
    return _parse_selection_answer(exp_text, bullet_options), "selection"


# ---------------------------------------------------------------------------
# Question text extraction
# ---------------------------------------------------------------------------

def parse_question_text(block, q_type):
    """Extract the actual question stem (after type header, before options/answer)."""
    body = re.sub(r"^Question:\s*\d+\s+Deep Dumps\n?", "", block, flags=re.MULTILINE).strip()
    body = re.sub(r"^(HOTSPOT|Case Study|DRAG DROP|SIMULATION)\s*[-–]?\s*\n?", "", body,
                  flags=re.MULTILINE | re.IGNORECASE).strip()

    before_answer = re.split(r"\nAnswer:", body, maxsplit=1)[0]

    # For MC questions, stop before the first lettered option
    option_start = re.search(r"^[A-E]\.", before_answer, re.MULTILINE)
    if option_start:
        question_text = before_answer[:option_start.start()].strip()
    else:
        question_text = before_answer.strip()

    return re.sub(r"\s+", " ", question_text)


# ---------------------------------------------------------------------------
# Main block parser
# ---------------------------------------------------------------------------

def parse_block(num, block):
    q_type = detect_question_type(block)

    parts = re.split(r"\nAnswer:", block, maxsplit=1, flags=re.IGNORECASE)
    question_part = parts[0]
    answer_part = "Answer:" + parts[1] if len(parts) > 1 else ""

    question_text = parse_question_text(block, q_type)
    # Keep raw explanation (newlines intact) for HOTSPOT regex matching;
    # normalise separately for storage.
    explanation_raw = parse_explanation(answer_part)
    explanation = re.sub(r"\s+", " ", explanation_raw) if explanation_raw else None

    entry = {
        "question_number": num,
        "type": q_type,
        "question": question_text,
    }

    if q_type == "hotspot":
        # Extract the pool of selectable options from bullet points
        bullet_opts = parse_bullet_options(question_part)
        if bullet_opts:
            entry["options"] = bullet_opts
        # Derive the answer from the raw explanation (preserves line structure)
        answer, subtype = parse_hotspot_answer(explanation_raw, question_text, bullet_opts)
        if answer:
            entry["answer"] = answer
            if subtype:
                entry["hotspot_subtype"] = subtype
    else:
        mc_opts = parse_mc_options(question_part)
        if mc_opts:
            entry["options"] = mc_opts
        answer = parse_answer(answer_part)
        if answer is not None:
            entry["answer"] = answer

    if explanation:
        entry["explanation"] = explanation

    return entry


def main():
    print("Extracting text from PDF...")
    full_text = extract_all_text(PDF_PATH)

    print("Splitting into question blocks...")
    blocks = split_into_questions(full_text)
    print(f"Found {len(blocks)} questions")

    questions = []
    for num, block in blocks:
        try:
            entry = parse_block(num, block)
            questions.append(entry)
        except Exception as e:
            print(f"  Warning: error parsing question {num}: {e}")
            questions.append({"question_number": num, "error": str(e)})

    output = {
        "exam": "AWS Certified Machine Learning Engineer - Associate",
        "code": "MLA-C01",
        "total_questions": len(questions),
        "questions": questions,
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Written to: {OUT_PATH}")


if __name__ == "__main__":
    main()
