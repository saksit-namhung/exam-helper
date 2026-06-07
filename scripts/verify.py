import json

with open(r"G:\My Drive\Sync\Docs\MLA-C01.json", encoding="utf-8") as f:
    data = json.load(f)

hotspots = [q for q in data["questions"] if q["type"] == "hotspot"]
no_ans = [q for q in hotspots if not q.get("answer")]

print(f"Total HOTSPOT questions: {len(hotspots)}")
print(f"HOTSPOT without answer: {len(no_ans)}")
print()

for q in hotspots[:6]:
    print(f"=== Q{q['question_number']} ===")
    print("Options:", q.get("options"))
    print("Answer:", q.get("answer"))
    print()
