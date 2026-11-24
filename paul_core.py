"""
PAUL Group · shared core
Themes, CSS, data loaders and calculation helpers used by every page.
"""
import streamlit as st
import pandas as pd
import numpy as np
import io

# ─────────────────────────────────────────
# THEME
# ─────────────────────────────────────────
THEMES = {
    "dark": {
        "bg":         "#0F0C07",
        "bg2":        "#181209",
        "bg3":        "#221A0D",
        "card":       "#181209",
        "border":     "rgba(201,168,76,0.20)",
        "text":       "#F0E6CC",
        "text_dim":   "rgba(240,230,204,0.5)",
        "accent":     "#C9A84C",
        "accent2":    "#E2C97E",
        "green":      "#5DBB8A",
        "red":        "#D96B6B",
        "blue":       "#6B9FD4",
        "chart_bg":   "#181209",
        "grid":       "rgba(201,168,76,0.07)",
        "sidebar_bg": "#181209",
    },
    "light": {
        "bg":         "#F4F6F9",
        "bg2":        "#FFFFFF",
        "bg3":        "#EEF2F7",
        "card":       "#FFFFFF",
        "border":     "#D0D7E3",
        "text":       "#1A2A3A",
        "text_dim":   "#6B7A8D",
        "accent":     "#1B3A6B",
        "accent2":    "#2E6DA4",
        "green":      "#1E8449",
        "red":        "#C0392B",
        "blue":       "#2E6DA4",
        "chart_bg":   "#FFFFFF",
        "grid":       "rgba(0,0,0,0.05)",
        "sidebar_bg": "#1B3A6B",
    }
}

FM_ORDER = ['Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec','Jan']

# ─────────────────────────────────────────
# CSS INJECTION
# ─────────────────────────────────────────
def inject_css(t):
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif !important;
    }}
    .stApp {{
        background: {t['bg']} !important;
    }}
    section[data-testid="stSidebar"] {{
        background: {t['sidebar_bg']} !important;
    }}
    section[data-testid="stSidebar"] * {{
        color: {'#F0E6CC' if t['sidebar_bg'] == '#181209' else '#FFFFFF'} !important;
    }}
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stRadio label,
    section[data-testid="stSidebar"] .stFileUploader label {{
        color: {'rgba(240,230,204,0.6)' if t['sidebar_bg'] == '#181209' else 'rgba(255,255,255,0.7)'} !important;
        font-size: 11px !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }}
    .stSelectbox > div > div {{
        background: {t['bg3']} !important;
        border: 1px solid {t['border']} !important;
        color: {t['text']} !important;
        border-radius: 8px !important;
    }}
    .stRadio > div {{ gap: 4px; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 100% !important;
    }}

    /* KPI Cards */
    .kpi-card {{
        background: {t['card']};
        border: 1px solid {t['border']};
        border-top: 3px solid {t['accent']};
        border-radius: 10px;
        padding: 16px 14px 12px 14px;
        height: 110px;
    }}
    .kpi-label {{
        font-size: 10px;
        color: {t['text_dim']};
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
        margin-bottom: 6px;
    }}
    .kpi-value {{
        font-size: 26px;
        font-weight: 700;
        color: {t['text']};
        line-height: 1;
        margin-bottom: 5px;
        font-family: 'DM Mono', monospace;
    }}
    .kpi-sub {{
        font-size: 11px;
        font-weight: 500;
    }}
    .kpi-pos {{ color: {t['green']}; }}
    .kpi-neg {{ color: {t['red']}; }}
    .kpi-neu {{ color: {t['text_dim']}; }}

    /* Section headers */
    .section-hdr {{
        font-size: 13px;
        font-weight: 700;
        color: {t['accent']};
        text-transform: uppercase;
        letter-spacing: 1px;
        padding: 6px 0;
        border-bottom: 2px solid {t['border']};
        margin-bottom: 12px;
    }}

    /* Dividers */
    .divider {{
        border: none;
        border-top: 1px solid {t['border']};
        margin: 14px 0;
    }}

    /* Filter pills */
    .filter-row {{
        background: {t['bg2']};
        border: 1px solid {t['border']};
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 14px;
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
    }}

    /* Dataframe */
    .stDataFrame {{
        border: 1px solid {t['border']} !important;
        border-radius: 8px !important;
    }}

    /* Top bar */
    .top-bar {{
        background: {t['accent']};
        border-radius: 10px;
        padding: 14px 20px;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }}
    .top-bar-title {{
        font-size: 20px;
        font-weight: 700;
        color: {'#1A1000' if t['accent']=='#C9A84C' else '#FFFFFF'};
        letter-spacing: 0.5px;
    }}
    .top-bar-sub {{
        font-size: 11px;
        color: {'rgba(26,16,0,0.65)' if t['accent']=='#C9A84C' else 'rgba(255,255,255,0.7)'};
        margin-top: 2px;
    }}
    </style>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────
# DATA HELPERS
# ─────────────────────────────────────────
def find_col(df, *names):
    norm = {c: c.strip().lower().replace(' ','').replace('#','').replace('_','')
            for c in df.columns}
    rev = {v: k for k, v in norm.items()}
    for n in names:
        k = n.lower().replace(' ','').replace('#','').replace('_','')
        if k in rev: return rev[k]
    return None

@st.cache_data(show_spinner="📂 Loading data…")
def load_sales(data, fname):
    df = pd.read_excel(io.BytesIO(data)) if fname.endswith(('.xlsx','.xls')) else pd.read_csv(io.BytesIO(data))

    c_country = find_col(df, 'country')
    c_store   = find_col(df, 'store')
    c_brand   = find_col(df, 'format', 'brand')
    c_channel = find_col(df, 'ordertypegroup', 'ordertype', 'channel')
    c_az_year = find_col(df, 'azyear', 'az year', 'azzear')
    c_month   = find_col(df, 'month')
    c_week    = find_col(df, 'week')
    c_tickets = find_col(df, 'tickets', 'ticket')
    c_sales   = find_col(df, 'totalnetsales', 'totalnet', 'netsales', 'sales', 'revenue')

    if not c_sales:
        st.error(f"❌ Cannot find Sales column. Columns found: {list(df.columns)}")
        return None

    out = pd.DataFrame()
    out['country'] = df[c_country].astype(str).str.strip() if c_country else 'Unknown'
    out['store']   = df[c_store].astype(str).str.strip()   if c_store   else 'Unknown'
    out['brand']   = df[c_brand].astype(str).str.strip()   if c_brand   else 'Unknown'
    out['channel'] = df[c_channel].astype(str).str.strip() if c_channel else 'Unknown'
    out['az_year'] = pd.to_numeric(df[c_az_year], errors='coerce') if c_az_year else np.nan
    out['month']   = df[c_month].astype(str).str.strip()   if c_month   else ''
    out['week']    = pd.to_numeric(df[c_week], errors='coerce') if c_week else np.nan
    out['sales']   = pd.to_numeric(df[c_sales].astype(str).str.replace(',',''), errors='coerce').fillna(0)
    out['tickets'] = pd.to_numeric(df[c_tickets].astype(str).str.replace(',',''), errors='coerce').fillna(0) if c_tickets else 0

    out = out[out['sales'] > 0].copy()
    out = out.drop_duplicates(subset=['country','store','channel','az_year','week','month'])
    return out

@st.cache_data(show_spinner="🎯 Loading budget…")
def load_budget(data, fname):
    df = pd.read_excel(io.BytesIO(data)) if fname.endswith(('.xlsx','.xls')) else pd.read_csv(io.BytesIO(data))
    c_store  = find_col(df, 'store')
    c_country= find_col(df, 'country')
    c_year   = find_col(df, 'azyear', 'year')
    c_month  = find_col(df, 'month')
    c_budget = find_col(df, 'budget', 'target')
    if not c_budget: return None
    out = pd.DataFrame()
    out['store']   = df[c_store].astype(str).str.strip()   if c_store   else ''
    out['country'] = df[c_country].astype(str).str.strip() if c_country else ''
    out['az_year'] = pd.to_numeric(df[c_year], errors='coerce') if c_year else np.nan
    out['month']   = df[c_month].astype(str).str.strip()   if c_month   else ''
    out['budget']  = pd.to_numeric(df[c_budget].astype(str).str.replace(',',''), errors='coerce').fillna(0)
    return out

# ─────────────────────────────────────────
# CALCULATION HELPERS
# ─────────────────────────────────────────
def get_ly(df_all, df_ty):
    """LY: same store + channel + week, az_year - 1 exactly."""
    if df_ty.empty: return pd.DataFrame(columns=df_all.columns)
    keys = set()
    for _, r in df_ty[['store','channel','week','az_year']].drop_duplicates().iterrows():
        if pd.notna(r['az_year']):
            keys.add((r['store'], r['channel'], r['week'], int(r['az_year']) - 1))
    ly_pool = df_all[df_all['az_year'].isin(df_ty['az_year'].dropna().unique() - 1)]
    if ly_pool.empty: return pd.DataFrame(columns=df_all.columns)
    mask = ly_pool.apply(lambda r: (r['store'], r['channel'], r['week'], int(r['az_year'])) in keys, axis=1)
    return ly_pool[mask]

def get_lfl(df_all, df_ty):
    """LFL: stores in same week in both TY and LY."""
    if df_ty.empty: return 0, 0
    ly_pool = df_all[df_all['az_year'].isin(df_ty['az_year'].dropna().unique() - 1)]
    if ly_pool.empty: return 0, 0
    ty_sw = set(zip(df_ty['store'], df_ty['week']))
    ly_sw = set(zip(ly_pool['store'], ly_pool['week']))
    common = ty_sw & ly_sw
    if not common: return 0, 0
    ty_lfl = df_ty[df_ty.apply(lambda r: (r['store'], r['week']) in common, axis=1)]
    ly_lfl = ly_pool[ly_pool.apply(lambda r: (r['store'], r['week']) in common, axis=1)]
    return ty_lfl['sales'].sum(), ly_lfl['sales'].sum()

def get_bgt(bdf, stores, months, az=None):
    if bdf is None or bdf.empty: return 0
    m = bdf['store'].isin(stores) & bdf['month'].isin(months)
    if az: m &= (bdf['az_year'] == az)
    return bdf[m]['budget'].sum()

def safe_pct(a, b):
    return (a - b) / b * 100 if b and b != 0 and pd.notna(b) else np.nan

def fmt(n, dec=0):
    if n is None or (isinstance(n, float) and np.isnan(n)): return "—"
    return f"{n:,.{dec}f}"

def fmt_pct(n, dec=1):
    if n is None or not np.isfinite(float(n) if n is not None else float('nan')): return "—"
    return f"{'+'if n>=0 else ''}{n:.{dec}f}%"

def pclass(n):
    if n is None or (isinstance(n, float) and not np.isfinite(n)): return "kpi-neu"
    return "kpi-pos" if n >= 0 else "kpi-neg"

# ─────────────────────────────────────────
# KPI CARD HTML
# ─────────────────────────────────────────
def kpi(label, value, sub, sub_class="kpi-neu"):
    return f"""<div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub {sub_class}">{sub}</div>
    </div>"""

# ─────────────────────────────────────────
# CHART STYLING
# ─────────────────────────────────────────
def chart_layout(t, height=300, title=None):
    layout = dict(
        paper_bgcolor=t['chart_bg'],
        plot_bgcolor=t['chart_bg'],
        font=dict(family="Inter", color=t['text'], size=11),
        height=height,
        margin=dict(l=10, r=10, t=30 if title else 10, b=10),
        xaxis=dict(gridcolor=t['grid'], tickfont=dict(size=10, color=t['text_dim']),
                   linecolor=t['border'], showline=True),
        yaxis=dict(gridcolor=t['grid'], tickfont=dict(size=10, color=t['text_dim'])),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10, color=t['text_dim'])),
        hoverlabel=dict(bgcolor=t['bg2'], bordercolor=t['border'],
                        font=dict(color=t['text'], size=11)),
    )
    layout['title'] = (dict(text=title, font=dict(size=13, color=t['text']), x=0)
                       if title else dict(text=''))
    return layout

def style_df(df_in, pct_cols, t):
    def color_cell(val):
        try:
            v = float(str(val).replace('%','').replace('+','').replace(',',''))
            return f"color: {t['green']}" if v >= 0 else f"color: {t['red']}"
        except: return ""
    existing = [c for c in pct_cols if c in df_in.columns]
    if existing:
        return df_in.style.applymap(color_cell, subset=existing)
    return df_in.style


MO_IDX = {m: i for i, m in enumerate(FM_ORDER)}


# ─────────────────────────────────────────
# SHARED PAGE SETUP
# Uploads are kept in session_state so a file uploaded on any page
# is available on every other page without re-uploading.
# ─────────────────────────────────────────
def setup_page(title, icon="🥐", require_sales=True):
    """Configure the page, render theme toggle + data uploads in the sidebar.

    Returns (theme_dict, is_dark, sales_df, budget_df).
    """
    st.set_page_config(page_title=f"PAUL · {title}", page_icon=icon,
                       layout="wide", initial_sidebar_state="expanded")
    ss = st.session_state

    with st.sidebar:
        theme_opts = ["Dark", "Light"]
        theme_choice = st.radio("🎨 Theme", theme_opts, horizontal=True,
                                index=theme_opts.index(ss.get("theme_pref", "Dark")))
        ss["theme_pref"] = theme_choice
        t = THEMES["dark"] if theme_choice == "Dark" else THEMES["light"]
        inject_css(t)

        st.markdown("---")
        st.markdown("**📂 Sales Data**")
        sf = st.file_uploader("Upload .xlsx or .csv", type=['xlsx', 'xls', 'csv'],
                              key='sf', label_visibility="collapsed")
        if sf is not None:
            ss["sales_bytes"], ss["sales_name"] = sf.getvalue(), sf.name

        st.markdown("**🎯 Budget** *(optional)*")
        bf = st.file_uploader("Upload .xlsx or .csv", type=['xlsx', 'xls', 'csv'],
                              key='bf', label_visibility="collapsed")
        if bf is not None:
            ss["budget_bytes"], ss["budget_name"] = bf.getvalue(), bf.name

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔄 Cache", use_container_width=True, help="Clear cached calculations"):
                st.cache_data.clear()
                st.rerun()
        with c2:
            if st.button("🗑 Data", use_container_width=True, help="Forget uploaded files"):
                for k in ["sales_bytes", "sales_name", "budget_bytes", "budget_name"]:
                    ss.pop(k, None)
                st.cache_data.clear()
                st.rerun()

        sales_df = budget_df = None
        if ss.get("sales_bytes"):
            sales_df = load_sales(ss["sales_bytes"], ss["sales_name"])
            if sales_df is not None:
                st.success(f"✅ {ss['sales_name']} · {sales_df['store'].nunique()} stores")
        if ss.get("budget_bytes"):
            budget_df = load_budget(ss["budget_bytes"], ss["budget_name"])
            if budget_df is not None:
                st.success(f"✅ Budget · {len(budget_df):,} rows")

        if require_sales and sales_df is None:
            st.info("↑ Upload your sales file to get started")
            st.stop()
        st.markdown("---")

    return t, theme_choice == "Dark", sales_df, budget_df


def top_bar(t, title, subtitle="", right=""):
    txt = '#1A1000' if t['accent'] == '#C9A84C' else '#FFFFFF'
    st.markdown(f"""
<div style="background:{t['accent']};border-radius:10px;padding:14px 20px;margin-bottom:16px;
     display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap">
  <div>
    <div style="font-size:20px;font-weight:700;color:{txt}">{title}</div>
    <div style="font-size:11px;color:{txt};opacity:0.7;margin-top:2px">{subtitle}</div>
  </div>
  <div style="text-align:right;font-size:11px;color:{txt};opacity:0.7">{right}</div>
</div>""", unsafe_allow_html=True)


def section(title):
    st.markdown(f'<div class="section-hdr">{title}</div>', unsafe_allow_html=True)


def callout(t, text, kind="neu"):
    color = {"pos": t['green'], "neg": t['red'], "neu": t['accent'], "info": t['blue']}[kind]
    st.markdown(f"""<div style="background:{t['card']};border:1px solid {t['border']};
        border-left:4px solid {color};border-radius:8px;padding:10px 14px;margin-bottom:8px;
        color:{t['text']};font-size:13px">{text}</div>""", unsafe_allow_html=True)


def filter_frame(df, country="All", brand="All", store="All", channel="All"):
    if country != "All": df = df[df['country'] == country]
    if brand   != "All": df = df[df['brand']   == brand]
    if store   != "All": df = df[df['store']   == store]
    if channel != "All": df = df[df['channel'] == channel]
    return df


def scope_filters(sales_df, prefix, show_store=True, show_channel=False):
    """Common Country / Brand / Store sidebar selectors. Returns dict of selections."""
    with st.sidebar:
        countries = sorted(sales_df['country'].dropna().unique().tolist())
        country = st.selectbox("Country", ["All"] + countries, key=f"{prefix}_country")
        brands = sorted(sales_df['brand'].dropna().unique().tolist())
        brand = st.selectbox("Brand / Format", ["All"] + brands, key=f"{prefix}_brand")
        store = "All"
        if show_store:
            sp = filter_frame(sales_df, country, brand)
            store = st.selectbox("Store", ["All"] + sorted(sp['store'].unique().tolist()),
                                 key=f"{prefix}_store")
        channel = "All"
        if show_channel:
            chs = sorted(sales_df['channel'].dropna().unique().tolist())
            channel = st.selectbox("Channel", ["All"] + chs, key=f"{prefix}_channel")
    return dict(country=country, brand=brand, store=store, channel=channel)


# ─────────────────────────────────────────
# FAST WEEKLY AGGREGATES (vectorised; used by the new pages)
# ─────────────────────────────────────────
def store_week(df):
    """Aggregate to one row per store × az_year × week."""
    return (df.groupby(['country', 'brand', 'store', 'az_year', 'week'], dropna=False)
              .agg(sales=('sales', 'sum'), tickets=('tickets', 'sum'),
                   month=('month', 'first'))
              .reset_index())


def add_ly(sw):
    """Attach LY sales/tickets for the same store and fiscal week (az_year - 1)."""
    ly = sw[['store', 'az_year', 'week', 'sales', 'tickets']].copy()
    ly['az_year'] = ly['az_year'] + 1
    ly = ly.rename(columns={'sales': 'ly_sales', 'tickets': 'ly_tickets'})
    out = sw.merge(ly, on=['store', 'az_year', 'week'], how='left')
    out[['ly_sales', 'ly_tickets']] = out[['ly_sales', 'ly_tickets']].fillna(0)
    return out


def latest_period(sales_df):
    """(latest az_year, latest week within that year)."""
    yr = int(sales_df['az_year'].dropna().max())
    wk = int(sales_df.loc[sales_df['az_year'] == yr, 'week'].dropna().max())
    return yr, wk


def weekly_budget(budget_df, sales_df):
    """Spread monthly budget evenly over the fiscal weeks of that month.

    Returns DataFrame [store, az_year, week, budget]. Weeks per month are taken
    from the sales file (current year, or last year if the month hasn't started).
    """
    if budget_df is None or budget_df.empty:
        return pd.DataFrame(columns=['store', 'az_year', 'week', 'budget'])
    cal = sales_df[['az_year', 'month', 'week']].dropna().drop_duplicates()
    cal_ly = cal.copy(); cal_ly['az_year'] += 1
    cal = pd.concat([cal, cal_ly]).drop_duplicates(['az_year', 'week'], keep='first')
    cal = cal.drop_duplicates(['az_year', 'month', 'week'])
    out = budget_df.merge(cal, on=['az_year', 'month'], how='inner')
    n = out.groupby(['store', 'az_year', 'month'])['week'].transform('nunique')
    out['budget'] = out['budget'] / n
    return out[['store', 'az_year', 'week', 'budget']]


def pct(v, dec=1):
    """Plain % formatter that tolerates NaN/inf."""
    try:
        return fmt_pct(float(v), dec)
    except (TypeError, ValueError):
        return "—"
