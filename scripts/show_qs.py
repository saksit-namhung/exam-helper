import pdfplumber, re, json

with pdfplumber.open(r"G:\My Drive\Sync\Docs\MLA-C01.pdf") as pdf:
    full_text = "\n".join(p.extract_text() for p in pdf.pages if p.extract_text())

for qnum in [94, 121, 139, 185, 196]:
    m = re.search(
        rf"Question:\s*{qnum}\s+Deep Dumps.*?(?=Question:\s*\d+\s+Deep Dumps|$)",
        full_text,
        re.DOTALL,
    )
    if m:
        print(f"===== Q{qnum} =====")
        print(m.group()[:1500])
        print()
