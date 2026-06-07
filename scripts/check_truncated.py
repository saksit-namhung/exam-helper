"""
Scan all questions in MLA-C01.json and report options with truncated text.
"""
import json

DATA_FILE = r"G:\My Drive\Sync\Docs\MLA-C01.json"

with open(DATA_FILE, encoding="utf-8") as f:
    data = json.load(f)

questions = data.get("questions", data) if isinstance(data, dict) else data
if isinstance(questions, dict):
    questions = list(questions.values())

TERMINAL_CHARS = (".", "!", "?", '"', ")", "]", "%", "s", "d")  # rough heuristic

END_OK = set('.!?")}]%0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
TERMINAL_CHARS = set('.!?"\')]}')

def is_truncated(text: str) -> bool:
    s = text.strip()
    if not s:
        return True
    # Truncated if it ends with a common preposition/article/conjunction or has no terminal punctuation
    last_char = s[-1]
    if last_char in TERMINAL_CHARS:
        return False
    # Check last word
    last_word = s.split()[-1].lower().rstrip(',:;')
    truncating_words = {
        'the', 'a', 'an', 'of', 'in', 'on', 'at', 'to', 'for', 'with',
        'by', 'from', 'and', 'or', 'that', 'which', 'this', 'as', 'is',
        'are', 'was', 'be', 'use', 'uses', 'specify', 'select', 'configure',
    }
    if last_word in truncating_words:
        return True
    # If no period at end and text looks sentence-like (>40 chars), flag it
    if last_char not in TERMINAL_CHARS and len(s) > 40:
        return True
    return False

truncated = []
for q in questions:
    opts = q.get("options", {})
    if isinstance(opts, dict):
        items = opts.items()
    elif isinstance(opts, list):
        items = enumerate(opts)
    else:
        continue
    for key, val in items:
        if isinstance(val, str):
            stripped = val.strip()
            if not stripped:
                truncated.append((q.get("question_number"), key, "(EMPTY)"))
            elif is_truncated(stripped):
                truncated.append((q.get("question_number"), key, stripped))

print(f"Total questions: {len(questions)}")
print(f"Truncated options found: {len(truncated)}\n")
for qnum, key, text in truncated:
    print(f"Q{qnum} [{key}]: {text}")
    print()
