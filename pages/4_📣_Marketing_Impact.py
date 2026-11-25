"""
Marketing Impact Tracker — did the campaign actually move sales?

For each campaign it compares the targeted stores with:
  • their own 4 weeks before the campaign (baseline uplift)
  • the same weeks last year (growth during vs before → removes seasonality)
  • the stores that were NOT targeted (control group) → removes market-wide effects
Optionally overlays weekly social metrics exported from Metricool.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io

from paul_core import (
    setup_page, top_bar, section, callout, kpi, chart_layout, find_col,
    store_week, add_ly, safe_pct, fmt, pct, pclass, style_df,
)

t, is_dark, sales_df, budget_df = setup_page("Marketing Impact", "📣")
ss = st.session_state

TEMPLATE = pd.DataFrame([
    ["Summer Iced Drinks", "Instagram", "Qatar", "All", 2025, 30, 33],
    ["Ramadan Boxes", "Instagram + TikTok", "UAE", "PAUL Dubai Mall", 2025, 8, 11],
], columns=['Campaign', 'Channel', 'Country', 'Store', 'AZ Year', 'Start Week', 'End Week'])


def to_fiscal(dates):
    """Approximate AZ fiscal year/week from calendar dates (AZ year starts 1 Feb)."""
    d = pd.to_datetime(dates, errors='coerce', dayfirst=True)
    az = np.where(d.dt.month >= 2, d.dt.year, d.dt.year - 1)
    start = pd.to_datetime(pd.Series(az).astype('Int64').astype(str) + "-02-01", errors='coerce')
    wk = ((d.reset_index(drop=True) - start).dt.days // 7 + 1).clip(1, 53)
    return pd.Series(az, dtype='float'), wk.astype('float')


def read_any(file):
    data = file.getvalue()
    return pd.read_excel(io.BytesIO(data)) if file.name.endswith(('xlsx', 'xls')) else pd.read_csv(io.BytesIO(data))


with st.sidebar:
    st.markdown("**📣 Campaigns file**")
    cf = st.file_uploader("Campaign list (.csv/.xlsx)", type=['csv', 'xlsx', 'xls'], key='mk_cf',
                          label_visibility="collapsed")
    st.download_button("⬇ Campaign template", TEMPLATE.to_csv(index=False).encode(),
                       "campaign_template.csv", "text/csv", use_container_width=True)
    st.markdown("**📱 Metricool export** *(optional)*")
    mf = st.file_uploader("Social metrics by date or week", type=['csv', 'xlsx', 'xls'], key='mk_mf',
                          label_visibility="collapsed")
    baseline_wks = st.slider("Baseline weeks before campaign", 2, 8, 4, key="mk_base")

top_bar(t, "📣 Marketing Impact Tracker", "Campaign uplift vs baseline, last year and non-targeted stores",
        "Upload campaigns in the sidebar or type them below")

# ── Campaign list (file or editable table) ──
if cf is not None:
    raw = read_any(cf)
    camp = pd.DataFrame({
        'Campaign': raw[find_col(raw, 'campaign', 'name') or raw.columns[0]].astype(str),
        'Channel': raw[find_col(raw, 'channel', 'network', 'platform')].astype(str) if find_col(raw, 'channel', 'network', 'platform') else '',
        'Country': raw[find_col(raw, 'country')].astype(str) if find_col(raw, 'country') else 'All',
        'Store': raw[find_col(raw, 'store')].astype(str) if find_col(raw, 'store') else 'All',
    })
    c_sw, c_ew, c_yr = find_col(raw, 'startweek'), find_col(raw, 'endweek'), find_col(raw, 'azyear', 'year')
    c_sd, c_ed = find_col(raw, 'startdate', 'start'), find_col(raw, 'enddate', 'end')
    if c_sw and c_ew and c_yr:
        camp['AZ Year'] = pd.to_numeric(raw[c_yr], errors='coerce')
        camp['Start Week'] = pd.to_numeric(raw[c_sw], errors='coerce')
        camp['End Week'] = pd.to_numeric(raw[c_ew], errors='coerce')
    elif c_sd and c_ed:
        _az, _sw = to_fiscal(raw[c_sd])
        _, _ew = to_fiscal(raw[c_ed])
        camp['AZ Year'], camp['Start Week'], camp['End Week'] = _az.values, _sw.values, _ew.values
        st.info("Dates converted to fiscal weeks assuming the AZ year starts on 1 February.")
    else:
        st.error("Campaign file needs either AZ Year + Start Week + End Week, or Start Date + End Date.")
        st.stop()
    ss['mk_campaigns'] = camp
elif 'mk_campaigns' not in ss:
    ss['mk_campaigns'] = TEMPLATE.copy()

section("📝 Campaigns")
st.caption("Edit, add or delete rows. Use **All** for every store in a country, or a country of **All** for group-wide.")
camp = st.data_editor(ss['mk_campaigns'], num_rows="dynamic", use_container_width=True, key="mk_editor",
                      column_config={
                          'Country': st.column_config.SelectboxColumn(options=['All'] + sorted(sales_df['country'].unique())),
                          'Store': st.column_config.SelectboxColumn(options=['All'] + sorted(sales_df['store'].unique())),
                          'AZ Year': st.column_config.NumberColumn(format="%d"),
                          'Start Week': st.column_config.NumberColumn(min_value=1, max_value=53, format="%d"),
                          'End Week': st.column_config.NumberColumn(min_value=1, max_value=53, format="%d"),
                      })
camp = camp.dropna(subset=['AZ Year', 'Start Week', 'End Week'])
if camp.empty:
    st.info("Add at least one campaign to see its impact."); st.stop()

# ── Impact calculation ──
sw = add_ly(store_week(sales_df))


def target_stores(row):
    m = pd.Series(True, index=sw.index)
    if str(row['Country']) not in ('All', '', 'nan'): m &= sw['country'] == row['Country']
    if str(row['Store']) not in ('All', '', 'nan'): m &= sw['store'] == row['Store']
    return set(sw.loc[m, 'store'])


def growth(d):
    return safe_pct(d['sales'].sum(), d['ly_sales'].sum())


results = []
for _, r in camp.iterrows():
    yr, s, e = int(r['AZ Year']), int(r['Start Week']), int(r['End Week'])
    tgt = target_stores(r)
    if not tgt:
        continue
    yr_df = sw[sw['az_year'] == yr]
    in_t = yr_df['store'].isin(tgt)
    during = yr_df[in_t & yr_df['week'].between(s, e)]
    before = yr_df[in_t & yr_df['week'].between(s - baseline_wks, s - 1)]
    ctrl_d = yr_df[~in_t & yr_df['week'].between(s, e)]
    ctrl_b = yr_df[~in_t & yr_df['week'].between(s - baseline_wks, s - 1)]
    n_d, n_b = max(during['week'].nunique(), 1), max(before['week'].nunique(), 1)

    avg_d, avg_b = during['sales'].sum() / n_d, before['sales'].sum() / n_b
    uplift = safe_pct(avg_d, avg_b)
    g_d, g_b = growth(during), growth(before)
    yoy_lift = g_d - g_b if pd.notna(g_d) and pd.notna(g_b) else np.nan
    c_up = safe_pct(ctrl_d['sales'].sum() / max(ctrl_d['week'].nunique(), 1),
                    ctrl_b['sales'].sum() / max(ctrl_b['week'].nunique(), 1)) if not ctrl_d.empty else np.nan
    vs_ctrl = uplift - c_up if pd.notna(uplift) and pd.notna(c_up) else np.nan
    incr = (avg_d - avg_b * (1 + (c_up if pd.notna(c_up) else 0) / 100)) * n_d
    tk_d, tk_b = during['tickets'].sum() / n_d, before['tickets'].sum() / n_b

    # verdict uses the most robust measure available
    best = vs_ctrl if pd.notna(vs_ctrl) else (yoy_lift if pd.notna(yoy_lift) else uplift)
    verdict = ("✅ Worked" if pd.notna(best) and best >= 3 else
               "➖ No clear effect" if pd.notna(best) and best > -3 else
               "❌ Underperformed" if pd.notna(best) else "—")
    results.append(dict(Campaign=r['Campaign'], Channel=r.get('Channel', ''), Stores=len(tgt),
                        Weeks=f"AZ{yr} W{s}–W{e}", _yr=yr, _s=s, _e=e, _tgt=tgt,
                        **{'Avg wk sales': avg_d, 'Uplift vs baseline %': uplift,
                           'YoY growth during %': g_d, 'YoY lift %': yoy_lift,
                           'Control uplift %': c_up, 'Net of control %': vs_ctrl,
                           'Tickets uplift %': safe_pct(tk_d, tk_b),
                           'Incremental sales': incr, 'Verdict': verdict}))

if not results:
    st.warning("None of the campaigns match stores in your sales file."); st.stop()
res = pd.DataFrame(results)

# ── Headline cards ──
worked = (res['Verdict'] == "✅ Worked").sum()
cols = st.columns(4)
cards = [("Campaigns analysed", str(len(res)), f"{worked} clearly worked", "kpi-neu"),
         ("Avg uplift vs baseline", pct(res['Uplift vs baseline %'].mean()), "sales per week", pclass(res['Uplift vs baseline %'].mean())),
         ("Avg net of control", pct(res['Net of control %'].mean()), "after market-wide trend", pclass(res['Net of control %'].mean())),
         ("Incremental sales", fmt(res['Incremental sales'].sum()), "est. total, all campaigns", pclass(res['Incremental sales'].sum()))]
for c, (a, b, s, k) in zip(cols, cards):
    with c: st.markdown(kpi(a, b, s, k), unsafe_allow_html=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)
section("📊 Campaign Scorecard")
disp = res.drop(columns=['_yr', '_s', '_e', '_tgt']).copy()
pcols = [c for c in disp.columns if c.endswith('%')]
for c in pcols: disp[c] = disp[c].apply(pct)
for c in ['Avg wk sales', 'Incremental sales']: disp[c] = disp[c].apply(fmt)
st.dataframe(style_df(disp, pcols + ['Incremental sales'], t), use_container_width=True, hide_index=True)

with st.expander("ℹ️ How to read this"):
    st.markdown(f"""
- **Uplift vs baseline** – average weekly sales during the campaign vs the {baseline_wks} weeks before.
- **YoY lift** – growth vs LY *during* the campaign minus growth vs LY *before* it. This removes seasonality (e.g. summer, Ramadan).
- **Net of control** – targeted stores' uplift minus the uplift of stores that weren't in the campaign. This removes market-wide effects. It's the most reliable figure.
- **Verdict** uses net of control when available (≥ +3 pts = worked).
""")

# ── Drill-down chart ──
section("🔍 Campaign Drill-down")
pick = st.selectbox("Campaign", res['Campaign'].tolist(), key="mk_pick")
row = res[res['Campaign'] == pick].iloc[0]
yr, s, e, tgt = row['_yr'], row['_s'], row['_e'], row['_tgt']
win = sw[(sw['az_year'] == yr) & sw['week'].between(max(1, s - 8), e + 6)]
tg = win[win['store'].isin(tgt)].groupby('week')[['sales', 'ly_sales']].sum()
ct = win[~win['store'].isin(tgt)].groupby('week')['sales'].sum()

fig = go.Figure()
fig.add_vrect(x0=s - 0.5, x1=e + 0.5, fillcolor=t['accent'], opacity=0.12, line_width=0,
              annotation_text=pick, annotation_position="top left")
fig.add_bar(x=tg.index, y=tg['sales'], name='Targeted stores TY', marker_color=t['accent'])
fig.add_scatter(x=tg.index, y=tg['ly_sales'], name='Targeted stores LY', mode='lines',
                line=dict(color=t['text_dim'], dash='dot'))
if not ct.empty:
    idx = ct / ct.loc[ct.index < s].mean() * tg['sales'].loc[tg.index < s].mean() if (ct.index < s).any() else ct
    fig.add_scatter(x=idx.index, y=idx.values, name='Control stores (indexed)', mode='lines',
                    line=dict(color=t['blue'], width=2))

# Metricool overlay
social = None
if mf is not None:
    m = read_any(mf)
    c_yr, c_wk, c_dt = find_col(m, 'azyear', 'year'), find_col(m, 'week'), find_col(m, 'date', 'day', 'publicationdate')
    if c_wk and c_yr:
        m['az_year'], m['week'] = pd.to_numeric(m[c_yr], errors='coerce'), pd.to_numeric(m[c_wk], errors='coerce')
    elif c_dt:
        _az, _wk = to_fiscal(m[c_dt])
        m['az_year'], m['week'] = _az.values, _wk.values
    num = [c for c in m.columns if c not in ('az_year', 'week') and pd.api.types.is_numeric_dtype(m[c])
           and c not in (c_yr, c_wk)]
    if 'week' in m and num:
        metric = st.selectbox("Social metric to overlay", num, key="mk_metric")
        social = m.groupby(['az_year', 'week'])[metric].sum().reset_index()
        so = social[(social['az_year'] == yr) & social['week'].between(max(1, s - 8), e + 6)]
        fig.add_scatter(x=so['week'], y=so[metric], name=metric, yaxis='y2', mode='lines+markers',
                        line=dict(color=t['green'], width=2))
lay = chart_layout(t, 360)
lay['xaxis']['title'] = f'Fiscal week · AZ {yr}'
lay['yaxis2'] = dict(overlaying='y', side='right', showgrid=False, tickfont=dict(color=t['green'], size=10))
fig.update_layout(**lay)
st.plotly_chart(fig, use_container_width=True)

v = row['Net of control %'] if pd.notna(row['Net of control %']) else row['YoY lift %']
callout(t, f"<b>{pick}</b>: {row['Verdict']} — sales per week {pct(row['Uplift vs baseline %'])} vs baseline, "
           f"{pct(v)} after adjusting for {'other stores' if pd.notna(row['Net of control %']) else 'seasonality'}. "
           f"Estimated incremental sales: <b>{fmt(row['Incremental sales'])}</b>.",
        "pos" if row['Verdict'].startswith("✅") else ("neg" if row['Verdict'].startswith("❌") else "neu"))

# Correlation (whole history) when social data present
if social is not None:
    group = sw.groupby(['az_year', 'week'])['sales'].sum().reset_index()
    j = group.merge(social, on=['az_year', 'week'])
    if len(j) >= 6:
        corr = j['sales'].corr(j[metric])
        callout(t, f"Across {len(j)} weeks, <b>{metric}</b> and group sales have a correlation of "
                   f"<b>{corr:.2f}</b> ({'strong' if abs(corr) > .6 else 'moderate' if abs(corr) > .3 else 'weak'} relationship).",
                "info")
