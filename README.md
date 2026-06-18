# Student Database Management — Web Edition

This is a browser-based version of your Tkinter desktop app. The business logic
(`models.py`, `system.py`, `exceptions.py`, `utils.py`) is copied unchanged from your
original repo. `gui.py` has been replaced by `app.py` (a Flask app) plus HTML
templates in `templates/` and a stylesheet in `static/style.css`, styled to match
the original app's dark dashboard look.

It has the same features as the desktop app: register/update/delete students,
mark attendance, create and collect fees, schedule exams, enter/update results,
view performance stats, generate JSON/CSV reports, and view notifications.

## Run it locally first

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Visit `http://localhost:5000` in your browser.

## Put it on GitHub

Replace the contents of your existing repo with these files (keep the same repo
name if you like), or push this as a new repo. At minimum your repo should contain:
`app.py`, `system.py`, `models.py`, `exceptions.py`, `utils.py`, `requirements.txt`,
`Procfile`, `templates/`, `static/`.

```bash
git add .
git commit -m "Add web version with Flask front end"
git push
```

## Deploy it for free on Render (gives you a public link)

1. Go to https://render.com and sign up / log in (you can sign in with GitHub).
2. Click **New +** → **Web Service**.
3. Connect your GitHub account and select this repository.
4. Fill in the settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** Free
5. Click **Create Web Service**. Render will build and deploy automatically.
6. After a minute or two you'll get a public URL like
   `https://student-database-management.onrender.com` — that's your shareable link.

Any time you push new commits to GitHub, Render redeploys automatically.

### Alternatives to Render
- **Railway** (https://railway.app) — similar git-based deploy, also has a free trial.
- **PythonAnywhere** (https://www.pythonanywhere.com) — good if you want a more
  manual, beginner-friendly setup with a permanent free tier (lower traffic limits).

## Important: data persistence

Like the original app, data is stored in a local JSON file (`sms_data.json`) on
the server's disk. Most free hosting tiers (including Render's free plan) use an
**ephemeral filesystem** — meaning the file is wiped whenever the app restarts or
redeploys (e.g. after inactivity, or after you push new code). This is fine for
demos, coursework submissions, or short-lived sharing, but isn't reliable for
long-term real data.

If you need data to survive restarts, the next step would be swapping the JSON
file for a real database (e.g. SQLite with a persistent disk on Render, or
Postgres) — happy to help with that whenever you're ready.

## Notes on what changed vs. the original

- All Tkinter widgets are gone; the same actions are now plain HTML forms and tables.
- Subject choices for results are a free-text field instead of dynamic dropdowns
  (the original GUI's course/subject auto-fill logic was view-only convenience,
  not part of the core system).
- JSON/CSV "Save report" buttons now trigger a file **download** in your browser
  instead of saving to the server's disk where you couldn't see it.
