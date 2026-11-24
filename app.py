import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from paul_core import (
    FM_ORDER, setup_page, kpi, chart_layout, style_df,
    get_ly, get_lfl, get_bgt, safe_pct, fmt, fmt_pct, pclass,
)

# ─────────────────────────────────────────
# PAGE SETUP · theme + shared data uploads (see paul_core.py)
# ─────────────────────────────────────────
t, _is_dark, sales_df, budget_df = setup_page("Sales Intelligence")
theme_choice = "Dark" if _is_dark else "Light"

# ─────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────
with st.sidebar:
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
