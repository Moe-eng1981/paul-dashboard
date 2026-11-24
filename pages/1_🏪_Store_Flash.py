"""
Store Manager Flash — one-glance weekly performance card for a single store
(or a whole country / format), with automatic alerts.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from paul_core import (
    setup_page, top_bar, section, callout, kpi, chart_layout, scope_filters,
    filter_frame, store_week, add_ly, weekly_budget, latest_period,
    safe_pct, fmt, pct, pclass,
)

t, is_dark, sales_df, budget_df = setup_page("Store Flash", "🏪")

# ── Sidebar ──
with st.sidebar:
    st.markdown("**Flash settings**")
    yr_latest, wk_latest = latest_period(sales_df)
    years = sorted(sales_df['az_year'].dropna().unique().astype(int).tolist(), reverse=True)
    sel_yr = st.selectbox("AZ Year", years, index=years.index(yr_latest), key="fl_yr")
    weeks = sorted(sales_df.loc[sales_df['az_year'] == sel_yr, 'week'].dropna().unique().astype(int).tolist())
    sel_wk = st.select_slider("Fiscal Week", weeks, value=weeks[-1], key="fl_wk")
    alert_th = st.slider("Alert threshold (% drop)", 5, 30, 10, key="fl_th",
                         help="Flag anything falling more than this vs last year")
scope = scope_filters(sales_df, "fl", show_store=True)

scoped = filter_frame(sales_df, scope['country'], scope['brand'], scope['store'])
if scoped.empty:
    st.warning("No data for this selection."); st.stop()

scope_lbl = scope['store'] if scope['store'] != "All" else (
    scope['country'] if scope['country'] != "All" else "All Stores")
top_bar(t, f"🏪 Store Flash · {scope_lbl}",
        f"AZ {sel_yr} · Week {sel_wk}",
        f"{scoped['store'].nunique()} store(s)")

# ── Numbers for the selected week ──
wk_ty = scoped[(scoped['az_year'] == sel_yr) & (scoped['week'] == sel_wk)]
wk_ly = scoped[(scoped['az_year'] == sel_yr - 1) & (scoped['week'] == sel_wk)
               & scoped['store'].isin(wk_ty['store'].unique())]
wk_pw = scoped[(scoped['az_year'] == sel_yr) & (scoped['week'] == sel_wk - 1)]

s_ty, s_ly, s_pw = wk_ty['sales'].sum(), wk_ly['sales'].sum(), wk_pw['sales'].sum()
t_ty, t_ly = wk_ty['tickets'].sum(), wk_ly['tickets'].sum()
b_ty = s_ty / t_ty if t_ty else 0
b_ly = s_ly / t_ly if t_ly else 0

wb = weekly_budget(budget_df, sales_df)
bgt = wb[(wb['az_year'] == sel_yr) & (wb['week'] == sel_wk)
         & wb['store'].isin(wk_ty['store'].unique())]['budget'].sum() if not wb.empty else 0

# Year-to-date
ytd_ty = scoped[(scoped['az_year'] == sel_yr) & (scoped['week'] <= sel_wk)]
ytd_ly = scoped[(scoped['az_year'] == sel_yr - 1) & (scoped['week'] <= sel_wk)]
ytd_bgt = wb[(wb['az_year'] == sel_yr) & (wb['week'] <= sel_wk)
             & wb['store'].isin(ytd_ty['store'].unique())]['budget'].sum() if not wb.empty else 0

vs_ly, vs_pw = safe_pct(s_ty, s_ly), safe_pct(s_ty, s_pw)
vs_bgt = safe_pct(s_ty, bgt) if bgt else np.nan
vs_t, vs_b = safe_pct(t_ty, t_ly), safe_pct(b_ty, b_ly)
ytd_vs_ly = safe_pct(ytd_ty['sales'].sum(), ytd_ly['sales'].sum())
ytd_vs_b = safe_pct(ytd_ty['sales'].sum(), ytd_bgt) if ytd_bgt else np.nan

cols = st.columns(6)
cards = [
    ("Week Sales", fmt(s_ty), f"{pct(vs_ly)} vs LY", pclass(vs_ly)),
    ("vs Budget", pct(vs_bgt), f"Budget {fmt(bgt)}" if bgt else "No budget loaded", pclass(vs_bgt)),
    ("vs Last Week", pct(vs_pw), f"W{sel_wk-1}: {fmt(s_pw)}", pclass(vs_pw)),
    ("Tickets", fmt(t_ty), f"{pct(vs_t)} vs LY", pclass(vs_t)),
    ("Avg Basket", fmt(b_ty, 1), f"{pct(vs_b)} vs LY", pclass(vs_b)),
    ("YTD Sales", fmt(ytd_ty['sales'].sum()),
     f"{pct(ytd_vs_ly)} vs LY" + (f" · {pct(ytd_vs_b)} vs Bgt" if ytd_bgt else ""), pclass(ytd_vs_ly)),
]
for c, (lbl, val, sub, cls) in zip(cols, cards):
    with c:
        st.markdown(kpi(lbl, val, sub, cls), unsafe_allow_html=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ── Alerts ──
left, right = st.columns([1, 1])
with left:
    section("🚨 Alerts & Highlights")
    alerts = []
    th = -abs(alert_th)

    # Store-level (only when looking at more than one store)
    sw = add_ly(store_week(scoped))
    cur = sw[(sw['az_year'] == sel_yr) & (sw['week'] == sel_wk)].copy()
    cur['vs_ly'] = [safe_pct(a, b) for a, b in zip(cur['sales'], cur['ly_sales'])]
    if scoped['store'].nunique() > 1:
        for _, r in cur.sort_values('vs_ly').iterrows():
            if pd.notna(r['vs_ly']) and r['vs_ly'] <= th:
                alerts.append(("neg", f"<b>{r['store']}</b> sales {pct(r['vs_ly'])} vs LY "
                                      f"({fmt(r['sales'])} vs {fmt(r['ly_sales'])})"))
        best = cur.dropna(subset=['vs_ly']).sort_values('vs_ly', ascending=False).head(1)
        for _, r in best.iterrows():
            if r['vs_ly'] > 0:
                alerts.append(("pos", f"⭐ Best performer: <b>{r['store']}</b> {pct(r['vs_ly'])} vs LY"))

    # Channel-level
    ch_ty = wk_ty.groupby('channel')['sales'].sum()
    ch_ly = wk_ly.groupby('channel')['sales'].sum()
    for ch, v in ch_ty.items():
        g = safe_pct(v, ch_ly.get(ch, 0))
        if pd.notna(g) and g <= th:
            alerts.append(("neg", f"<b>{ch}</b> channel {pct(g)} vs LY"))
        elif pd.notna(g) and g >= abs(th):
            alerts.append(("pos", f"<b>{ch}</b> channel {pct(g)} vs LY"))

    # Ticket vs basket diagnosis
    if pd.notna(vs_t) and pd.notna(vs_b):
        if vs_t <= th and vs_b >= 0:
            alerts.append(("neg", f"Footfall issue: tickets {pct(vs_t)} while basket is holding ({pct(vs_b)})"))
        elif vs_b <= th and vs_t >= 0:
            alerts.append(("neg", f"Basket issue: avg basket {pct(vs_b)} while tickets are fine ({pct(vs_t)})"))

    if pd.notna(vs_bgt):
        alerts.append(("pos" if vs_bgt >= 0 else "neg",
                       f"Week is {pct(vs_bgt)} vs budget ({fmt(s_ty - bgt)} {'ahead' if vs_bgt >= 0 else 'behind'})"))

    # Streak: consecutive weeks below LY
    trend = sw[sw['az_year'] == sel_yr].groupby('week')[['sales', 'ly_sales']].sum().sort_index()
    trend = trend[trend.index <= sel_wk]
    streak = 0
    for _, r in trend[::-1].iterrows():
        if r['ly_sales'] > 0 and r['sales'] < r['ly_sales']:
            streak += 1
        else:
            break
    if streak >= 3:
        alerts.append(("neg", f"📉 {streak} weeks in a row below last year"))

    if not alerts:
        callout(t, "✅ Nothing unusual this week — all within threshold.", "pos")
    for kind, msg in alerts[:10]:
        callout(t, msg, kind)

with right:
    section("🍩 Channel Mix · This Week vs LY")
    mix = pd.DataFrame({'TY': ch_ty, 'LY': ch_ly}).fillna(0)
    fig = go.Figure()
    fig.add_bar(y=mix.index, x=mix['LY'], name='LY', orientation='h', marker_color=t['text_dim'])
    fig.add_bar(y=mix.index, x=mix['TY'], name='TY', orientation='h', marker_color=t['accent'])
    lay = chart_layout(t, 260); lay['barmode'] = 'group'
    fig.update_layout(**lay)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ── 12-week trend ──
section("📈 Last 12 Weeks")
last = trend.tail(12)
if not last.empty:
    wb_scope = wb[wb['store'].isin(scoped['store'].unique()) & (wb['az_year'] == sel_yr)]
    b_tr = wb_scope.groupby('week')['budget'].sum()
    fig = go.Figure()
    fig.add_bar(x=[f"W{int(w)}" for w in last.index], y=last['sales'], name='This Year',
                marker_color=t['accent'])
    fig.add_scatter(x=[f"W{int(w)}" for w in last.index], y=last['ly_sales'], name='Last Year',
                    mode='lines+markers', line=dict(color=t['text_dim'], dash='dot'))
    if not b_tr.empty:
        fig.add_scatter(x=[f"W{int(w)}" for w in last.index], y=b_tr.reindex(last.index).values,
                        name='Budget', mode='lines', line=dict(color=t['blue'], width=2))
    fig.update_layout(**chart_layout(t, 300))
    st.plotly_chart(fig, use_container_width=True)

st.caption("Tip: open this page on your phone — the cards stack vertically. "
           "Pick a store in the sidebar to give each manager their own flash.")
