import fitz
doc = fitz.open(r"")
print(doc.page_count)
