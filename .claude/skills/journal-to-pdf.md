# Journal to PDF

Convert Monthly Journal Assignment markdown files into professionally formatted PDFs.

## When to use

When the user asks to convert, export, or generate PDFs from their monthly journal assignments. Trigger phrases: "convert journal", "journal to pdf", "export journal", "generate journal pdf".

## Instructions

1. Run the converter script on the Journal Report directory:

```bash
python3 .claude/scripts/journal_to_pdf.py "<path-to-Journal-Report-directory>"
```

This will:
- Find all `*Monthly Journal Assignment.md` files in the directory
- Parse the header table (student info) and weekly entries (summary, technologies, reflection)
- Generate a styled Typst document with:
  - Purple/aqua color scheme (#6f2dbd, #a663cc, #b298dc, #b8c0eb, #b9faf8)
  - Student info card with purple label column
  - Week blocks with purple header bars showing week number and date
  - Technology tables with sky-blue header row
  - Page footers with student name, page count, and month
- Compile to PDF via `typst compile`
- Save PDFs to the `PDF/` subfolder

2. If the user provides a custom path, pass it as the argument. The script also accepts no argument and defaults to a sensible location.

3. Report which files were converted and their output paths.

## Requirements

- `typst` must be installed (`brew install typst`)
- Journal `.md` files must follow the standard format: header table with student info, then `---`-separated weekly entries with Section 1 (Summary), Section 2 (Technologies table), Section 3 (Reflection)
