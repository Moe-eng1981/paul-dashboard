"""
Store Benchmarking — league table of every store with a fair composite score,
peer comparison within format/country, and a growth-vs-basket quadrant.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from paul_core import (
    FM_ORDER, setup_page, top_bar, section, callout, kpi, chart_layout,
    scope_filters, filter_frame, store_week, add_ly, latest_period,
    safe_pct, fmt, pct, style_df,
)

t, is_dark, sales_df, budget_df = setup_page("Benchmarking", "🏆")

with st.sidebar:
    st.markdown("**Benchmark settings**")
    yr_latest, wk_latest = latest_period(sales_df)
    years = sorted(sales_df['az_year'].dropna().unique().astype(int).tolist(), reverse=True)
    sel_yr = st.selectbox("AZ Year", years, index=years.index(yr_latest), key="bm_yr")
    weeks = sorted(sales_df.loc[sales_df['az_year'] == sel_yr, 'week'].dropna().unique().astype(int).tolist())
    wk_rng = st.select_slider("Fiscal weeks", weeks, value=(weeks[0], weeks[-1]), key="bm_wk")
    peer = st.radio("Rank stores against", ["All stores", "Same format", "Same country"], key="bm_peer")
    st.markdown("**Score weights**")
    w_growth = st.slider("LFL growth", 0, 5, 3, key="bm_w1")
    w_budget = st.slider("Budget achievement", 0, 5, 3, key="bm_w2")
    w_basket = st.slider("Basket growth", 0, 5, 2, key="bm_w3")
    w_tickets = st.slider("Ticket growth", 0, 5, 2, key="bm_w4")
scope = scope_filters(sales_df, "bm", show_store=False)

scoped = filter_frame(sales_df, scope['country'], scope['brand'])
sw = add_ly(store_week(scoped))
cur = sw[(sw['az_year'] == sel_yr) & sw['week'].between(*wk_rng)]
if cur.empty:
    st.warning("No data for this period."); st.stop()

# ── Store metrics ──
g = cur.groupby(['store', 'country', 'brand']).agg(
    sales=('sales', 'sum'), ly=('ly_sales', 'sum'), tickets=('tickets', 'sum'),
    ly_tickets=('ly_tickets', 'sum'), weeks=('week', 'nunique')).reset_index()
lfl_rows = cur[(cur['sales'] > 0) & (cur['ly_sales'] > 0)].groupby('store')[['sales', 'ly_sales']].sum()
g['lfl'] = g['store'].map(lambda s: safe_pct(*lfl_rows.loc[s]) if s in lfl_rows.index else np.nan)
g['vs_ly'] = [safe_pct(a, b) for a, b in zip(g['sales'], g['ly'])]
g['basket'] = g['sales'] / g['tickets'].replace(0, np.nan)
g['ly_basket'] = g['ly'] / g['ly_tickets'].replace(0, np.nan)
# ticket & basket growth on like-for-like weeks only, so new stores compare fairly
lfl_t = cur[(cur['sales'] > 0) & (cur['ly_sales'] > 0)].groupby('store')[
    ['sales', 'ly_sales', 'tickets', 'ly_tickets']].sum()
def _g(s, kind):
    if s not in lfl_t.index: return np.nan
    r = lfl_t.loc[s]
    if kind == 't': return safe_pct(r['tickets'], r['ly_tickets'])
    b_ty = r['sales'] / r['tickets'] if r['tickets'] else np.nan
    b_ly = r['ly_sales'] / r['ly_tickets'] if r['ly_tickets'] else np.nan
    return safe_pct(b_ty, b_ly)
g['tickets_g'] = g['store'].map(lambda s: _g(s, 't'))
g['basket_g'] = g['store'].map(lambda s: _g(s, 'b'))
g['sales_wk'] = g['sales'] / g['weeks']
g['share'] = g['sales'] / g['sales'].sum() * 100

# Budget: achievement and monthly hit-rate
months_in = cur['month'].dropna().unique().tolist()
if budget_df is not None and not budget_df.empty:
    b = budget_df[(budget_df['az_year'] == sel_yr) & budget_df['month'].isin(months_in)]
    m_act = cur.groupby(['store', 'month'])['sales'].sum().reset_index()
    mb = m_act.merge(b.groupby(['store', 'month'])['budget'].sum().reset_index(), on=['store', 'month'])
    # only count complete months inside the selected week range
    full_months = (sales_df[sales_df['az_year'] == sel_yr].groupby('month')['week']
                   .agg(['min', 'max']))
    full_months = full_months[(full_months['min'] >= wk_rng[0]) & (full_months['max'] <= wk_rng[1])].index
    mb_full = mb[mb['month'].isin(full_months)]
    hit = mb_full.assign(hit=mb_full['sales'] >= mb_full['budget']).groupby('store')['hit'].agg(['sum', 'count'])
    g['hit_rate'] = g['store'].map(lambda s: hit.loc[s, 'sum'] / hit.loc[s, 'count'] * 100 if s in hit.index and hit.loc[s, 'count'] else np.nan)
    bt = mb_full.groupby('store')[['sales', 'budget']].sum()
    g['vs_bgt'] = g['store'].map(lambda s: safe_pct(bt.loc[s, 'sales'], bt.loc[s, 'budget']) if s in bt.index else np.nan)
else:
    g['hit_rate'] = np.nan
    g['vs_bgt'] = np.nan
has_bgt = g['vs_bgt'].notna().any()

# ── Composite score (percentile rank within peer group, 0–100) ──
peer_col = {"All stores": None, "Same format": 'brand', "Same country": 'country'}[peer]
metrics = {'lfl': w_growth, 'vs_bgt': w_budget if has_bgt else 0, 'basket_g': w_basket, 'tickets_g': w_tickets}
def prank(s):
    return s.rank(pct=True) * 100
score_parts = []
for m, w in metrics.items():
    if w == 0 or g[m].isna().all():
        continue
    r = g.groupby(peer_col)[m].transform(prank) if peer_col else prank(g[m])
    score_parts.append(r.fillna(50) * w)
total_w = sum(w for m, w in metrics.items() if w and not g[m].isna().all())
g['score'] = (sum(score_parts) / total_w) if score_parts else 50
g['rank'] = (g.groupby(peer_col)['score'].rank(ascending=False, method='min') if peer_col
             else g['score'].rank(ascending=False, method='min')).astype(int)
g = g.sort_values(['score'], ascending=False)
medal = {1: "🥇", 2: "🥈", 3: "🥉"}

scope_lbl = " · ".join(v for v in [scope['country'], scope['brand']] if v != "All") or "PAUL Group"
top_bar(t, "🏆 Store Benchmarking", f"{scope_lbl} · AZ {sel_yr} · W{wk_rng[0]}–W{wk_rng[1]} · ranked vs {peer.lower()}",
        f"{len(g)} stores")

# ── Podium ──
top3 = g.head(3).reset_index(drop=True)
cols = st.columns(4)
for i, r in top3.iterrows():
    with cols[i]:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">{medal[i+1]} #{i+1} overall</div>
            <div style="font-size:17px;font-weight:700;color:{t['text']};line-height:1.2;margin-bottom:6px;
                 white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="{r['store']}">{r['store']}</div>
            <div class="kpi-sub kpi-pos">Score {r['score']:.0f} / 100 · LFL {pct(r['lfl'])}</div>
        </div>""", unsafe_allow_html=True)
with cols[3]:
    lfl_all = safe_pct(lfl_rows['sales'].sum(), lfl_rows['ly_sales'].sum()) if not lfl_rows.empty else np.nan
    st.markdown(kpi("Group LFL", pct(lfl_all), f"Median store LFL {pct(g['lfl'].median())}",
                    "kpi-pos" if pd.notna(lfl_all) and lfl_all >= 0 else "kpi-neg"), unsafe_allow_html=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ── League table ──
section("📋 League Table")
tbl = g.copy()
tbl['Rank'] = tbl['rank'].map(lambda r: f"{medal.get(r, '')} {r}".strip())
tbl = tbl[['Rank', 'store', 'country', 'brand', 'score', 'sales', 'share', 'sales_wk', 'lfl', 'vs_ly',
           'vs_bgt', 'hit_rate', 'tickets_g', 'basket', 'basket_g']]
tbl.columns = ['Rank', 'Store', 'Country', 'Format', 'Score', 'Sales', 'Share %', 'Sales / wk', 'LFL %',
               'vs LY %', 'vs Bgt %', 'Bgt hit-rate', 'LFL Tickets %', 'Avg Basket', 'LFL Basket %']
export = tbl.copy()
if not has_bgt:
    tbl = tbl.drop(columns=['vs Bgt %', 'Bgt hit-rate'])
tbl['Score'] = tbl['Score'].map(lambda x: f"{x:.0f}")
for c in ['Sales', 'Sales / wk']: tbl[c] = tbl[c].apply(fmt)
tbl['Share %'] = tbl['Share %'].map(lambda x: f"{x:.1f}%")
tbl['Avg Basket'] = tbl['Avg Basket'].apply(lambda x: fmt(x, 1))
if 'Bgt hit-rate' in tbl: tbl['Bgt hit-rate'] = tbl['Bgt hit-rate'].map(lambda x: f"{x:.0f}%" if pd.notna(x) else "—")
pcols = [c for c in ['LFL %', 'vs LY %', 'vs Bgt %', 'LFL Tickets %', 'LFL Basket %'] if c in tbl]
for c in pcols: tbl[c] = tbl[c].apply(pct)
st.dataframe(style_df(tbl.reset_index(drop=True), pcols, t), use_container_width=True, hide_index=True,
             height=min(38 + 35 * len(tbl), 600))
st.download_button("⬇ League table (CSV)", export.to_csv(index=False).encode(),
                   f"paul_league_AZ{sel_yr}_W{wk_rng[0]}-{wk_rng[1]}.csv", "text/csv")

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ── Quadrant + format comparison ──
c1, c2 = st.columns([3, 2])
with c1:
    section("🎯 Growth Quadrant · Tickets vs Basket")
    q = g.dropna(subset=['tickets_g', 'basket_g'])
    if q.empty:
        st.info("Needs last-year data to plot growth.")
    else:
        fig = go.Figure()
        palette = [t['accent'], t['blue'], t['green'], t['red'], "#A07840", "#8E6FBF"]
        for i, (grp, d) in enumerate(q.groupby('brand')):
            fig.add_scatter(x=d['tickets_g'], y=d['basket_g'], mode='markers+text', name=grp,
                            text=d['store'].str.replace('PAUL ', '').str[:18], textposition='top center',
                            textfont=dict(size=9, color=t['text_dim']),
                            marker=dict(size=np.clip(d['sales'] / d['sales'].max() * 40, 8, 40),
                                        color=palette[i % len(palette)], opacity=0.8,
                                        line=dict(width=1, color=t['bg'])),
                            customdata=np.stack([d['store'], d['sales']], axis=-1),
                            hovertemplate='<b>%{customdata[0]}</b><br>Tickets %{x:+.1f}%<br>Basket %{y:+.1f}%<br>Sales %{customdata[1]:,.0f}<extra></extra>')
        fig.add_hline(y=0, line=dict(color=t['border'])); fig.add_vline(x=0, line=dict(color=t['border']))
        for x, y, txt in [(1, 1, "⭐ More guests, bigger baskets"), (0, 1, "Bigger baskets, fewer guests"),
                          (0, 0, "⚠️ Losing on both"), (1, 0, "More guests, smaller baskets")]:
            fig.add_annotation(xref='paper', yref='paper', x=0.02 if x == 0 else 0.98, y=0.02 if y == 0 else 0.98,
                               text=txt, showarrow=False, xanchor='left' if x == 0 else 'right',
                               font=dict(size=10, color=t['text_dim']))
        lay = chart_layout(t, 420)
        lay['xaxis']['title'] = 'LFL tickets vs LY (%)'; lay['yaxis']['title'] = 'LFL avg basket vs LY (%)'
        fig.update_layout(**lay)
        st.plotly_chart(fig, use_container_width=True)

with c2:
    section("🏷️ Format & Country Averages")
    by = st.radio("Group by", ["Format", "Country"], horizontal=True, key="bm_by")
    col = 'brand' if by == "Format" else 'country'
    agg = g.groupby(col).agg(stores=('store', 'count'), sales=('sales', 'sum'), ly=('ly', 'sum'),
                             sales_wk=('sales_wk', 'mean'), score=('score', 'mean')).reset_index()
    agg['vs LY %'] = [pct(safe_pct(a, b)) for a, b in zip(agg['sales'], agg['ly'])]
    agg['Sales / store / wk'] = agg['sales_wk'].apply(fmt)
    agg['Avg score'] = agg['score'].map(lambda x: f"{x:.0f}")
    agg['Sales'] = agg['sales'].apply(fmt)
    out = agg[[col, 'stores', 'Sales', 'vs LY %', 'Sales / store / wk', 'Avg score']].rename(
        columns={col: by, 'stores': 'Stores'})
    st.dataframe(style_df(out, ['vs LY %'], t), use_container_width=True, hide_index=True)

    section("💬 Talking Points")
    best = g.iloc[0]
    callout(t, f"🥇 <b>{best['store']}</b> leads with LFL {pct(best['lfl'])} and basket {pct(best['basket_g'])}.", "pos")
    worst = g.iloc[-1]
    callout(t, f"Lowest score: <b>{worst['store']}</b> (LFL {pct(worst['lfl'])}, tickets {pct(worst['tickets_g'])}).", "neg")
    both_down = g[(g['tickets_g'] < 0) & (g['basket_g'] < 0)]['store'].tolist()
    if both_down:
        callout(t, f"Losing guests <i>and</i> basket: {', '.join(both_down[:6])}", "neg")
    if has_bgt:
        perfect = g[g['hit_rate'] == 100]['store'].tolist()
        if perfect:
            callout(t, f"Hit budget every full month: {', '.join(perfect[:6])}", "pos")

with st.expander("ℹ️ How the score works"):
    st.markdown("""
Each store gets a **percentile rank (0–100)** on each metric, compared with its peer group (all stores, same format or same country).
The score is the weighted average of those ranks, using the weights in the sidebar. This way, a small kiosk and a flagship
are compared on **growth and execution, not size**. Budget achievement and hit-rate only count fiscal months that are fully inside the selected weeks.
""")
