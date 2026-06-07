"""Verify Q58 is fixed and count remaining truncated options."""
import json

DATA_FILE = r"G:\My Drive\Sync\Docs\MLA-C01.json"

with open(DATA_FILE, encoding="utf-8") as f:
    data = json.load(f)

qs = data["questions"]

# Check Q58
q58 = next(q for q in qs if q["question_number"] == 58)
print("=== Q58 Options ===")
for k, v in q58["options"].items():
    print(f"  {k}: {v}")
print()

# Count remaining truncated options
TERMINAL = set(".!?\")}]%0123456789")
STOPWORDS = {
    "the", "a", "an", "of", "in", "on", "at", "to", "for", "with",
    "by", "from", "and", "or", "that", "which", "this", "as",
    "specify", "select", "configure", "use",
}

truncated = []
for q in qs:
    opts = q.get("options", {})
    items = opts.items() if isinstance(opts, dict) else enumerate(opts)
    for key, val in items:
        if not isinstance(val, str):
            continue
        s = val.strip()
        if not s:
            continue
        last_word = s.split()[-1].lower() if s.split() else ""
        if last_word in STOPWORDS or (s[-1] not in TERMINAL and len(s) > 40):
            truncated.append((q["question_number"], key, s))

print(f"Remaining potentially truncated options: {len(truncated)}")
for qn, k, text in truncated[:30]:
    print(f"  Q{qn}[{k}]: {text[-100:]}")

# Spot-check Q209 and Q229
print()
for target in [209, 229]:
    q = next((x for x in qs if x["question_number"] == target), None)
    if not q:
        continue
    print(f"=== Q{target} (type={q['type']}) ===")
    opts = q.get("options", [])
    items = opts.items() if isinstance(opts, dict) else enumerate(opts)
    for k, v in items:
        print(f"  [{k}]: {v}")
    print()
