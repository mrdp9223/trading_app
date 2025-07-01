# Trading App and PDF Tutor

This repository contains a Streamlit trading application and a simple command line
utility to create a study plan for a PDF textbook.

## Interactive PDF Tutor

`interactive_tutor.py` helps you split a PDF book into daily lessons with
periodic revision days. It can also generate a few basic quiz questions from the
assigned pages.

### Usage

1. **Create a schedule** (default 60 days starting today):

   ```bash
   python interactive_tutor.py create path/to/book.pdf --start YYYY-MM-DD --days 60
   ```

   This writes a `schedule.json` file describing the daily reading plan.

2. **Show a day's lesson and quiz**:

   ```bash
   python interactive_tutor.py show schedule.json path/to/book.pdf --day 1
   ```

   The script prints the pages to read and a few fill-in-the-blank questions
   generated from those pages.

The quiz generation uses very simple heuristics and may not always produce
meaningful questions, but it provides a lightweight way to review material.

## Requirements

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Trading App

`trading_app.py` is an existing Streamlit application for generating intraday
buy signals using the Zerodha Kite Connect API.
