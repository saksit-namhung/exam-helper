import json, collections

with open(r"G:\My Drive\Sync\Docs\MLA-C01.json", encoding="utf-8") as f:
    data = json.load(f)

types = collections.Counter(q["type"] for q in data["questions"])
print("Question types:", dict(types))
print()

no_ans = [q for q in data["questions"] if not q.get("answer")]
print(f"Questions with empty answer: {len(no_ans)}")
for q in no_ans[:10]:
    print(f"  Q{q['question_number']}: {q['question'][:120]}")
