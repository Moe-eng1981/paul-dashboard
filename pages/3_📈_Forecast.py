"""
Forecast & Budget Planner — projects the rest of the AZ year per store,
shows who will hit budget, the weekly run-rate needed, and drafts next year's budget.

Method (simple, explainable):
  forecast week = last-year sales for the same store & week × store's recent growth vs LY
  (recent growth = last N weeks TY ÷ same weeks LY). Stores with no LY history use their
  recent weekly average.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from paul_core import (
    FM_ORDER, MO_IDX, setup_page, top_bar, section, callout, kpi, chart_layout,
    scope_filters, filter_frame, store_week, latest_period, safe_pct, fmt, pct,
    pclass, style_df,
)

t, is_dark, sales_df, budget_df = setup_page("Forecast", "📈")

with st.sidebar:
    st.markdown("**Forecast settings**")
    yr_latest, _ = latest_period(sales_df)
    years = sorted(sales_df['az_year'].dropna().unique().astype(int).tolist(), reverse=True)
    sel_yr = st.selectbox("AZ Year to forecast", years, index=years.index(yr_latest), key="fc_yr")
    n_recent = st.slider("Growth based on last N weeks", 4, 16, 8, key="fc_n")
    adj = st.slider("Manual adjustment to remaining weeks (%)", -20, 20, 0, key="fc_adj",
                    help="Apply your own view on top of the trend, e.g. a new campaign (+) or a closure (-)")
scope = scope_filters(sales_df, "fc", show_store=True)

scoped = filter_frame(sales_df, scope['country'], scope['brand'], scope['store'])
sw = store_week(scoped)
ty = sw[sw['az_year'] == sel_yr]
ly = sw[sw['az_year'] == sel_yr - 1]
if ty.empty:
    st.warning("No data for the selected year."); st.stop()

last_wk = int(ty['week'].max())
n_weeks = int(max(52, ly['week'].max() if not ly.empty else 52, last_wk))

# ── Per-store forecast ──
calendar = (sales_df[sales_df['az_year'].isin([sel_yr, sel_yr - 1])][['week', 'month']]
            .dropna().drop_duplicates('week').set_index('week')['month'])
group_recent = ty[ty['week'] > last_wk - n_recent]
group_ly_same = ly[ly['week'].isin(group_recent['week'].unique()) & ly['store'].isin(group_recent['store'].unique())]
group_factor = (group_recent['sales'].sum() / group_ly_same['sales'].sum()) if group_ly_same['sales'].sum() else 1.0

rows = []
for store, g in ty.groupby('store'):
    g_ly = ly[ly['store'] == store].set_index('week')['sales']
    rec = g[g['week'] > last_wk - n_recent]
    ly_same = g_ly.reindex(rec['week']).dropna()
    rec_matched = rec[rec['week'].isin(ly_same.index)]['sales'].sum()
    if len(ly_same) >= max(2, n_recent // 2) and ly_same.sum() > 0:
        factor, method = rec_matched / ly_same.sum(), "LY × trend"
    else:
        factor, method = None, "Run-rate"
    run_rate = rec['sales'].mean() if len(rec) else 0
    meta = g.iloc[0]
    for w in range(last_wk + 1, n_weeks + 1):
        if factor is not None and w in g_ly.index:
            v = g_ly[w] * factor
        else:
            v = run_rate
        rows.append(dict(store=store, country=meta['country'], brand=meta['brand'], week=w,
                         month=calendar.get(w, ''), sales=v * (1 + adj / 100), kind='Forecast'))
    rows.append(dict(store=store, country=meta['country'], brand=meta['brand'], week=None, month=None,
                     sales=np.nan, kind='_meta', factor=factor, method=method))

fc_all = pd.DataFrame(rows)
meta = fc_all[fc_all['kind'] == '_meta'].set_index('store')[['factor', 'method']]
fc = fc_all[fc_all['kind'] == 'Forecast']

act = ty[['store', 'country', 'brand', 'week', 'month', 'sales']].assign(kind='Actual')
full = pd.concat([act, fc[act.columns]], ignore_index=True)

# Budget for the year
if budget_df is not None and not budget_df.empty:
    bud = budget_df[(budget_df['az_year'] == sel_yr) & budget_df['store'].isin(ty['store'].unique())]
else:
    bud = pd.DataFrame(columns=['store', 'month', 'budget'])

# ── Summary per store ──
summ = (full.groupby(['store', 'kind'])['sales'].sum().unstack(fill_value=0)
            .reindex(columns=['Actual', 'Forecast'], fill_value=0))
summ['Projected FY'] = summ['Actual'] + summ['Forecast']
summ['LY FY'] = ly.groupby('store')['sales'].sum().reindex(summ.index).fillna(0)
summ['Budget FY'] = bud.groupby('store')['budget'].sum().reindex(summ.index).fillna(0)
remaining = max(n_weeks - last_wk, 0)
summ['Proj vs Bgt %'] = [safe_pct(p, b) if b else np.nan for p, b in zip(summ['Projected FY'], summ['Budget FY'])]
summ['Proj vs LY %'] = [safe_pct(p, l) if l else np.nan for p, l in zip(summ['Projected FY'], summ['LY FY'])]
summ['Needed / wk'] = [(b - a) / remaining if remaining and b else np.nan
                       for a, b in zip(summ['Actual'], summ['Budget FY'])]
summ['Forecast / wk'] = summ['Forecast'] / remaining if remaining else np.nan
summ = summ.join(meta)

tot = summ[['Actual', 'Forecast', 'Projected FY', 'LY FY', 'Budget FY']].sum()
has_bgt = tot['Budget FY'] > 0
proj_vs_b = safe_pct(tot['Projected FY'], tot['Budget FY']) if has_bgt else np.nan
proj_vs_ly = safe_pct(tot['Projected FY'], tot['LY FY'])
need_wk = (tot['Budget FY'] - tot['Actual']) / remaining if has_bgt and remaining else np.nan
fc_wk = tot['Forecast'] / remaining if remaining else np.nan

scope_lbl = scope['store'] if scope['store'] != "All" else (scope['country'] if scope['country'] != "All" else "All Stores")
top_bar(t, f"📈 Forecast & Budget Planner · {scope_lbl}",
        f"AZ {sel_yr} · actuals to W{last_wk} · forecast W{last_wk+1}–W{n_weeks}",
        f"Trend factor (group): {pct((group_factor - 1) * 100)} vs LY")

cols = st.columns(5)
cards = [
    ("Actual YTD", fmt(tot['Actual']), f"W1–W{last_wk}", "kpi-neu"),
    ("Projected Full Year", fmt(tot['Projected FY']), f"{pct(proj_vs_ly)} vs LY", pclass(proj_vs_ly)),
    ("Budget Full Year", fmt(tot['Budget FY']) if has_bgt else "—",
     f"Projection {pct(proj_vs_b)} vs budget" if has_bgt else "Upload a budget file", pclass(proj_vs_b)),
    ("Needed per Week", fmt(need_wk) if pd.notna(need_wk) else "—",
     f"to land on budget ({remaining} wks left)" if has_bgt else "—", "kpi-neu"),
    ("Forecast per Week", fmt(fc_wk) if pd.notna(fc_wk) else "—",
     (f"{pct(safe_pct(fc_wk, need_wk))} vs needed" if pd.notna(need_wk) else "trend-based"),
     pclass(safe_pct(fc_wk, need_wk)) if pd.notna(need_wk) else "kpi-neu"),
]
for c, (a, b, s, k) in zip(cols, cards):
    with c: st.markdown(kpi(a, b, s, k), unsafe_allow_html=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ── Verdict ──
if has_bgt:
    on_track = summ[(summ['Budget FY'] > 0) & (summ['Proj vs Bgt %'] >= 0)]
    off_track = summ[(summ['Budget FY'] > 0) & (summ['Proj vs Bgt %'] < 0)].sort_values('Proj vs Bgt %')
    gap = tot['Projected FY'] - tot['Budget FY']
    callout(t, f"On current trend you will finish <b>{pct(proj_vs_b)}</b> vs budget "
               f"({fmt(abs(gap))} {'ahead' if gap >= 0 else 'short'}). "
               f"<b>{len(on_track)}</b> store(s) on track, <b>{len(off_track)}</b> at risk.",
            "pos" if gap >= 0 else "neg")
    if len(off_track):
        worst = ", ".join(f"{s} ({pct(v)})" for s, v in off_track['Proj vs Bgt %'].head(5).items())
        callout(t, f"Biggest gaps to budget: {worst}", "neg")

# ── Cumulative chart ──
section("📊 Cumulative Sales · Actual, Forecast, Budget, Last Year")
wk_act = act.groupby('week')['sales'].sum()
wk_fc = fc.groupby('week')['sales'].sum()
weeks_axis = list(range(1, n_weeks + 1))
cum_all = pd.concat([wk_act, wk_fc]).groupby(level=0).sum().reindex(weeks_axis, fill_value=0).cumsum()
cum_act = cum_all.loc[:last_wk]
cum_fc = cum_all.loc[last_wk:]
cum_ly = ly.groupby('week')['sales'].sum().reindex(weeks_axis, fill_value=0).cumsum()

fig = go.Figure()
fig.add_scatter(x=cum_act.index, y=cum_act.values, name='Actual', line=dict(color=t['accent'], width=3))
fig.add_scatter(x=cum_fc.index, y=cum_fc.values, name='Forecast', line=dict(color=t['accent'], width=3, dash='dash'))
if not ly.empty:
    fig.add_scatter(x=cum_ly.index, y=cum_ly.values, name='Last Year', line=dict(color=t['text_dim'], dash='dot'))
if has_bgt:
    # spread monthly budget across that month's weeks
    wk_month = pd.Series({w: calendar.get(w, '') for w in weeks_axis})
    per_m = wk_month.value_counts()
    b_m = bud.groupby('month')['budget'].sum()
    b_wk = wk_month.map(lambda m: b_m.get(m, 0) / per_m.get(m, 1))
    fig.add_scatter(x=weeks_axis, y=b_wk.cumsum().values, name='Budget', line=dict(color=t['blue'], width=2))
fig.add_vline(x=last_wk, line=dict(color=t['border'], dash='dot'))
lay = chart_layout(t, 340); lay['xaxis']['title'] = 'Fiscal week'
fig.update_layout(**lay)
st.plotly_chart(fig, use_container_width=True)

# ── Store table ──
section("🏪 Store Projections")
disp = summ.reset_index()[['store', 'Actual', 'Projected FY', 'LY FY', 'Budget FY',
                           'Proj vs LY %', 'Proj vs Bgt %', 'Needed / wk', 'Forecast / wk', 'method']]
disp = (disp.sort_values('Proj vs Bgt %', ascending=True) if has_bgt
        else disp.sort_values('Projected FY', ascending=False))
disp.columns = ['Store', 'Actual YTD', 'Projected FY', 'LY FY', 'Budget FY',
                'Proj vs LY %', 'Proj vs Bgt %', 'Needed / wk', 'Forecast / wk', 'Method']
raw_export = disp.copy()
for c in ['Actual YTD', 'Projected FY', 'LY FY', 'Budget FY', 'Needed / wk', 'Forecast / wk']:
    disp[c] = disp[c].apply(lambda x: fmt(x) if pd.notna(x) and x != 0 else '—')
for c in ['Proj vs LY %', 'Proj vs Bgt %']:
    disp[c] = disp[c].apply(pct)
st.dataframe(style_df(disp.reset_index(drop=True), ['Proj vs LY %', 'Proj vs Bgt %'], t),
             use_container_width=True, hide_index=True, height=min(38 + 35 * len(disp), 500))
st.download_button("⬇ Store projections (CSV)", raw_export.to_csv(index=False).encode(),
                   f"paul_forecast_AZ{sel_yr}.csv", "text/csv")

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ── Next year budget draft ──
section(f"🎯 Draft Budget for AZ {sel_yr + 1}")
c1, c2 = st.columns([1, 3])
with c1:
    growth = st.number_input("Growth on projected AZ year (%)", -20.0, 50.0, 5.0, 0.5, key="fc_growth")
    st.caption("Starts from this year's projected sales by store and month, then applies your growth. "
               "Edit any cell before downloading.")
with c2:
    monthly = full.groupby(['store', 'month'])['sales'].sum().reset_index()
    monthly = monthly[monthly['month'].isin(FM_ORDER)]
    monthly['Budget'] = (monthly['sales'] * (1 + growth / 100)).round(0)
    piv = monthly.pivot(index='store', columns='month', values='Budget').reindex(columns=[m for m in FM_ORDER if m in monthly['month'].unique()])
    piv['Total'] = piv.sum(axis=1)
    edited = st.data_editor(piv.round(0), use_container_width=True, height=300, key="fc_editor")
    store_country = ty.groupby('store')['country'].first()
    out = (edited.drop(columns='Total').reset_index().melt(id_vars='store', var_name='Month', value_name='Budget'))
    out.insert(0, 'Country', out['store'].map(store_country))
    out = out.rename(columns={'store': 'Store'})
    out.insert(2, 'AZ Year', sel_yr + 1)
    out['_m'] = out['Month'].map(MO_IDX); out = out.sort_values(['Store', '_m']).drop(columns='_m')
    st.download_button(f"⬇ Download AZ {sel_yr + 1} budget (ready to upload)", out.to_csv(index=False).encode(),
                       f"paul_budget_AZ{sel_yr + 1}.csv", "text/csv")

with st.expander("ℹ️ How the forecast works"):
    st.markdown(f"""
- For each store, I compare its **last {n_recent} weeks** with the **same weeks last year** to get a growth factor.
- Each remaining week = **last year's sales for that week × the growth factor** (this keeps your seasonality: Ramadan, summer, Christmas).
- Stores without last-year history (new openings) use their **recent weekly average**.
- Your **manual adjustment** ({adj:+d}%) is applied to all remaining weeks.
- Months in the budget draft follow your fiscal calendar (Feb → Jan).
""")
