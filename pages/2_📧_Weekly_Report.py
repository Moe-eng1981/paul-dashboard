"""
Weekly Sales Report — writes the management email for you:
headline numbers, wins, misses and stores to watch, ready to copy, download or send.
"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
from urllib.parse import quote

from paul_core import (
    setup_page, top_bar, section, scope_filters, filter_frame,
    store_week, add_ly, weekly_budget, latest_period, safe_pct, fmt, pct,
)

t, is_dark, sales_df, budget_df = setup_page("Weekly Report", "📧")

with st.sidebar:
    st.markdown("**Report settings**")
    yr_latest, wk_latest = latest_period(sales_df)
    years = sorted(sales_df['az_year'].dropna().unique().astype(int).tolist(), reverse=True)
    sel_yr = st.selectbox("AZ Year", years, index=years.index(yr_latest), key="wr_yr")
    weeks = sorted(sales_df.loc[sales_df['az_year'] == sel_yr, 'week'].dropna().unique().astype(int).tolist())
    sel_wk = st.select_slider("Fiscal Week", weeks, value=weeks[-1], key="wr_wk")
    n_top = st.slider("Stores in top / bottom lists", 3, 10, 5, key="wr_n")
    currency = st.text_input("Currency label", "QAR", key="wr_cur")
    sender = st.text_input("Sign off as", "", key="wr_sender", placeholder="Your name")
scope = scope_filters(sales_df, "wr", show_store=False)

scoped = filter_frame(sales_df, scope['country'], scope['brand'])
scope_lbl = " · ".join(v for v in [scope['country'], scope['brand']] if v != "All") or "PAUL Group"

top_bar(t, "📧 Weekly Sales Report", f"{scope_lbl} · AZ {sel_yr} · Week {sel_wk}",
        "Auto-written from your sales file")

# ── Calculations ──
sw = add_ly(store_week(scoped))
wb = weekly_budget(budget_df, sales_df)
if not wb.empty:
    sw = sw.merge(wb, on=['store', 'az_year', 'week'], how='left')
else:
    sw['budget'] = np.nan

wk = sw[(sw['az_year'] == sel_yr) & (sw['week'] == sel_wk)].copy()
if wk.empty:
    st.warning("No sales for this week in the selected scope."); st.stop()
ytd = sw[(sw['az_year'] == sel_yr) & (sw['week'] <= sel_wk)]
prev = sw[(sw['az_year'] == sel_yr) & (sw['week'] == sel_wk - 1)]

def totals(d):
    s, ly, tk, lyt = d['sales'].sum(), d['ly_sales'].sum(), d['tickets'].sum(), d['ly_tickets'].sum()
    b = d['budget'].sum(min_count=1)
    lfl = d[(d['sales'] > 0) & (d['ly_sales'] > 0)]
    return dict(sales=s, ly=ly, vs_ly=safe_pct(s, ly),
                lfl=safe_pct(lfl['sales'].sum(), lfl['ly_sales'].sum()),
                budget=b, vs_bgt=safe_pct(s, b) if pd.notna(b) and b else np.nan,
                tickets=tk, vs_t=safe_pct(tk, lyt),
                basket=s / tk if tk else 0,
                vs_basket=safe_pct(s / tk if tk else 0, ly / lyt if lyt else 0))

W, Y = totals(wk), totals(ytd)
wow = safe_pct(W['sales'], prev['sales'].sum())

wk['vs_ly'] = [safe_pct(a, b) for a, b in zip(wk['sales'], wk['ly_sales'])]
wk['vs_bgt'] = [safe_pct(a, b) if pd.notna(b) and b else np.nan for a, b in zip(wk['sales'], wk['budget'])]
ranked = wk.dropna(subset=['vs_ly']).sort_values('vs_ly', ascending=False)
winners = ranked[ranked['vs_ly'] > 0].head(n_top)
losers = ranked[ranked['vs_ly'] < 0].sort_values('vs_ly').head(n_top)
new_stores = wk[wk['ly_sales'] == 0]['store'].tolist()

countries = (wk.groupby('country')[['sales', 'ly_sales']].sum()
               .assign(vs=lambda d: [safe_pct(a, b) for a, b in zip(d['sales'], d['ly_sales'])])
               .sort_values('sales', ascending=False))

ch_ty = scoped[(scoped['az_year'] == sel_yr) & (scoped['week'] == sel_wk)].groupby('channel')['sales'].sum()
ch_ly = scoped[(scoped['az_year'] == sel_yr - 1) & (scoped['week'] == sel_wk)].groupby('channel')['sales'].sum()
ch_tot = ch_ty.sum()

# Stores to watch: below LY three weeks running
recent = sw[(sw['az_year'] == sel_yr) & sw['week'].between(sel_wk - 2, sel_wk)]
watch = (recent.assign(below=recent['sales'] < recent['ly_sales'])
               .groupby('store').agg(n=('below', 'sum'), weeks=('week', 'nunique')))
watch = watch[(watch['n'] == 3) & (watch['weeks'] == 3)].index.tolist()

# ── Narrative ──
def word(v, up="up", down="down"):
    return up if pd.notna(v) and v >= 0 else down

headline = (f"Week {sel_wk} net sales were {currency} {fmt(W['sales'])}, "
            f"{word(W['vs_ly'])} {pct(abs(W['vs_ly'])).lstrip('+')} vs last year")
if pd.notna(W['vs_bgt']):
    headline += f" and {pct(W['vs_bgt'])} vs budget"
headline += "."

drivers = []
if pd.notna(W['vs_t']) and pd.notna(W['vs_basket']):
    drivers.append(f"Tickets were {pct(W['vs_t'])} and average basket {pct(W['vs_basket'])} "
                   f"({currency} {fmt(W['basket'], 1)}), so the change was driven mainly by "
                   f"{'traffic' if abs(W['vs_t']) >= abs(W['vs_basket']) else 'basket size'}.")
if pd.notna(W['lfl']):
    drivers.append(f"Like-for-like growth was {pct(W['lfl'])}.")
if pd.notna(wow):
    drivers.append(f"Compared with week {sel_wk - 1}, sales moved {pct(wow)}.")

ytd_line = (f"Year to date (W1–W{sel_wk}) sales are {currency} {fmt(Y['sales'])}, "
            f"{pct(Y['vs_ly'])} vs LY")
if pd.notna(Y['vs_bgt']):
    gap = Y['sales'] - Y['budget']
    ytd_line += f" and {pct(Y['vs_bgt'])} vs budget ({currency} {fmt(abs(gap))} {'ahead' if gap >= 0 else 'behind'})"
ytd_line += "."

# ── Build plain text ──
subject = f"{scope_lbl if scope_lbl.startswith('PAUL') else 'PAUL ' + scope_lbl} · Weekly Sales · AZ{sel_yr} W{sel_wk} · {pct(W['vs_ly'])} vs LY"
L = [f"Dear all,", "", f"Please find below the sales summary for AZ{sel_yr} week {sel_wk}.", "",
     "HEADLINES", f"• {headline}"] + [f"• {d}" for d in drivers] + [f"• {ytd_line}", ""]
if len(countries) > 1:
    L += ["BY COUNTRY"] + [f"• {c}: {currency} {fmt(r['sales'])} ({pct(r['vs'])} vs LY)"
                           for c, r in countries.iterrows()] + [""]
if len(ch_ty):
    L += ["BY CHANNEL"] + [f"• {c}: {fmt(v / ch_tot * 100, 0)}% of sales, {pct(safe_pct(v, ch_ly.get(c, 0)))} vs LY"
                           for c, v in ch_ty.sort_values(ascending=False).items()] + [""]
if len(winners):
    L += ["WINS"] + [f"• {r['store']}: {pct(r['vs_ly'])} vs LY ({currency} {fmt(r['sales'])})"
                     for _, r in winners.iterrows()] + [""]
if len(losers):
    L += ["NEEDS ATTENTION"] + [f"• {r['store']}: {pct(r['vs_ly'])} vs LY ({currency} {fmt(r['sales'])})"
                                for _, r in losers.iterrows()] + [""]
if watch:
    L += ["STORES TO WATCH (below LY 3 weeks running)"] + [f"• {s}" for s in watch] + [""]
if new_stores:
    L += [f"New / no-LY stores (excluded from LFL): {', '.join(new_stores)}", ""]
L += ["Best regards,", sender or ""]
text = "\n".join(L).rstrip()

# ── Build HTML email ──
def row(cells, bold=False):
    tag = "th" if bold else "td"
    return "<tr>" + "".join(f"<{tag} style='padding:6px 10px;border-bottom:1px solid #e5e5e5;text-align:left'>{c}</{tag}>" for c in cells) + "</tr>"

def colored(v):
    if not (pd.notna(v) and np.isfinite(v)): return "—"
    return f"<span style='color:{'#1E8449' if v >= 0 else '#C0392B'};font-weight:600'>{pct(v)}</span>"

kpi_tbl = ("<table style='border-collapse:collapse;font-size:13px;margin:8px 0 16px'>" +
           row(["", f"Week {sel_wk}", "YTD"], True) +
           row(["Net Sales", f"{currency} {fmt(W['sales'])}", f"{currency} {fmt(Y['sales'])}"]) +
           row(["vs LY", colored(W['vs_ly']), colored(Y['vs_ly'])]) +
           row(["LFL", colored(W['lfl']), colored(Y['lfl'])]) +
           row(["vs Budget", colored(W['vs_bgt']), colored(Y['vs_bgt'])]) +
           row(["Tickets vs LY", colored(W['vs_t']), colored(Y['vs_t'])]) +
           row(["Avg Basket", fmt(W['basket'], 1), fmt(Y['basket'], 1)]) + "</table>")

def store_tbl(d):
    return ("<table style='border-collapse:collapse;font-size:13px;margin:4px 0 16px'>" +
            row(["Store", "Sales", "vs LY", "vs Budget"], True) +
            "".join(row([r['store'], fmt(r['sales']), colored(r['vs_ly']), colored(r['vs_bgt'])])
                    for _, r in d.iterrows()) + "</table>")

H = [f"<div style='font-family:Arial,sans-serif;color:#1A2A3A;max-width:680px'>",
     "<p>Dear all,</p>",
     f"<p>Please find below the sales summary for <b>AZ{sel_yr} week {sel_wk}</b>.</p>",
     f"<p style='font-size:15px'><b>{headline}</b></p>",
     "<ul>" + "".join(f"<li>{d}</li>" for d in drivers + [ytd_line]) + "</ul>", kpi_tbl]
if len(countries) > 1:
    H += ["<h4 style='margin:12px 0 4px'>By country</h4>",
          "<table style='border-collapse:collapse;font-size:13px'>" + row(["Country", "Sales", "vs LY"], True) +
          "".join(row([c, fmt(r['sales']), colored(r['vs'])]) for c, r in countries.iterrows()) + "</table>"]
if len(winners):
    H += ["<h4 style='margin:16px 0 4px;color:#1E8449'>🏆 Wins</h4>", store_tbl(winners)]
if len(losers):
    H += ["<h4 style='margin:16px 0 4px;color:#C0392B'>⚠️ Needs attention</h4>", store_tbl(losers)]
if watch:
    H += ["<p><b>Stores to watch</b> (below LY three weeks running): " + ", ".join(watch) + "</p>"]
H += [f"<p>Best regards,<br>{sender}</p></div>"]
html = "\n".join(H)

# ── Display ──
c1, c2 = st.columns([3, 2])
with c1:
    section("👀 Preview")
    st.markdown(f"**Subject:** {subject}")
    components.html(f"<div style='background:#fff;padding:16px;border-radius:8px'>{html}</div>",
                          height=720, scrolling=True)
with c2:
    section("📤 Send it")
    st.download_button("⬇ Download email (.html)", html.encode(), f"PAUL_AZ{sel_yr}_W{sel_wk}.html",
                       "text/html", use_container_width=True)
    st.download_button("⬇ Download text (.txt)", f"Subject: {subject}\n\n{text}".encode(),
                       f"PAUL_AZ{sel_yr}_W{sel_wk}.txt", "text/plain", use_container_width=True)
    mail_body = text if len(text) < 1800 else text[:1800] + "\n…(see attached report)"
    st.link_button("✉️ Open in my email app", f"mailto:?subject={quote(subject)}&body={quote(mail_body)}",
                   use_container_width=True)
    st.markdown("**Copy plain text**")
    st.code(f"Subject: {subject}\n\n{text}", language=None)
    st.caption("Tip: open the .html file in your browser, select all and paste into Outlook/Gmail "
               "to keep the coloured tables.")
