---
name: read-pdf-document
description: Extract and analyze PDF content — financial reports, legal documents, whitepapers, research papers.
auto-activate: true
---

# PDF Document Processing
Read and extract information from PDF documents.

## Tools & Process
- **code_execution**: Use Python libraries (PyPDF2, pdfplumber) to extract text and tables
- **browse_page**: If PDF is hosted online, read the web version
- **remember_fact**: Store extracted key data

## Process
1. **Extract**: code_execution with Python to parse PDF text content
2. **Tables**: Use pdfplumber for structured table extraction
3. **Analyze**: Identify key sections, figures, and data points
4. **Summarize**: Generate actionable summary
5. **Store**: remember_fact with source, key findings, extracted data
