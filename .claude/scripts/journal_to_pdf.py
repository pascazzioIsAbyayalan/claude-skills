#!/usr/bin/env python3
"""Convert a Monthly Journal Assignment .md to a styled Typst document for PDF rendering."""

import re
import sys
import os
import subprocess
import glob


def escape_typst(text):
    """Escape special Typst characters."""
    replacements = [
        ('\\', '\\\\'),
        ('#', '\\#'),
        ('*', '\\*'),
        ('_', '\\_'),
        ('@', '\\@'),
        ('<', '\\<'),
        ('>', '\\>'),
        ('$', '\\$'),
        ('"', '\\"'),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def parse_header_table(lines):
    info = {}
    for line in lines:
        match = re.match(r'\|\s*\*\*(.+?)\*\*\s*\|\s*(.+?)\s*\|', line)
        if match:
            key = match.group(1).strip()
            val = match.group(2).strip()
            if not val.startswith('---'):
                info[key] = val
    return info


def parse_tech_table(lines):
    rows = []
    for line in lines:
        match = re.match(r'\|\s*(.+?)\s*\|\s*(.*?)\s*\|', line)
        if match:
            key = match.group(1).strip()
            val = match.group(2).strip()
            if key.startswith('---'):
                continue
            rows.append((key, val))
    return rows


def parse_weeks(content):
    weeks = []
    parts = re.split(r'^---\s*$', content, flags=re.MULTILINE)

    for part in parts:
        part = part.strip()
        if not part:
            continue

        week_match = re.search(r'##\s*\*\*Week of:\*\*\s*(.+)', part)
        if not week_match:
            continue

        week_date = week_match.group(1).strip()

        summary_match = re.search(
            r"\*\*Week's Summary\*\*\s*\n(.+?)(?=\n###|\Z)", part, re.DOTALL
        )
        summary = summary_match.group(1).strip() if summary_match else ""

        tech_section = re.search(
            r"\*\*Technologies and Software used this week\*\*\s*\n((?:\|.+\n?)+)",
            part,
        )
        tech_rows = []
        if tech_section:
            tech_rows = parse_tech_table(tech_section.group(1).strip().split('\n'))

        reflection_match = re.search(
            r"\*\*Reflection\*\*\s*\n(.+?)(?=\n###|\n---|\Z)", part, re.DOTALL
        )
        reflection = reflection_match.group(1).strip() if reflection_match else ""

        weeks.append({
            'date': week_date,
            'summary': summary,
            'tech': tech_rows,
            'reflection': reflection,
        })

    return weeks


def generate_typst(info, weeks, month):
    accent = "rgb(\"#6f2dbd\")"
    dark = "rgb(\"#a663cc\")"
    light_bg = "rgb(\"#b9faf8\")"
    border_color = "rgb(\"#b298dc\")"

    info_rows = ""
    fields = [
        ("Student Name", info.get("Student Name", "")),
        ("Student Number", info.get("Student Number", "")),
        ("Degree", info.get("Degree", "")),
        ("Company", info.get("Company Name and Address", "")),
        ("Website", info.get("Company Website", "")),
    ]
    for label, value in fields:
        escaped_val = escape_typst(value)
        if label == "Website" and value:
            info_rows += f"""
      [{label}], [#link("{value}")[#text(fill: {accent})[{escaped_val}]]],"""
        else:
            info_rows += f"""
      [{label}], [{escaped_val}],"""

    weeks_typst = ""
    for i, w in enumerate(weeks):
        escaped_summary = escape_typst(w['summary'])
        escaped_reflection = escape_typst(w['reflection'])
        escaped_date = escape_typst(w['date'])

        tech_rows = ""
        for cat, val in w['tech']:
            escaped_cat = escape_typst(cat)
            if val:
                escaped_val = escape_typst(val)
            else:
                escaped_val = '#text(fill: rgb("#b298dc"), style: "italic")[---]'
            tech_rows += f"""
          [#text(weight: \"bold\", fill: {dark})[{escaped_cat}]], [{escaped_val}],"""

        weeks_typst += f"""
    // ── Week {i + 1} ──
    #block(
      width: 100%,
      clip: true,
      radius: 8pt,
      stroke: 0.5pt + {border_color},
      below: 16pt,
    )[
      #block(
        width: 100%,
        fill: {dark},
        inset: (x: 14pt, y: 10pt),
      )[
        #grid(
          columns: (1fr, auto),
          align: (left, right),
          text(weight: "bold", fill: white, size: 11pt, tracking: 1pt)[WEEK {i + 1}],
          text(fill: rgb("#ffffffcc"), size: 9.5pt)[{escaped_date}],
        )
      ]

      #block(inset: (x: 16pt, y: 12pt), width: 100%)[
        #text(weight: "bold", fill: {accent}, size: 10pt, tracking: 0.5pt)[#sym.arrow.r WEEK'S SUMMARY]
        #v(6pt)
        #text(size: 9.5pt, fill: rgb("#333333"))[#par(justify: true)[{escaped_summary}]]
      ]

      #line(length: 100%, stroke: 0.5pt + {border_color})

      #block(inset: (x: 16pt, y: 12pt), width: 100%)[
        #text(weight: "bold", fill: {accent}, size: 10pt, tracking: 0.5pt)[#sym.circle.filled.small TECHNOLOGIES \\& SOFTWARE]
        #v(6pt)
        #table(
          columns: (35%, 65%),
          stroke: 0.5pt + rgb("#eeeeee"),
          inset: 6pt,
          fill: (x, y) => if y == 0 {{ rgb("#b8c0eb") }} else {{ none }},
          align: (left, left),
          table.header(
            [#text(weight: "bold", size: 8pt, fill: {dark}, tracking: 0.5pt)[CATEGORY]],
            [#text(weight: "bold", size: 8pt, fill: {dark}, tracking: 0.5pt)[DETAILS]],
          ),{tech_rows}
        )
      ]

      #line(length: 100%, stroke: 0.5pt + {border_color})

      #block(inset: (x: 16pt, y: 12pt), width: 100%)[
        #text(weight: "bold", fill: {accent}, size: 10pt, tracking: 0.5pt)[#sym.diamond.stroked REFLECTION]
        #v(6pt)
        #text(size: 9.5pt, fill: rgb("#333333"))[#par(justify: true)[{escaped_reflection}]]
      ]
    ]
"""

    escaped_month = escape_typst(month)
    escaped_name = escape_typst(info.get("Student Name", ""))
    escaped_degree = escape_typst(info.get("Degree", ""))

    return f"""#set page(
  paper: "a4",
  margin: (top: 24mm, bottom: 24mm, left: 20mm, right: 20mm),
  footer: context [
    #line(length: 100%, stroke: 0.3pt + rgb("#b298dc"))
    #v(4pt)
    #grid(
      columns: (1fr, auto, 1fr),
      align: (left, center, right),
      text(size: 7.5pt, fill: rgb("#a663cc"))[{escaped_name}],
      text(size: 7.5pt, fill: rgb("#a663cc"))[#counter(page).display("1 / 1", both: true)],
      text(size: 7.5pt, fill: rgb("#a663cc"))[{escaped_month} -- Work Placement],
    )
  ],
)

#set text(font: "Helvetica Neue", size: 10pt, fill: rgb("#1a1a2e"))
#set par(leading: 0.7em)

// ── Title ──
#align(center)[
  #v(8pt)
  #text(size: 26pt, weight: "bold", fill: {accent}, tracking: 2pt)[MONTHLY JOURNAL]
  #v(2pt)
  #text(size: 11pt, fill: rgb("#a663cc"), style: "italic")[{escaped_month} --- Work Placement Report]
  #v(4pt)
]
#line(length: 100%, stroke: 2.5pt + {accent})
#v(16pt)

// ── Student Info ──
#table(
  columns: (35%, 65%),
  stroke: 0.5pt + rgb("#dddddd"),
  inset: 8pt,
  fill: (x, y) => if calc.rem(x, 2) == 0 {{ {dark} }} else {{ {light_bg} }},
  align: (left, left),{info_rows}
)
#v(20pt)

// ── Weeks ──
{weeks_typst}

// ── End ──
#v(12pt)
#line(length: 100%, stroke: 1.5pt + {accent})
#v(4pt)
#align(center)[
  #text(size: 8pt, fill: rgb("#a663cc"))[{escaped_name} #sym.bullet {escaped_degree} #sym.bullet {escaped_month}]
]
"""


def convert_file(md_path, pdf_dir):
    with open(md_path, 'r') as f:
        content = f.read()

    lines = content.strip().split('\n')

    header_lines = []
    rest_start = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('|'):
            header_lines.append(line)
        elif header_lines:
            rest_start = i
            break

    info = parse_header_table(header_lines)
    month = info.get('Month', 'Unknown')

    rest_content = '\n'.join(lines[rest_start:])
    weeks = parse_weeks(rest_content)

    typst_content = generate_typst(info, weeks, month)

    basename = os.path.splitext(os.path.basename(md_path))[0]
    typst_path = os.path.join(pdf_dir, f"{basename}.typ")
    pdf_path = os.path.join(pdf_dir, f"{basename}.pdf")

    with open(typst_path, 'w') as f:
        f.write(typst_content)

    result = subprocess.run(
        ['typst', 'compile', typst_path, pdf_path],
        capture_output=True, text=True
    )

    os.remove(typst_path)

    if result.returncode != 0:
        print(f"ERROR compiling {basename}: {result.stderr}", file=sys.stderr)
        return False

    print(f"  -> {pdf_path}")
    return True


def main():
    journal_dir = sys.argv[1] if len(sys.argv) > 1 else "/Users/gpascaci/Desktop/Internship/Internship Docs/Journal Report"
    pdf_dir = os.path.join(journal_dir, "PDF")
    os.makedirs(pdf_dir, exist_ok=True)

    md_files = sorted(glob.glob(os.path.join(journal_dir, "*Monthly Journal Assignment.md")))

    if not md_files:
        print("No Monthly Journal Assignment .md files found.")
        sys.exit(1)

    print(f"Found {len(md_files)} journal(s) to convert:\n")
    success = 0
    for md_path in md_files:
        basename = os.path.basename(md_path)
        print(f"  Converting: {basename}")
        if convert_file(md_path, pdf_dir):
            success += 1

    print(f"\nDone: {success}/{len(md_files)} converted to PDF in {pdf_dir}")


if __name__ == '__main__':
    main()
