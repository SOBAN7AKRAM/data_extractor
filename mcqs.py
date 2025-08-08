import sys
import os
import re
import csv
from bs4 import BeautifulSoup

def parse_section_parts(filename: str):
    # filename like: 1.1.quranic_instructions.html
    base = os.path.splitext(os.path.basename(filename))[0]
    parts = base.split(".", 2)  # ["1", "1", "quranic_instructions"]
    if len(parts) >= 2:
        section_no = ".".join(parts[:2])
        section_name = parts[2] if len(parts) == 3 else ""
    else:
        section_no = ""
        section_name = base
    return section_no, section_name

def _clean(text):
    return (text or "").replace("\xa0", " ").strip()

def extract_mcqs(html_text: str):
    """
    Returns a list of dicts:
    {
      id, question_en, question_ur,
      option_a_en, option_a_ur, option_b_en, option_b_ur,
      option_c_en, option_c_ur, option_d_en, option_d_ur,
      correct_option
    }
    """
    soup = BeautifulSoup(html_text, "lxml")
    rows = []

    # Each MCQ sits in a .TableHover row; options are <li> children
    for row in soup.select("#chooseQuestionsByChapterIDs .TableHover"):
        qid = row.get("id")
        eng_p = row.select_one(".EnglishDiv p")
        urd_p = row.select_one(".UrduDiv p")
        question_en = _clean(eng_p.get_text(" ", strip=True) if eng_p else "")
        question_ur = _clean(urd_p.get_text(" ", strip=True) if urd_p else "")

        # Default option containers
        opts = {
            "A": {"en": "", "ur": ""},
            "B": {"en": "", "ur": ""},
            "C": {"en": "", "ur": ""},
            "D": {"en": "", "ur": ""},
        }
        correct_letter = ""

        # Find all <li> for options
        for li in row.select("ul > li"):
            # Get letter like "(A)" -> "A"
            letter_span = li.find("span")
            letter = ""
            if letter_span and letter_span.get_text():
                letter = letter_span.get_text().strip().strip("()").upper()

            # English/Urdu option text
            en_p = li.select_one(".En p")
            ur_p = li.select_one(".Ur p")
            en_txt = _clean(en_p.get_text(" ", strip=True) if en_p else "")
            ur_txt = _clean(ur_p.get_text(" ", strip=True) if ur_p else "")

            if letter in opts:
                opts[letter]["en"] = en_txt
                opts[letter]["ur"] = ur_txt

            # Detect correct answer
            if "correctAnswer" in (li.get("class") or []):
                # Prefer the span’s letter; otherwise parse from thiscorrect attr e.g. "1-(A)"
                if letter:
                    correct_letter = letter
                else:
                    tc = li.get("thiscorrect", "")
                    m = re.search(r"-\(([A-D])\)", tc, re.IGNORECASE)
                    if m:
                        correct_letter = m.group(1).upper()

        rows.append({
            "id": qid,
            "question_en": question_en,
            "question_ur": question_ur,
            "option_a_en": opts["A"]["en"], "option_a_ur": opts["A"]["ur"],
            "option_b_en": opts["B"]["en"], "option_b_ur": opts["B"]["ur"],
            "option_c_en": opts["C"]["en"], "option_c_ur": opts["C"]["ur"],
            "option_d_en": opts["D"]["en"], "option_d_ur": opts["D"]["ur"],
            "correct_option": correct_letter,
        })

    return rows

def main():
    if len(sys.argv) < 3:
        print("Usage: python mcqs_script.py <path_up_to_mcqs_folder> <book_name>")
        print("Example: python mcqs_script.py 9th_class/biology/chapter1/mcqs biology")
        sys.exit(1)

    mcqs_folder = sys.argv[1].rstrip(r"\/")
    book_name = sys.argv[2]

    if not os.path.isdir(mcqs_folder):
        print(f"❌ Not a directory: {mcqs_folder}")
        sys.exit(1)

    # chapter_no from path (expects 'chapter<number>')
    m = re.search(r"(chapter\d+)", mcqs_folder.replace("\\", "/"), flags=re.IGNORECASE)
    chapter_no = m.group(1) if m else ""

    # Output CSV path
    out_dir = os.path.join("csv", "9th_class/mcqs")
    os.makedirs(out_dir, exist_ok=True)
    csv_path = os.path.join(out_dir, f"{book_name}.csv")

    fieldnames = [
        "chapter_no", "section_no", "section_name",
        "id", "question_en", "question_ur",
        "option_a_en", "option_a_ur",
        "option_b_en", "option_b_ur",
        "option_c_en", "option_c_ur",
        "option_d_en", "option_d_ur",
        "correct_option"
    ]

    file_exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists or os.path.getsize(csv_path) == 0:
            writer.writeheader()

        total_written = 0
        for name in sorted(os.listdir(mcqs_folder)):
            if not name.lower().endswith(".html"):
                continue

            file_path = os.path.join(mcqs_folder, name)
            try:
                with open(file_path, "r", encoding="utf-8") as fp:
                    html_content = fp.read()
            except Exception as e:
                print(f"⚠️ Skipping {file_path}: {e}")
                continue

            section_no, section_name = parse_section_parts(name)
            rows = extract_mcqs(html_content)

            for r in rows:
                writer.writerow({
                    "chapter_no": chapter_no,
                    "section_no": section_no,
                    "section_name": section_name,
                    **r
                })
                total_written += 1

    print(f"✅ Done. Appended {total_written} MCQs to {csv_path}")

if __name__ == "__main__":
    main()
