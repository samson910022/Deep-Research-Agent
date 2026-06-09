# Python python-docx Manipulation Patterns

When Phase 6 of the `deep-science-writer` skill requires generating or editing `.docx` files, use these proven patterns to avoid XML corruption or missing dependencies.

## Dependencies
Ensure libraries are installed dynamically if missing:
```python
import sys, subprocess
try:
    import docx
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-docx", "-q"])
    import docx

try:
    import fitz # PyMuPDF for reading PDFs
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyMuPDF", "-q"])
    import fitz
```

## Safely Deleting a Section
To replace hallucinated content or rewrite a specific section, you cannot just clear the text (which leaves empty paragraph blocks). You must remove the XML element:
```python
doc = docx.Document(path)
start_idx = -1

# 1. Find the target section
for i, p in enumerate(doc.paragraphs):
    if "Target Heading Text" in p.text:
        start_idx = i
        break

# 2. Remove the element and everything after it
if start_idx != -1:
    for p in doc.paragraphs[start_idx:]:
        p._element.getparent().remove(p._element)

# 3. Append new content
doc.add_heading('New Verified Section', level=2)
doc.add_paragraph('New content...')
```

## User Preferences
- Always save final outputs to the user's preferred directory (e.g., `D:\` drive on Windows) unless instructed otherwise.