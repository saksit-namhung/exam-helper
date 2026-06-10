import pdfplumber
import re
import json
import os

# Default paths - can be overridden via environment variables or command line
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_PATH = os.environ.get("PDF_PATH", "/Users/saksit/Downloads/FIles/aws-certified-cloud-practitioner-clf-c02.pdf")
OUT_PATH = os.environ.get("OUT_PATH", os.path.join(PROJECT_ROOT, "resources", "CLF-C02.json"))


def extract_all_text(pdf_path):
    """Extract text from all pages of the PDF."""
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return "\n".join(pages)


def split_into_questions(full_text):
    """Split the full text on 'Question: N CertyIQ' boundaries."""
    # Match "Question: N CertyIQ" or "Question: N\nCertyIQ" or just "Question: N"
    pattern = re.compile(r"(?=Question:\s*(\d+)\s+(?:CertyIQ)?)", re.MULTILINE)
    splits = list(pattern.finditer(full_text))
    blocks = []
    for i, match in enumerate(splits):
        start = match.start()
        end = splits[i + 1].start() if i + 1 < len(splits) else len(full_text)
        question_num = int(match.group(1))
        blocks.append((question_num, full_text[start:end]))
    return blocks


def parse_mc_options(text):
    """Extract A/B/C/D/E letter options from multiple-choice text."""
    # Match options that start with a letter followed by a period
    # Use DOTALL to match across lines, and lazy matching to stop at next option or Answer:
    option_pattern = re.compile(
        r"^([A-E])\.\s*(.+?)(?=^[A-E]\.\s+|^Answer:|$)",
        re.MULTILINE | re.DOTALL
    )
    options = {}
    for m in option_pattern.finditer(text):
        letter = m.group(1)
        content = re.sub(r"\s+", " ", m.group(2).strip())
        options[letter] = content
    return options


def parse_answer(text):
    """Extract answer letter(s) after 'Answer:' for multiple-choice questions."""
    # Look for "Answer: X" where X can be single or multiple letters
    m = re.search(r"Answer:\s*([A-E,\s]+?)(?:\n|Explanation:|$)", text, re.IGNORECASE | re.DOTALL)
    if m:
        raw = m.group(1).strip()
        letters = re.findall(r"[A-E]", raw)
        if letters:
            return letters if len(letters) > 1 else letters[0]
        return raw
    return None


def parse_explanation(text):
    """Extract explanation text after 'Explanation:'."""
    m = re.search(
        r"Explanation:\s*(.*?)(?=Question:\s*\d+\s+(?:CertyIQ)?|$)",
        text,
        re.DOTALL | re.IGNORECASE
    )
    if m:
        explanation = m.group(1).strip()
        # Normalize whitespace
        explanation = re.sub(r"\s+", " ", explanation)
        return explanation
    return None


def parse_question_text(block):
    """Extract the actual question stem (before options)."""
    # Remove the header "Question: N CertyIQ"
    body = re.sub(r"^Question:\s*\d+\s+(?:CertyIQ)?\s*\n?", "", block, flags=re.MULTILINE).strip()
    
    # Split at "Answer:" to get everything before it
    before_answer = re.split(r"\nAnswer:", body, maxsplit=1)[0]
    
    # Split at the first option (A., B., etc.)
    option_start = re.search(r"^[A-E]\.\s*", before_answer, re.MULTILINE)
    if option_start:
        question_text = before_answer[:option_start.start()].strip()
    else:
        question_text = before_answer.strip()
    
    # Normalize whitespace
    return re.sub(r"\s+", " ", question_text)


def parse_block(num, block):
    """Parse a single question block into structured data."""
    # Split at Answer: to separate question part from answer part
    parts = re.split(r"\nAnswer:", block, maxsplit=1, flags=re.IGNORECASE)
    question_part = parts[0]
    answer_part = "Answer:" + parts[1] if len(parts) > 1 else ""
    
    # Extract components
    question_text = parse_question_text(block)
    options = parse_mc_options(question_part)
    answer = parse_answer(answer_part)
    explanation = parse_explanation(answer_part)
    
    # Build entry
    entry = {
        "question_number": num,
        "type": "multiple_choice",
        "question": question_text,
    }
    
    if options:
        entry["options"] = options
    
    if answer is not None:
        entry["answer"] = answer
    
    if explanation:
        entry["explanation"] = explanation
    
    return entry


def main():
    print("Extracting text from PDF...")
    print(f"Reading: {PDF_PATH}")
    full_text = extract_all_text(PDF_PATH)
    
    print("Splitting into question blocks...")
    blocks = split_into_questions(full_text)
    print(f"Found {len(blocks)} questions")
    
    questions = []
    errors = []
    
    for num, block in blocks:
        try:
            entry = parse_block(num, block)
            questions.append(entry)
            if num % 50 == 0:
                print(f"  Processed question {num}...")
        except Exception as e:
            print(f"  Warning: error parsing question {num}: {e}")
            errors.append({"question_number": num, "error": str(e)})
            questions.append({"question_number": num, "error": str(e)})
    
    output = {
        "exam": "AWS Certified Cloud Practitioner",
        "code": "CLF-C02",
        "total_questions": len(questions),
        "questions": questions,
    }
    
    print(f"\nWriting to: {OUT_PATH}")
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Successfully parsed {len(questions)} questions")
    if errors:
        print(f"✗ Encountered {len(errors)} errors")
    print(f"Output saved to: {OUT_PATH}")


if __name__ == "__main__":
    main()
