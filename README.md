# Track That

A simple web app to track your job and internship applications.

## Stack

- **Backend:** Python, Flask
- **Templates:** Jinja2
- **Frontend:** HTML5, Bootstrap 5, jQuery, custom CSS
- **Data:** SQLite (persistent; stored in `applications.db`)

## Setup

```bash
cd "Track That"
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Features

- **List** all applications with filter by status (Applied, Interviewing, Offer, Rejected, Withdrawn, Accepted)
- **Add** new applications (company, role, status, date applied, job URL, notes)
- **Edit** and **delete** existing applications

Data is stored in `applications.db` in the project folder.
