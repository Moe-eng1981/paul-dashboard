# 🥐 PAUL Group · Sales Intelligence Dashboard

## Deploy to Streamlit Cloud (Step by Step)

### Step 1 — GitHub
1. Go to https://github.com and create a free account
2. Click **"New repository"**
3. Name it `paul-dashboard`
4. Click **"Create repository"**
5. Drag and drop these files into the repository:
   - `app.py`
   - `requirements.txt`
6. Click **"Commit changes"**

### Step 2 — Streamlit Cloud
1. Go to https://streamlit.io/cloud
2. Sign in with your GitHub account
3. Click **"New app"**
4. Select your `paul-dashboard` repository
5. Main file path: `app.py`
6. Click **"Deploy"**

Your dashboard will be live at:
`https://[your-name]-paul-dashboard.streamlit.app`

---

## Your Sales File Format

| Column | Example |
|--------|---------|
| Country | Qatar |
| Store | Le Chariot City Center Mall |
| Format | PAUL Le Chariot |
| AZ Year | 2025 |
| Month | Jan |
| Week | 48 |
| Order Type Group | Take Away |
| # Tickets | 91 |
| Total Net Sales | 1019.5 |

**AZ Year 2025 = Feb 2025 → Jan 2026**

---

## Budget File Format

| Column | Example |
|--------|---------|
| Country | Qatar |
| Store | Le Chariot City Center Mall |
| AZ Year | 2025 |
| Month | Jan |
| Budget | 45000 |
