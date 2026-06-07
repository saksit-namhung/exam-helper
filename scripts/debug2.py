import pdfplumber, re

with pdfplumber.open(r"G:\My Drive\Sync\Docs\MLA-C01.pdf") as pdf:
    all_pages = []
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        all_pages.append((i + 1, text or ""))

# Find pages containing Q185 and nearby
for pg_num, text in all_pages:
    if "Question: 185" in text or "Question: 196" in text or "Question: 197" in text:
        print(f"=== Page {pg_num} ===")
        print(text[:2000])
        print()
        # Also print next 2 pages
        for j in range(1, 3):
            if pg_num - 1 + j < len(all_pages):
                np, nt = all_pages[pg_num - 1 + j]
                print(f"--- Next page {np} ---")
                print(nt[:1500])
                print()
        break
