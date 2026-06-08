import pdfplumber, re, json

with open("/Users/saksit/Downloads/FIles/MLA-C01.json", encoding="utf-8") as f:
    data = json.load(f)

no_ans = [q for q in data["questions"] if q["type"] == "hotspot" and not q.get("answer")]
print(f"HOTSPOT without answer: {len(no_ans)}")
for q in no_ans:
    print(f"  Q{q['question_number']}: {q['question'][:100]}")

print()

# Show raw PDF blocks for unanswered HOTSPOT questions
with pdfplumber.open("/Users/saksit/Downloads/FIles/MLA-C01.pdf") as pdf:
    full_text = "\n".join(p.extract_text() for p in pdf.pages if p.extract_text())

for q in no_ans[:4]:
    num = q["question_number"]
    m = re.search(
        rf"Question:\s*{num}\s+Deep Dumps.*?(?=Question:\s*\d+\s+Deep Dumps|$)",
        full_text, re.DOTALL
    )
    if m:
        print(f"===== Q{num} RAW =====")
        print(m.group()[:1800])
        print()
