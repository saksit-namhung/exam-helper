import json

with open(r"G:\My Drive\Sync\Docs\MLA-C01.json", encoding="utf-8") as f:
    data = json.load(f)

qs = data["questions"]
hotspots = [q for q in qs if q["type"] == "hotspot"]
no_ans = [q for q in hotspots if not q.get("answer")]

print(f"Total questions: {len(qs)}")
print(f"HOTSPOT questions: {len(hotspots)}")
print(f"  - with answer parsed: {len(hotspots) - len(no_ans)}")
print(f"  - no answer in PDF:   {len(no_ans)}")
print(f"    (Q{', Q'.join(str(q['question_number']) for q in no_ans)})")
print()

# Show all answered HOTSPOTs
print("=== All answered HOTSPOT questions ===")
for q in hotspots:
    if q.get("answer"):
        ans = q["answer"]
        if isinstance(ans, list) and ans and isinstance(ans[0], dict):
            ans_str = f"matching ({len(ans)} pairs)"
        elif isinstance(ans, list):
            ans_str = f"ordered/selection ({len(ans)} items)"
        else:
            ans_str = str(ans)
        print(f"  Q{q['question_number']}: {ans_str}")
