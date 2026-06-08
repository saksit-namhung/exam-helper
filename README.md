# Exam Helper

A web-based exam practice application built with Flask. It reads exam data from local JSON files and presents questions one at a time in the browser.

## Requirements

- Python 3.8+

## Setup

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure the data directory**

   Edit `app.py` and set `DATA_DIR` to the folder containing your exam JSON files:

   ```python
   DATA_DIR = r"C:\path\to\your\exam\files"   # Windows example
   # DATA_DIR = "/path/to/your/exam/files"     # macOS / Linux example
   ```

3. **Run the app**

   ```bash
   python app.py
   ```

   Open your browser and go to <http://127.0.0.1:5000>.

## Features

- Supports single-choice, multiple-choice, and dropdown-selection questions
- Choose the number of questions per session
- Sequential or randomized question order
- Immediate feedback after each answer
- Final score summary at the end of each session
