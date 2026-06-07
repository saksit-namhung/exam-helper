import pdfplumber, re

with pdfplumber.open(r"G:\My Drive\Sync\Docs\MLA-C01.pdf") as pdf:
    full_text = "\n".join(p.extract_text() for p in pdf.pages if p.extract_text())

m = re.search(
    r"Question:\s*9\s+Deep Dumps.*?(?=Question:\s*10\s+Deep Dumps)",
    full_text, re.DOTALL
)
if m:
    print(repr(m.group()))
