import sys
import os
import re
import csv
from bs4 import BeautifulSoup

def parse_section_parts(filename: str):
    # filename like: 1.1.malaria_an_example.html
    base = os.path.splitext(os.path.basename(filename))[0]
    parts = base.split(".", 2)  # ["1", "1", "malaria_an_example"]
    if len(parts) >= 2:
        section_no = ".".join(parts[:2])
        section_name = parts[2] if len(parts) == 3 else ""
    else:
        section_no = ""
        section_name = base
    return section_no, section_name

def extract_long_questions(html_text: str):
    soup = BeautifulSoup(html_text, "lxml")
    rows = []
    # Same DOM structure: rows of .TableHover; question text in .EnglishDiv p / .UrduDiv p
    for row in soup.select("#chooseQuestionsByChapterIDs .TableHover"):
        qid = row.get("id")
        eng_p = row.select_one(".EnglishDiv p")
        urd_p = row.select_one(".UrduDiv p")

        eng = (eng_p.get_text(" ", strip=True) if eng_p else "").replace("\xa0", " ")
        urd = (urd_p.get_text(" ", strip=True) if urd_p else "").replace("\xa0", " ")

        rows.append({"id": qid, "english": eng, "urdu": urd})
    return rows

def main():
    if len(sys.argv) < 3:
        print("Usage: python long_script.py <path_up_to_long_folder> <book_name>")
        print("Example: python long_script.py 9th_class/biology/chapter1/long biology")
        sys.exit(1)

    long_folder = sys.argv[1].rstrip(r"\/")
    book_name = sys.argv[2]

    if not os.path.isdir(long_folder):
        print(f"❌ Not a directory: {long_folder}")
        sys.exit(1)

    # Derive chapter_no from path (expects 'chapter<number>' in the path)
    m = re.search(r"(chapter\d+)", long_folder.replace("\\", "/"), flags=re.IGNORECASE)
    chapter_no = m.group(1) if m else ""

    # Ensure CSV output dir
    out_dir = os.path.join("csv", "9th_class/long")
    os.makedirs(out_dir, exist_ok=True)

    # Avoid clashing with short questions CSV
    csv_path = os.path.join(out_dir, f"{book_name}.csv")

    fieldnames = ["chapter_no", "section_no", "section_name", "id", "english", "urdu"]

    file_exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists or os.path.getsize(csv_path) == 0:
            writer.writeheader()

        total_written = 0
        # Process all HTML files in the /long folder
        for name in sorted(os.listdir(long_folder)):
            if not name.lower().endswith(".html"):
                continue

            file_path = os.path.join(long_folder, name)
            try:
                with open(file_path, "r", encoding="utf-8") as fp:
                    html_content = fp.read()
            except Exception as e:
                print(f"⚠️ Skipping {file_path}: {e}")
                continue

            section_no, section_name = parse_section_parts(name)
            rows = extract_long_questions(html_content)

            for r in rows:
                writer.writerow({
                    "chapter_no": chapter_no,
                    "section_no": section_no,
                    "section_name": section_name,
                    "id": r["id"],
                    "english": r["english"],
                    "urdu": r["urdu"],
                })
                total_written += 1

    print(f"✅ Done. Appended {total_written} long questions to {csv_path}")

if __name__ == "__main__":
    main()
