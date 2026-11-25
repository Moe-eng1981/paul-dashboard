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
   - `paul_core.py`
   - the whole `pages/` folder
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


## 🧭 What's inside

Upload your sales file (and budget) **once** in the sidebar. Every page uses it.

| Page | What it does |
|------|--------------|
| 🥐 **app** (home) | The full Sales Intelligence dashboard: TY vs LY, LFL, budget, channel mix, breakdowns |
| 🏪 **Store Flash** | One-glance weekly card per store, country or format, with automatic alerts (drops vs LY, footfall vs basket issues, weeks-below-LY streaks, budget gap) |
| 📧 **Weekly Report** | Writes the weekly management email for you: headlines, YTD, country and channel split, wins, stores needing attention. Download as HTML/text or open in your email app |
| 📈 **Forecast** | Projects the rest of the AZ year per store (LY × recent trend, so it keeps seasonality), shows who will hit budget and the weekly run-rate needed, and drafts next year's budget as a ready-to-upload file |
| 📣 **Marketing Impact** | Measures campaign uplift vs the weeks before, vs last year and vs stores that weren't targeted. Optional Metricool export overlay |
| 🏆 **Benchmarking** | League table with a fair 0–100 score (growth & execution, not size), peer ranking by format/country, growth quadrant and talking points |

### Campaign file format (Marketing Impact)

| Campaign | Channel | Country | Store | AZ Year | Start Week | End Week |
|----------|---------|---------|-------|---------|------------|----------|
| Summer Iced Drinks | Instagram | Qatar | All | 2025 | 30 | 33 |

You can also use `Start Date` / `End Date` instead of weeks, or type campaigns directly into the page.
A template can be downloaded from the page's sidebar.

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
