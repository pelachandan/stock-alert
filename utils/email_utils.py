import os
import smtplib
from email.mime.text import MIMEText
import pandas as pd
from datetime import datetime

# --- Helper: HTML table with score-based row coloring ---
def df_to_html_table(df, score_column="Score", title="", max_rows=5):
    if df is None or df.empty:
        return f"<p>No {title} today.</p>"

    if score_column and score_column in df.columns:
        df = df.sort_values(by=score_column, ascending=False)
    if max_rows is not None:
        df = df.head(max_rows)

    html = f"<h2>{title}</h2>"
    html += "<table border='1' cellpadding='4' cellspacing='0' style='border-collapse:collapse;'>"
    html += "<tr>"
    for col in df.columns:
        html += f"<th style='background-color:#f2f2f2;font-weight:bold;text-align:center;'>{col}</th>"
    html += "</tr>"

    for _, row in df.iterrows():
        score = row.get(score_column, 0) if score_column else 0
        if score_column:
            if score >= 8.5: color = "#c6efce"
            elif score >= 6.5: color = "#ffeb9c"
            else: color = "#f4c7c3"
        else:
            color = "#ffffff"
        html += f"<tr style='background-color:{color};'>"
        for col in df.columns:
            html += f"<td style='text-align:center;'>{row[col]}</td>"
        html += "</tr>"

    html += "</table><br>"
    return html

# --- Normalize lists for table-friendly DataFrames ---
def normalize_highs_for_table(high_list):
    if not high_list: return pd.DataFrame()
    df = pd.DataFrame(high_list)
    cols = ["Ticker","Company","Close","High52","PctFrom52High","EMA20","EMA50","EMA200","VolumeRatio","RSI14","Score"]
    return df[[c for c in cols if c in df.columns]]

def normalize_watchlist_for_table(watch_list):
    if not watch_list: return pd.DataFrame()
    df = pd.DataFrame(watch_list)
    cols = ["Ticker","Company","Close","High52","PctFrom52High","EMA20","EMA50","EMA200","RSI14"]
    return df[[c for c in cols if c in df.columns]]

def normalize_generic_for_table(generic_list):
    if not generic_list: return pd.DataFrame()
    return pd.DataFrame(generic_list)

# --- Main Email Sender ---
def send_email_alert(
    prebuy_df,
    presell_df,
    high_buy_list=None,
    high_watch_list=None,
    ema_list=None,
    consolidation_list=None,
    rs_list=None,
    subject_prefix="📊 Market Summary",
    html_body=None
):
    if html_body:
        body_html = html_body
    else:
        body_html = "<h1>📊 Daily Market Scan</h1>"

        # EMA Crossovers
        if ema_list:
            body_html += df_to_html_table(pd.DataFrame(ema_list), "Score", "📈 EMA Crossovers (Trend Ignition)")
        else:
            body_html += "<p>No EMA crossovers today.</p>"

        # Pre-Buy Actionable Trades
        body_html += df_to_html_table(prebuy_df, "Score", "🔥 Pre-Buy Actionable Trades")

        # Pre-Sell Actionable Trades
        body_html += df_to_html_table(presell_df, "Score", "📉 Pre-Sell Actionable Trades")

        # 52-Week High BUY-READY
        if high_buy_list:
            df_high = normalize_highs_for_table(high_buy_list)
            body_html += df_to_html_table(df_high, "Score", "🚀 52-Week High Continuation (BUY-READY)")
        else:
            body_html += "<p>No BUY-ready 52-week highs today.</p>"

        # 52-Week High Watchlist
        if high_watch_list:
            df_watch = normalize_watchlist_for_table(high_watch_list)
            body_html += df_to_html_table(df_watch, None, "👀 52-Week Near-High Watchlist")
        else:
            body_html += "<p>No 52-week near-high watchlist stocks today.</p>"

        # Consolidation Breakouts
        if consolidation_list:
            df_cons = normalize_generic_for_table(consolidation_list)
            body_html += df_to_html_table(df_cons, "Score" if "Score" in df_cons.columns else None, "📊 Consolidation Breakouts")
        else:
            body_html += "<p>No consolidation breakout setups today.</p>"

        # Relative Strength Leaders
        if rs_list:
            df_rs = normalize_generic_for_table(rs_list)
            body_html += df_to_html_table(df_rs, "Score" if "Score" in df_rs.columns else None, "⭐ Relative Strength / Sector Leaders")
        else:
            body_html += "<p>No relative strength setups today.</p>"

    # Email credentials
    sender = os.getenv("EMAIL_SENDER")
    receiver = os.getenv("EMAIL_RECEIVER")
    password = os.getenv("EMAIL_PASSWORD")
    subject = f"{subject_prefix} – {datetime.now().strftime('%Y-%m-%d')}"

    # Build MIME email
    msg = MIMEText(body_html, "html")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = receiver

    # Send email
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
        print(f"✅ Email sent: {subject}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
