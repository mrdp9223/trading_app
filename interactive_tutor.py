import argparse
import json
import os
from datetime import datetime, timedelta
from typing import List, Tuple

import PyPDF2


def load_pdf_pages(pdf_path: str) -> int:
    """Return number of pages in the PDF."""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        return len(reader.pages)


def extract_text(pdf_path: str, start: int, end: int) -> str:
    """Extract text from page range (1-indexed inclusive)."""
    text_parts: List[str] = []
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for i in range(start - 1, min(end, len(reader.pages))):
            page = reader.pages[i]
            page_text = page.extract_text() or ""
            text_parts.append(page_text.strip())
    return "\n".join(text_parts)


def generate_schedule(page_count: int, days: int = 60, revision_every: int = 7) -> List[dict]:
    """Create a reading schedule for the given number of pages and days."""
    pages_per_day = page_count // days
    remainder = page_count % days
    schedule = []
    page = 1
    for day in range(1, days + 1):
        start = page
        end = page + pages_per_day - 1
        if remainder > 0:
            end += 1
            remainder -= 1
        schedule.append({"day": day, "start_page": start, "end_page": end, "revision": False})
        page = end + 1
    # Mark revision days
    for i in range(revision_every, days + 1, revision_every):
        schedule[i - 1]["revision"] = True
    return schedule


def annotate_with_dates(schedule: List[dict], start_date: datetime) -> None:
    """Add dates to the schedule in-place."""
    for item in schedule:
        item["date"] = start_date.strftime("%Y-%m-%d")
        start_date += timedelta(days=1)


def blank_word_question(sentence: str) -> Tuple[str, str]:
    """Create a simple fill-in-the-blank question from a sentence."""
    words = [w for w in sentence.split() if w.isalpha()]
    if len(words) < 4:
        return sentence, ""
    import random
    idx = random.randint(0, len(words) - 1)
    answer = words[idx]
    words[idx] = "_____"
    question = " ".join(words)
    return question, answer


def generate_quiz(text: str, num_questions: int = 3) -> List[Tuple[str, str]]:
    """Generate basic quiz questions from text."""
    import random
    sentences = [s.strip() for s in text.split('.') if len(s.split()) > 3]
    questions = []
    for _ in range(min(num_questions, len(sentences))):
        s = random.choice(sentences)
        q, a = blank_word_question(s)
        if q and a:
            questions.append((q, a))
    return questions


def save_schedule(schedule: List[dict], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(schedule, f, indent=2)


def load_schedule(path: str) -> List[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def cmd_create(args: argparse.Namespace) -> None:
    pages = load_pdf_pages(args.pdf)
    schedule = generate_schedule(pages, args.days, args.revision_every)
    start_date = datetime.strptime(args.start, "%Y-%m-%d")
    annotate_with_dates(schedule, start_date)
    save_schedule(schedule, args.output)
    print(f"Schedule saved to {args.output}. Total pages: {pages}")


def cmd_show(args: argparse.Namespace) -> None:
    schedule = load_schedule(args.schedule)
    if args.day < 1 or args.day > len(schedule):
        print("Day out of range")
        return
    item = schedule[args.day - 1]
    print(f"Day {item['day']} - {item['date']}")
    if item["revision"]:
        print("Revision Day")
    print(f"Read pages {item['start_page']} to {item['end_page']}")
    text = extract_text(args.pdf, item['start_page'], item['end_page'])
    questions = generate_quiz(text)
    if questions:
        print("\nQuiz:")
        for i, (q, a) in enumerate(questions, 1):
            print(f"Q{i}: {q}")
            print(f"A{i}: {a}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Interactive PDF Tutor")
    sub = parser.add_subparsers(dest="cmd")

    create_p = sub.add_parser("create", help="Create study schedule")
    create_p.add_argument("pdf", help="Path to PDF file")
    create_p.add_argument("--start", default=datetime.now().strftime("%Y-%m-%d"), help="Start date YYYY-MM-DD")
    create_p.add_argument("--days", type=int, default=60, help="Number of study days")
    create_p.add_argument("--revision-every", type=int, default=7, help="Revision interval (days)")
    create_p.add_argument("--output", default="schedule.json", help="Output schedule JSON path")
    create_p.set_defaults(func=cmd_create)

    show_p = sub.add_parser("show", help="Show lesson for a given day")
    show_p.add_argument("schedule", help="Schedule JSON path")
    show_p.add_argument("pdf", help="Path to PDF file")
    show_p.add_argument("--day", type=int, required=True, help="Day number to display")
    show_p.set_defaults(func=cmd_show)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
