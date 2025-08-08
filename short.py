import sys
import os
import re
import csv
from bs4 import BeautifulSoup

def parse_section_parts(filename: str):
    # filename like: 1.1.biology_and_its_branches.html
    base = os.path.splitext(os.path.basename(filename))[0]  # "1.1.biology_and_its_branches"
    parts = base.split(".", 2)  # ["1", "1", "biology_and_its_branches"]
    if len(parts) >= 2:
        section_no = ".".join(parts[:2])
        section_name = parts[2] if len(parts) == 3 else ""
    else:
        # fallback: whole base is name, no section number
        section_no = ""
        section_name = base
    return section_no, section_name

def extract_questions(html_text: str):
    soup = BeautifulSoup(html_text, "lxml")
    rows = []
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
        print("Usage: python script.py <path_up_to_short_folder> <book_name>")
        print("Example: python script.py 9th_class/biology/chapter1/short biology")
        sys.exit(1)

    short_folder = sys.argv[1].rstrip(r"\/")
    book_name = sys.argv[2]

    if not os.path.isdir(short_folder):
        print(f"❌ Not a directory: {short_folder}")
        sys.exit(1)

    # Derive chapter_no from path (expects 'chapter<number>' somewhere in path)
    m = re.search(r"(chapter\d+)", short_folder.replace("\\", "/"), flags=re.IGNORECASE)
    chapter_no = m.group(1) if m else ""

    # Ensure CSV output dir
    out_dir = os.path.join("csv", "9th_class/short")
    os.makedirs(out_dir, exist_ok=True)
    csv_path = os.path.join(out_dir, f"{book_name}.csv")

    fieldnames = ["chapter_no", "section_no", "section_name", "id", "english", "urdu"]

    # Create file (and header) if new
    file_exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists or os.path.getsize(csv_path) == 0:
            writer.writeheader()

        total_written = 0
        for name in sorted(os.listdir(short_folder)):
            if not name.lower().endswith(".html"):
                continue

            file_path = os.path.join(short_folder, name)
            try:
                with open(file_path, "r", encoding="utf-8") as fp:
                    html_content = fp.read()
            except Exception as e:
                print(f"⚠️ Skipping {file_path}: {e}")
                continue

            section_no, section_name = parse_section_parts(name)
            rows = extract_questions(html_content)

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

    print(f"✅ Done. Appended {total_written} rows to {csv_path}")

if __name__ == "__main__":
    main()
