import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import io

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="PAUL Group · Sales Intelligence",
    page_icon="🥐",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    return dict(
        paper_bgcolor=t['chart_bg'],
        plot_bgcolor=t['chart_bg'],
        font=dict(family="Inter", color=t['text'], size=11),
        height=height,
        title=dict(text=title, font=dict(size=13, color=t['text']), x=0) if title else None,
        margin=dict(l=10, r=10, t=30 if title else 10, b=10),
        xaxis=dict(gridcolor=t['grid'], tickfont=dict(size=10, color=t['text_dim']),
                   linecolor=t['border'], showline=True),
        yaxis=dict(gridcolor=t['grid'], tickfont=dict(size=10, color=t['text_dim'])),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10, color=t['text_dim'])),
        hoverlabel=dict(bgcolor=t['bg2'], bordercolor=t['border'],
                        font=dict(color=t['text'], size=11)),
    )

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

# ─────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────
with st.sidebar:
    # Theme toggle
    theme_choice = st.radio("🎨 Theme", ["Dark", "Light"], horizontal=True)
    t = THEMES["dark"] if theme_choice == "Dark" else THEMES["light"]
    inject_css(t)

    st.markdown("---")

    # File uploads
    st.markdown("**📂 Sales Data**")
    sales_file = st.file_uploader("Upload .xlsx or .csv", type=['xlsx','xls','csv'], key='sf',
                                   label_visibility="collapsed")

    st.markdown("**🎯 Budget** *(optional)*")
    budget_file = st.file_uploader("Upload .xlsx or .csv", type=['xlsx','xls','csv'], key='bf',
                                    label_visibility="collapsed")

    if st.button("🔄 Clear Cache", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    sales_df = budget_df = None

    if sales_file:
        sales_df = load_sales(sales_file.read(), sales_file.name)
        if sales_df is not None:
            st.success(f"✅ {len(sales_df):,} rows · {sales_df['store'].nunique()} stores")

    if budget_file:
        budget_df = load_budget(budget_file.read(), budget_file.name)
        if budget_df is not None:
            st.success(f"✅ {len(budget_df):,} budget rows")

    if sales_df is None:
        st.info("↑ Upload your sales file to get started")
        st.stop()

    st.markdown("---")

    # ── FILTERS ──
    st.markdown("**Fiscal Year (AZ Year)**")
    fy_opts = sorted(sales_df['az_year'].dropna().unique().astype(int).tolist())
    sel_fy = st.selectbox("", ["All"] + [str(y) for y in fy_opts],
                           label_visibility="collapsed", key="fy")

    st.markdown("**View By**")
    view = st.radio("", ["Week", "Month", "Year"], horizontal=True,
                     label_visibility="collapsed")

    if view == "Week":
        pool = sales_df if sel_fy == "All" else sales_df[sales_df['az_year'] == int(sel_fy)]
        avail_wks = sorted(pool['week'].dropna().unique().astype(int).tolist())
        sel_week = st.select_slider("Fiscal Week", ["All"] + avail_wks, value="All")
    else:
        sel_week = "All"

    if view == "Month":
        pool = sales_df if sel_fy == "All" else sales_df[sales_df['az_year'] == int(sel_fy)]
        avail_mo = [m for m in FM_ORDER if m in pool['month'].values]
        sel_month = st.select_slider("Month", ["All"] + avail_mo, value="All")
    else:
        sel_month = "All"

    st.markdown("**Country**")
    countries = sorted(sales_df['country'].dropna().unique().tolist())
    sel_country = st.selectbox("", ["All"] + countries,
                                label_visibility="collapsed", key="country")

    st.markdown("**Brand**")
    brands = sorted(sales_df['brand'].dropna().unique().tolist())
    sel_brand = st.selectbox("", ["All"] + brands,
                              label_visibility="collapsed", key="brand")

    st.markdown("**Store**")
    sp = sales_df.copy()
    if sel_country != "All": sp = sp[sp['country'] == sel_country]
    if sel_brand   != "All": sp = sp[sp['brand']   == sel_brand]
    stores = sorted(sp['store'].dropna().unique().tolist())
    sel_store = st.selectbox("", ["All"] + stores,
                              label_visibility="collapsed", key="store")

    st.markdown("**Channel**")
    channels = sorted(sales_df['channel'].dropna().unique().tolist())
    sel_channel = st.selectbox("", ["All"] + channels,
                                label_visibility="collapsed", key="channel")

# ─────────────────────────────────────────
# APPLY FILTERS — strict exact match
# ─────────────────────────────────────────
df = sales_df.copy()
if sel_fy      != "All": df = df[df['az_year'] == int(sel_fy)]
if sel_country != "All": df = df[df['country'] == sel_country]
if sel_brand   != "All": df = df[df['brand']   == sel_brand]
if sel_store   != "All": df = df[df['store']   == sel_store]
if sel_channel != "All": df = df[df['channel'] == sel_channel]
if sel_week    != "All": df = df[df['week']    == int(sel_week)]
if sel_month   != "All": df = df[df['month']   == sel_month]

if df.empty:
    st.warning("⚠️ No data matches the selected filters.")
    st.stop()

ly_df = get_ly(sales_df, df)

# ─────────────────────────────────────────
# TOP BAR
# ─────────────────────────────────────────
fy_lbl   = f"AZ {sel_fy}" if sel_fy != "All" else "All Years"
ctx_lbl  = f"W{sel_week}" if sel_week != "All" else (sel_month if sel_month != "All" else view)
country_lbl = sel_country if sel_country != "All" else "All Countries"
txt_color = '#1A1000' if t['accent'] == '#C9A84C' else '#FFFFFF'

st.markdown(f"""
<div style="background:{t['accent']};border-radius:10px;padding:14px 20px;margin-bottom:16px;
     display:flex;align-items:center;justify-content:space-between">
  <div>
    <div style="font-size:20px;font-weight:700;color:{txt_color}">🥐 PAUL Group · Sales Intelligence</div>
    <div style="font-size:11px;color:{txt_color};opacity:0.65;margin-top:2px">
        {fy_lbl} · {ctx_lbl} · {country_lbl}
    </div>
  </div>
  <div style="text-align:right;font-size:11px;color:{txt_color};opacity:0.65">
    {len(df):,} rows · {df['store'].nunique()} stores · {df['country'].nunique()} countries
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# KPIs
# ─────────────────────────────────────────
ty_s  = df['sales'].sum()
ly_s  = ly_df['sales'].sum() if not ly_df.empty else 0
ty_t  = df['tickets'].sum()
ly_t  = ly_df['tickets'].sum() if not ly_df.empty else 0
ty_bk = ty_s / ty_t if ty_t else 0
ly_bk = ly_s / ly_t if ly_t else 0

lfl_ty, lfl_ly = get_lfl(sales_df, df)
months_sel = df['month'].dropna().unique().tolist()
stores_sel = df['store'].dropna().unique().tolist()
fy_val = int(sel_fy) if sel_fy != "All" else None
bgt = get_bgt(budget_df, stores_sel, months_sel, fy_val)

vs_ly  = safe_pct(ty_s,  ly_s)
lfl_p  = safe_pct(lfl_ty, lfl_ly)
bgt_p  = safe_pct(ty_s,  bgt) if bgt else np.nan
vs_t   = safe_pct(ty_t,  ly_t)
vs_bk  = safe_pct(ty_bk, ly_bk)

def arrow(v): return "▲" if pd.notna(v) and np.isfinite(v) and v >= 0 else "▼"

k1,k2,k3,k4,k5,k6 = st.columns(6)
kpi_data = [
    (k1, "Total Net Sales",  fmt(ty_s),        f"{arrow(vs_ly)} {fmt_pct(vs_ly)} vs LY",  pclass(vs_ly)),
    (k2, "LFL Growth",       fmt_pct(lfl_p),   "Like-for-Like · same fiscal week",         pclass(lfl_p)),
    (k3, "vs Budget",        fmt_pct(bgt_p),   f"Budget: {fmt(bgt)}" if bgt else "No budget", pclass(bgt_p)),
    (k4, "# Tickets",        fmt(ty_t),        f"{arrow(vs_t)} {fmt_pct(vs_t)} vs LY",    pclass(vs_t)),
    (k5, "Avg Basket",       fmt(ty_bk, 1),    f"{arrow(vs_bk)} {fmt_pct(vs_bk)} vs LY",  pclass(vs_bk)),
    (k6, "Active Stores",    str(df['store'].nunique()), f"of {sales_df['store'].nunique()} total", "kpi-neu"),
]
for col, label, value, sub, sc in kpi_data:
    with col:
        st.markdown(kpi(label, value, sub, sc), unsafe_allow_html=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ─────────────────────────────────────────
# TREND + CHANNEL
# ─────────────────────────────────────────
MO_IDX = {m:i for i,m in enumerate(FM_ORDER)}

def build_trend(df_ty, df_all, view):
    if view == "Week":
        ty = df_ty.groupby(['az_year','week'])['sales'].sum().reset_index()
        ty['lbl'] = 'AZ'+ty['az_year'].astype(str)+' W'+ty['week'].astype(str).str.zfill(2)
        ty = ty.sort_values(['az_year','week'])
        ly_yrs = ty['az_year'].dropna().unique() - 1
        ly = df_all[df_all['az_year'].isin(ly_yrs)].groupby(['az_year','week'])['sales'].sum().reset_index()
        ly['lbl'] = 'AZ'+(ly['az_year']+1).astype(str)+' W'+ly['week'].astype(str).str.zfill(2)
        ly = ly.sort_values(['az_year','week'])
        return ty['lbl'], ty['sales'], ly['lbl'], ly['sales']
    elif view == "Month":
        ty = df_ty.groupby(['az_year','month'])['sales'].sum().reset_index()
        ty['sort'] = ty['az_year'].astype(str)+ty['month'].map(lambda m: str(MO_IDX.get(m,99)).zfill(2))
        ty['lbl'] = ty['month']+' AZ'+ty['az_year'].astype(str)
        ty = ty.sort_values('sort')
        ly_yrs = ty['az_year'].dropna().unique() - 1
        ly = df_all[df_all['az_year'].isin(ly_yrs)].groupby(['az_year','month'])['sales'].sum().reset_index()
        ly['sort'] = ly['az_year'].astype(str)+ly['month'].map(lambda m: str(MO_IDX.get(m,99)).zfill(2))
        ly['lbl'] = ly['month']+' AZ'+(ly['az_year']+1).astype(str)
        ly = ly.sort_values('sort')
        return ty['lbl'], ty['sales'], ly['lbl'], ly['sales']
    else:
        ty = df_ty.groupby('az_year')['sales'].sum().reset_index().sort_values('az_year')
        ly_yrs = ty['az_year'].dropna().unique() - 1
        ly = df_all[df_all['az_year'].isin(ly_yrs)].groupby('az_year')['sales'].sum().reset_index()
        ly['lbl'] = (ly['az_year']+1).astype(str)
        ty['lbl'] = ty['az_year'].astype(str)
        return ty['lbl'], ty['sales'], ly['lbl'], ly['sales']

x_ty, y_ty, x_ly, y_ly = build_trend(df, sales_df, view)

col_trend, col_ch = st.columns([2,1])

with col_trend:
    st.markdown(f'<div class="section-hdr">📈 Sales Trend · {view}</div>', unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_ty, y=y_ty, name=f"AZ {sel_fy if sel_fy!='All' else 'TY'}",
        line=dict(color=t['accent'], width=3),
        fill='tozeroy', fillcolor=f"{'rgba(201,168,76,0.08)' if theme_choice=='Dark' else 'rgba(27,58,107,0.06)'}",
        mode='lines+markers', marker=dict(size=4, color=t['accent']),
        hovertemplate='%{x}<br><b>%{y:,.0f}</b><extra>TY</extra>'
    ))
    if len(y_ly) > 0 and y_ly.sum() > 0:
        fig.add_trace(go.Scatter(
            x=x_ly, y=y_ly, name="Last Year",
            line=dict(color=t['text_dim'], width=2, dash='dot'),
            mode='lines', hovertemplate='%{x}<br>%{y:,.0f}<extra>LY</extra>'
        ))
    fig.update_layout(**chart_layout(t, 300))
    st.plotly_chart(fig, use_container_width=True)

with col_ch:
    st.markdown(f'<div class="section-hdr">🍩 Channel Mix</div>', unsafe_allow_html=True)
    ch = df.groupby('channel')['sales'].sum().reset_index().sort_values('sales', ascending=False)
    colors_d = [t['accent'], t['blue'], t['green'], t['red'], "#A07840", "#8B6914"]
    colors_l = ["#1B3A6B","#2E6DA4","#4A9FD4","#1E8449","#F39C12","#C0392B"]
    clrs = colors_d if theme_choice == "Dark" else colors_l
    fig2 = go.Figure(go.Pie(
        labels=ch['channel'], values=ch['sales'], hole=0.55,
        marker=dict(colors=clrs[:len(ch)], line=dict(color=t['bg'], width=2)),
        textfont=dict(size=10, color=t['text']),
        hovertemplate='%{label}<br><b>%{value:,.0f}</b> (%{percent})<extra></extra>'
    ))
    layout2 = chart_layout(t, 300)
    layout2.pop('xaxis', None); layout2.pop('yaxis', None)
    layout2['legend'] = dict(orientation='v', font=dict(size=9, color=t['text_dim']),
                              x=1.0, y=0.5, bgcolor='rgba(0,0,0,0)')
    fig2.update_layout(**layout2)
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ─────────────────────────────────────────
# BREAKDOWN TABLES
# ─────────────────────────────────────────
def make_breakdown(df_ty, df_all, group_col):
    grp = df_ty.groupby(group_col).agg(sales=('sales','sum'), tickets=('tickets','sum')).reset_index()
    ly  = get_ly(df_all, df_ty)
    if not ly.empty:
        ly_grp = ly.groupby(group_col)['sales'].sum().rename('ly_sales')
        grp = grp.merge(ly_grp, on=group_col, how='left').fillna({'ly_sales':0})
    else:
        grp['ly_sales'] = 0
    grp['vs_ly'] = grp.apply(lambda r: safe_pct(r['sales'], r['ly_sales']), axis=1)
    grp['basket'] = grp.apply(lambda r: r['sales']/r['tickets'] if r['tickets'] else 0, axis=1)
    return grp.sort_values('sales', ascending=False).reset_index(drop=True)

c_store, c_country2, c_brand2 = st.columns(3)

with c_store:
    st.markdown('<div class="section-hdr">🏪 Top Stores</div>', unsafe_allow_html=True)
    t_df = make_breakdown(df, sales_df, 'store')
    disp = t_df[['store','sales','vs_ly','basket']].head(20).copy()
    disp.index += 1
    disp.columns = ['Store','Sales','vs LY %','Avg Basket']
    disp['Sales']      = disp['Sales'].apply(fmt)
    disp['vs LY %']    = disp['vs LY %'].apply(fmt_pct)
    disp['Avg Basket'] = disp['Avg Basket'].apply(lambda x: fmt(x,1))
    st.dataframe(style_df(disp, ['vs LY %'], t), use_container_width=True, height=340)

with c_country2:
    st.markdown('<div class="section-hdr">🌍 By Country</div>', unsafe_allow_html=True)
    t_df2 = make_breakdown(df, sales_df, 'country')
    disp2 = t_df2[['country','sales','vs_ly','tickets']].copy()
    disp2.index += 1
    disp2.columns = ['Country','Sales','vs LY %','Tickets']
    disp2['Sales']   = disp2['Sales'].apply(fmt)
    disp2['vs LY %'] = disp2['vs LY %'].apply(fmt_pct)
    disp2['Tickets'] = disp2['Tickets'].apply(fmt)
    st.dataframe(style_df(disp2, ['vs LY %'], t), use_container_width=True, height=340)

with c_brand2:
    st.markdown('<div class="section-hdr">🏷️ By Brand</div>', unsafe_allow_html=True)
    t_df3 = make_breakdown(df, sales_df, 'brand')
    # LFL per brand
    lfl_brand = {}
    for brand in t_df3['brand']:
        df_b = df[df['brand']==brand]
        lt, ll = get_lfl(sales_df, df_b)
        lfl_brand[brand] = safe_pct(lt, ll)
    t_df3['lfl'] = t_df3['brand'].map(lfl_brand)
    disp3 = t_df3[['brand','sales','vs_ly','lfl']].copy()
    disp3.index += 1
    disp3.columns = ['Brand','Sales','vs LY %','LFL %']
    disp3['Sales']   = disp3['Sales'].apply(fmt)
    disp3['vs LY %'] = disp3['vs LY %'].apply(fmt_pct)
    disp3['LFL %']   = disp3['LFL %'].apply(fmt_pct)
    st.dataframe(style_df(disp3, ['vs LY %','LFL %'], t), use_container_width=True, height=340)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ─────────────────────────────────────────
# DETAIL TABLE
# ─────────────────────────────────────────
st.markdown(f'<div class="section-hdr">📋 Detail by {view}</div>', unsafe_allow_html=True)

def build_detail(df_ty, df_all, bdf, view):
    rows = []
    if view == "Week":
        for (az,wk), grp in df_ty.groupby(['az_year','week']):
            ly_g = df_all[(df_all['az_year']==(az-1)) & (df_all['week']==wk) & (df_all['store'].isin(grp['store'].unique()))]
            lt,ll = get_lfl(df_all, grp)
            bv = get_bgt(bdf, grp['store'].unique().tolist(), grp['month'].unique().tolist(), int(az))
            ty_s2=grp['sales'].sum(); ly_s2=ly_g['sales'].sum()
            ty_t2=grp['tickets'].sum(); ly_t2=ly_g['tickets'].sum()
            rows.append({'Period':f'AZ{int(az)} · W{int(wk)}','Sales TY':ty_s2,'Sales LY':ly_s2,
                'vs LY %':safe_pct(ty_s2,ly_s2),'LFL %':safe_pct(lt,ll),
                'Budget':bv or np.nan,'vs Bgt %':safe_pct(ty_s2,bv) if bv else np.nan,
                'Tickets TY':int(ty_t2),'Tickets LY':int(ly_t2),
                'vs Tkts %':safe_pct(ty_t2,ly_t2),
                'Avg Basket':ty_s2/ty_t2 if ty_t2 else 0})
        rows.sort(key=lambda x: x['Period'])
    elif view == "Month":
        for (az,mo), grp in df_ty.groupby(['az_year','month']):
            ly_g = df_all[(df_all['az_year']==(az-1)) & (df_all['month']==mo) & (df_all['store'].isin(grp['store'].unique()))]
            lt,ll = get_lfl(df_all, grp)
            bv = get_bgt(bdf, grp['store'].unique().tolist(), [mo], int(az))
            ty_s2=grp['sales'].sum(); ly_s2=ly_g['sales'].sum()
            ty_t2=grp['tickets'].sum(); ly_t2=ly_g['tickets'].sum()
            rows.append({'Period':f'{mo} AZ{int(az)}','_sort':str(int(az))+str(MO_IDX.get(mo,99)).zfill(2),
                'Sales TY':ty_s2,'Sales LY':ly_s2,'vs LY %':safe_pct(ty_s2,ly_s2),'LFL %':safe_pct(lt,ll),
                'Budget':bv or np.nan,'vs Bgt %':safe_pct(ty_s2,bv) if bv else np.nan,
                'Tickets TY':int(ty_t2),'Tickets LY':int(ly_t2),
                'vs Tkts %':safe_pct(ty_t2,ly_t2),'Avg Basket':ty_s2/ty_t2 if ty_t2 else 0})
        rows.sort(key=lambda x: x.get('_sort',''))
        for r in rows: r.pop('_sort',None)
    else:
        for az, grp in df_ty.groupby('az_year'):
            ly_g = df_all[(df_all['az_year']==(az-1)) & (df_all['store'].isin(grp['store'].unique()))]
            lt,ll = get_lfl(df_all, grp)
            bv = get_bgt(bdf, grp['store'].unique().tolist(), grp['month'].unique().tolist(), int(az))
            ty_s2=grp['sales'].sum(); ly_s2=ly_g['sales'].sum()
            ty_t2=grp['tickets'].sum(); ly_t2=ly_g['tickets'].sum()
            rows.append({'Period':f'AZ{int(az)}','Sales TY':ty_s2,'Sales LY':ly_s2,
                'vs LY %':safe_pct(ty_s2,ly_s2),'LFL %':safe_pct(lt,ll),
                'Budget':bv or np.nan,'vs Bgt %':safe_pct(ty_s2,bv) if bv else np.nan,
                'Tickets TY':int(ty_t2),'Tickets LY':int(ly_t2),
                'vs Tkts %':safe_pct(ty_t2,ly_t2),'Avg Basket':ty_s2/ty_t2 if ty_t2 else 0})

    out = pd.DataFrame(rows)
    if out.empty: return out
    for c in ['Sales TY','Sales LY','Budget']:
        out[c] = out[c].apply(lambda x: fmt(x) if pd.notna(x) else '—')
    for c in ['vs LY %','LFL %','vs Bgt %','vs Tkts %']:
        out[c] = out[c].apply(lambda x: fmt_pct(x) if pd.notna(x) else '—')
    out['Tickets TY'] = out['Tickets TY'].apply(fmt)
    out['Tickets LY'] = out['Tickets LY'].apply(fmt)
    out['Avg Basket'] = out['Avg Basket'].apply(lambda x: fmt(x,1))
    return out

det = build_detail(df, sales_df, budget_df, view)
pct_cols = ['vs LY %','LFL %','vs Bgt %','vs Tkts %']
st.dataframe(style_df(det, pct_cols, t), use_container_width=True, height=400)

# ─────────────────────────────────────────
# EXPORT
# ─────────────────────────────────────────
st.markdown("<hr class='divider'>", unsafe_allow_html=True)
e1, e2, e3, _ = st.columns([1,1,1,3])
with e1:
    st.download_button("⬇ Detail CSV", det.to_csv(index=False).encode(),
                        f"paul_{view.lower()}.csv", "text/csv")
with e2:
    s_exp = make_breakdown(df, sales_df, 'store')[['store','sales','vs_ly','basket']]
    s_exp.columns = ['Store','Sales','vs LY %','Avg Basket']
    st.download_button("⬇ Store Rankings", s_exp.to_csv(index=False).encode(),
                        "paul_stores.csv", "text/csv")
with e3:
    st.download_button("⬇ Raw Filtered Data", df.to_csv(index=False).encode(),
                        "paul_raw.csv", "text/csv")
