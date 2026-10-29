import streamlit as st
import streamlit.components.v1 as components
import sqlite3
import pandas as pd
import io
import os
import base64
import subprocess
from datetime import date

# ----------------- App Configuration -----------------
st.set_page_config(
    page_title="ANNUAL ATHLETICS CHAMPIONSHIP 2026",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ----------------- Helper: Base64 Background Encoder -----------------
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

# ----------------- Safe Secret Loading -----------------
try:
    auth_secrets = st.secrets.get("auth", {})
    ADMIN_USER = auth_secrets.get("admin_username", "admin")
    ADMIN_PASS = auth_secrets.get("admin_password", "admin123")
except Exception:
    ADMIN_USER = "admin"
    ADMIN_PASS = "admin123"

# ----------------- Database Setup & Persistence -----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "athletic_meet.db")
STATIC_FILE = os.path.join(BASE_DIR, "latest_board.html")

def get_connection():
    return sqlite3.connect(DB_FILE, timeout=30, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # 1. Ensure Results table exists
    c.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_date TEXT,
            event_name TEXT,
            category TEXT,
            gold_student TEXT,
            gold_house TEXT,
            silver_student TEXT,
            silver_house TEXT,
            bronze_student TEXT,
            bronze_house TEXT
        )
    ''')

    # 2. Dynamically add missing columns
    c.execute("PRAGMA table_info(results)")
    existing_cols = [row[1] for row in c.fetchall()]

    new_columns = [
        ("gold_class", "TEXT"),
        ("gold_adm", "TEXT"),
        ("gold_perf", "TEXT"),
        ("gold_pts", "INTEGER DEFAULT 5"),
        ("silver_class", "TEXT"),
        ("silver_adm", "TEXT"),
        ("silver_perf", "TEXT"),
        ("silver_pts", "INTEGER DEFAULT 4"),
        ("bronze_class", "TEXT"),
        ("bronze_adm", "TEXT"),
        ("bronze_perf", "TEXT"),
        ("bronze_pts", "INTEGER DEFAULT 3"),
    ]

    for col_name, col_type in new_columns:
        if col_name not in existing_cols:
            c.execute(f"ALTER TABLE results ADD COLUMN {col_name} {col_type}")

    # Standardize scoring rules: Gold=5, Silver=4, Bronze=3
    c.execute("UPDATE results SET silver_pts = 4 WHERE silver_pts = 3 OR silver_pts IS NULL")
    c.execute("UPDATE results SET bronze_pts = 3 WHERE bronze_pts = 1 OR bronze_pts IS NULL")
    c.execute("UPDATE results SET gold_pts = 5 WHERE gold_pts IS NULL")

    # 3. Ensure Announcements table exists
    c.execute('''
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_date TEXT,
            announcement TEXT
        )
    ''')

    # 4. Ensure House Points table exists
    c.execute('''
        CREATE TABLE IF NOT EXISTS house_points (
            house_code TEXT PRIMARY KEY,
            pp_points INTEGER DEFAULT 0
        )
    ''')
    conn.commit()

    c.execute("SELECT count(*) FROM house_points")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO house_points (house_code, pp_points) VALUES (?, ?)", [
            ("CARIAPPA", 0),
            ("MANEKSHAW", 0),
            ("SUNDARJI", 0),
            ("VAIDYA", 0)
        ])
        conn.commit()
    conn.close()

init_db()

# ----------------- Canonical Definitions -----------------
houses = ["CARIAPPA", "MANEKSHAW", "SUNDARJI", "VAIDYA"]

def normalize_house(name):
    if not name:
        return "MANEKSHAW"
    n = str(name).strip().upper()
    if n in ["C", "CAR", "CARIAPPA"]:
        return "CARIAPPA"
    elif n in ["M", "MAN", "MANEKSHAW"]:
        return "MANEKSHAW"
    elif n in ["S", "SUN", "SUNDARJI"]:
        return "SUNDARJI"
    elif n in ["V", "VAI", "VAIDYA"]:
        return "VAIDYA"
    return n

# ----------------- Snapshot & Git Sync Functions -----------------
def sync_to_github():
    """Pushes the updated snapshot to GitHub Pages repository."""
    try:
        subprocess.run(["git", "add", "latest_board.html"], check=False)
        subprocess.run(["git", "commit", "-m", "Auto-update standings snapshot"], check=False)
        subprocess.run(["git", "push", "origin", "main"], check=False)
    except Exception as e:
        print(f"Git push status: {e}")

def export_static_board():
    """Generates the frozen standalone HTML snapshot file for 24/7 display."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM results ORDER BY id ASC", conn)
    announcements_df = pd.read_sql_query("SELECT announcement FROM announcements ORDER BY id DESC LIMIT 5", conn)
    pp_df = pd.read_sql_query("SELECT house_code, pp_points FROM house_points", conn)
    conn.close()

    pp_dict = {normalize_house(r['house_code']): r['pp_points'] for _, r in pp_df.iterrows()}
    tally = {h: {"Gold": 0, "Silver": 0, "Bronze": 0, "TotalMedals": 0, "PP": int(pp_dict.get(h, 0)), "EarnedPts": 0, "TP": 0} for h in houses}

    for _, r in df.iterrows():
        gh = normalize_house(r["gold_house"])
        sh = normalize_house(r["silver_house"])
        bh = normalize_house(r["bronze_house"])
        if gh in tally:
            tally[gh]["Gold"] += 1
            tally[gh]["EarnedPts"] += int(r["gold_pts"] if r["gold_pts"] is not None else 5)
        if sh in tally:
            tally[sh]["Silver"] += 1
            tally[sh]["EarnedPts"] += int(r["silver_pts"] if r["silver_pts"] is not None else 4)
        if bh in tally:
            tally[bh]["Bronze"] += 1
            tally[bh]["EarnedPts"] += int(r["bronze_pts"] if r["bronze_pts"] is not None else 3)

    for h in tally:
        tally[h]["TotalMedals"] = tally[h]["Gold"] + tally[h]["Silver"] + tally[h]["Bronze"]
        tally[h]["TP"] = tally[h]["PP"] + tally[h]["EarnedPts"]

    sorted_houses = sorted(
        houses,
        key=lambda h: (tally[h]["TP"], tally[h]["Gold"], tally[h]["Silver"], tally[h]["Bronze"], tally[h]["TotalMedals"]),
        reverse=True
    )

    tally_html = ""
    for rank, h in enumerate(sorted_houses, start=1):
        rank_disp = "👑 1" if rank == 1 else f"#{rank}"
        tally_html += f"""
        <div class="house-tally-row">
            <div style="font-weight:900; font-size:14px; color:#334155;">{rank_disp}</div>
            <div><span class="house-box-label house-{h}">{h}</span></div>
            <div class="tally-num gold-text">{tally[h]['Gold']}</div>
            <div class="tally-num silver-text">{tally[h]['Silver']}</div>
            <div class="tally-num bronze-text">{tally[h]['Bronze']}</div>
            <div class="tally-num total-col">{tally[h]['TotalMedals']}</div>
            <div class="tally-num pp-col">{tally[h]['PP']}</div>
            <div class="tally-num tp-col">{tally[h]['TP']}</div>
        </div>
        """

    cards_html = ""
    if df.empty:
        cards_html = "<div style='text-align:center; padding: 40px; color:#64748b; font-weight:800;'>🏆 Events are underway! Results will appear here as soon as verified.</div>"
    else:
        for _, r in df.iterrows():
            gh = normalize_house(r['gold_house'])
            sh = normalize_house(r['silver_house'])
            bh = normalize_house(r['bronze_house'])
            g_pts = 5 if r['gold_pts'] in [None, 0] else r['gold_pts']
            s_pts = 4 if r['silver_pts'] in [None, 3, 0] else r['silver_pts']
            b_pts = 3 if r['bronze_pts'] in [None, 1, 0] else r['bronze_pts']

            cards_html += f"""
            <div class="event-doc-card">
                <div class="doc-card-header">
                    <span class="doc-badge-event">{r['event_name']}</span>
                    <span class="doc-badge-cat">{r['category']}</span>
                    <span class="doc-date-badge">📅 {r['event_date']}</span>
                </div>
                <table class="doc-sub-table">
                    <thead><tr><th style="width:8%;">Place</th><th style="width:20%;">Name</th><th style="width:12%;">Class</th><th style="width:16%;">Adm. No.</th><th style="width:17%;">Ti/Ht/Dis</th><th style="width:18%;">House</th><th style="width:9%;">Pts</th></tr></thead>
                    <tbody>
                        <tr class="row-gold"><td class="place-badge gold-bg">1st 🥇</td><td class="compact-name">{r['gold_student']}</td><td>{r['gold_class'] or '-'}</td><td>{r['gold_adm'] or '-'}</td><td class="perf-text">{r['gold_perf'] or '-'}</td><td><span class="mini-house-badge house-{gh}">{gh}</span></td><td class="bold-pts">+{g_pts}</td></tr>
                        <tr class="row-silver"><td class="place-badge silver-bg">2nd 🥈</td><td class="compact-name">{r['silver_student'] or '-'}</td><td>{r['silver_class'] or '-'}</td><td>{r['silver_adm'] or '-'}</td><td class="perf-text">{r['silver_perf'] or '-'}</td><td><span class="mini-house-badge house-{sh}">{sh}</span></td><td class="bold-pts">+{s_pts}</td></tr>
                        <tr class="row-bronze"><td class="place-badge bronze-bg">3rd 🥉</td><td class="compact-name">{r['bronze_student'] or '-'}</td><td>{r['bronze_class'] or '-'}</td><td>{r['bronze_adm'] or '-'}</td><td class="perf-text">{r['bronze_perf'] or '-'}</td><td><span class="mini-house-badge house-{bh}">{bh}</span></td><td class="bold-pts">+{b_pts}</td></tr>
                    </tbody>
                </table>
            </div>
            """

    today_events = " • ".join(announcements_df['announcement'].tolist()) if not announcements_df.empty else "All championship track and field events concluded for the day."

    snapshot_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
    body {{ background-color: #f1f5f9; padding: 4px 10px 16px 10px; overflow-x: hidden; }}
    .offline-ribbon {{ background: #991b1b; color: #ffffff; text-align: center; font-size: 13px; font-weight: 800; padding: 6px; border-radius: 6px; margin-bottom: 8px; }}
    .top-banner {{ background: #002244; color: #ffffff; border-radius: 8px 8px 0 0; padding: 8px 18px; display: flex; align-items: center; justify-content: space-between; }}
    .top-banner .title {{ font-size: 22px; font-weight: 900; letter-spacing: 1.5px; color: #ffffff; text-transform: uppercase; }}
    .top-banner .school-name {{ font-size: 16px; font-weight: 900; color: #ffdd00; text-transform: uppercase; }}
    .top-ticker {{ width: 100%; background-color: #002244; color: #FFDD00; padding: 7px 12px; font-size: 15px; font-weight: 800; border-bottom: 3px solid #f59e0b; border-radius: 0 0 8px 8px; margin-bottom: 12px; }}
    .dashboard-grid {{ display: grid; grid-template-columns: 3.8fr 6.2fr; gap: 14px; width: 100%; }}
    @media (max-width: 900px) {{ .dashboard-grid {{ grid-template-columns: 1fr; }} }}
    .main-panel {{ background: #ffffff; border: 2.5px solid #002D62; border-radius: 10px; overflow: hidden; }}
    .panel-top-header {{ background: #004080; color: #ffffff; padding: 9px 14px; font-weight: 900; font-size: 16px; }}
    .tally-container {{ padding: 10px 6px; background: #f8fafc; }}
    .medal-icon-row {{ display: grid; grid-template-columns: 0.6fr 2.1fr 0.7fr 0.7fr 0.7fr 0.8fr 0.8fr 1.0fr; text-align: center; font-size: 12px; font-weight: 900; margin-bottom: 8px; }}
    .house-tally-row {{ display: grid; grid-template-columns: 0.6fr 2.1fr 0.7fr 0.7fr 0.7fr 0.8fr 0.8fr 1.0fr; align-items: center; text-align: center; background: #ffffff; border: 1.8px solid #cbd5e1; border-radius: 7px; margin-bottom: 8px; padding: 6px 2px; }}
    .house-box-label {{ display: inline-block; padding: 4px; border-radius: 5px; font-size: 12px; font-weight: 900; width: 95%; text-transform: uppercase; color: #fff; }}
    .house-MANEKSHAW {{ background: #D90429 !important; }}
    .house-CARIAPPA {{ background: #008000 !important; }}
    .house-SUNDARJI {{ background: #0047AB !important; }}
    .house-VAIDYA {{ background: #FFC300 !important; color: #111 !important; }}
    .tally-num {{ font-size: 16px; font-weight: 900; }}
    .gold-text {{ color: #d97706; }} .silver-text {{ color: #64748b; }} .bronze-text {{ color: #c2410c; }}
    .total-col {{ color: #0284c7; }} .pp-col {{ color: #64748b; }}
    .tp-col {{ background: #002244; color: #ffdd00 !important; border-radius: 5px; padding: 3px 2px; display: inline-block; }}
    .winner-scroll-box {{ height: 530px; overflow-y: auto; background: #f8fafc; padding: 8px; }}
    .event-doc-card {{ background: #ffffff; border: 2px solid #cbd5e1; border-radius: 8px; margin-bottom: 12px; overflow: hidden; }}
    .doc-card-header {{ background: #002D62; color: #ffffff; padding: 7px 12px; display: flex; justify-content: space-between; font-weight: 800; font-size: 14px; }}
    .doc-badge-event {{ font-size: 15px; color: #ffdd00; text-transform: uppercase; font-weight: 900; }}
    .doc-badge-cat {{ background: rgba(255, 255, 255, 0.22); padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 700; color: #fff; }}
    .doc-date-badge {{ font-size: 12px; color: #cbd5e1; font-weight: 700; }}
    .doc-sub-table {{ width: 100%; border-collapse: collapse; text-align: center; font-size: 13px; }}
    .doc-sub-table th {{ background: #e2e8f0; color: #0f172a; padding: 5px 3px; font-weight: 800; border-bottom: 2px solid #cbd5e1; }}
    .doc-sub-table td {{ padding: 6px 3px; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #334155; }}
    .compact-name {{ font-weight: 900 !important; color: #0f172a !important; text-align: left; padding-left: 6px !important; }}
    .perf-text {{ font-weight: 800; color: #b91c1c; font-family: monospace; }}
    .bold-pts {{ font-weight: 900; color: #008000; }}
    .place-badge {{ font-weight: 900; border-radius: 4px; }}
    .gold-bg {{ background: #fef08a; color: #854d0e; }}
    .silver-bg {{ background: #f1f5f9; color: #475569; }}
    .bronze-bg {{ background: #fed7aa; color: #9a3412; }}
    .mini-house-badge {{ display: inline-block; padding: 2px 5px; border-radius: 4px; font-size: 10.5px; font-weight: 800; color: #fff; }}
</style>
</head>
<body>
    <div class="offline-ribbon">🔒 SESSION CONCLUDED (OFFLINE STANDINGS) — Recorded from Army Public School Sports Desk</div>
    <div class="top-banner">
        <div>
            <div class="title">ANNUAL ATHLETICS CHAMPIONSHIP 2026</div>
            <div class="school-name">ARMY PUBLIC SCHOOL, MEERUT CANTT</div>
        </div>
    </div>
    <div class="top-ticker">📢 <b>FINAL STATUS:</b> {today_events}</div>
    <div class="dashboard-grid">
        <div class="main-panel">
            <div class="panel-top-header">MEDAL & POINTS TALLY (OFFICIAL)</div>
            <div class="tally-container">
                <div class="medal-icon-row">
                    <div>POS</div><div>HOUSE</div><div>G</div><div>S</div><div>B</div><div>MED</div><div>PP</div><div style="color:#d97706;">TP</div>
                </div>
                {tally_html}
            </div>
        </div>
        <div class="main-panel">
            <div class="panel-top-header">COMPLETED EVENT RESULTS</div>
            <div class="winner-scroll-box">
                {cards_html}
            </div>
        </div>
    </div>
</body>
</html>
"""
    with open(STATIC_FILE, "w", encoding="utf-8") as f:
        f.write(snapshot_html)
    
    sync_to_github()

# ----------------- Root-Level Live Display Fragment -----------------
# Defining the fragment at the module level prevents the "Fragment with id does not exist" error
def render_live_screen(scroll_speed, marquee_velocity, marquee_font_size, marquee_bg_color, marquee_text_color):
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM results ORDER BY id ASC", conn)
    announcements_df = pd.read_sql_query("SELECT announcement FROM announcements ORDER BY id DESC LIMIT 5", conn)
    pp_df = pd.read_sql_query("SELECT house_code, pp_points FROM house_points", conn)
    conn.close()

    pp_dict = {normalize_house(r['house_code']): r['pp_points'] for _, r in pp_df.iterrows()}
    tally = {h: {"Gold": 0, "Silver": 0, "Bronze": 0, "TotalMedals": 0, "PP": int(pp_dict.get(h, 0)), "EarnedPts": 0, "TP": 0} for h in houses}
    
    for _, r in df.iterrows():
        gh = normalize_house(r["gold_house"])
        sh = normalize_house(r["silver_house"])
        bh = normalize_house(r["bronze_house"])

        if gh in tally:
            tally[gh]["Gold"] += 1
            tally[gh]["EarnedPts"] += int(r["gold_pts"] if r["gold_pts"] is not None else 5)
        if sh in tally:
            tally[sh]["Silver"] += 1
            tally[sh]["EarnedPts"] += int(r["silver_pts"] if r["silver_pts"] is not None else 4)
        if bh in tally:
            tally[bh]["Bronze"] += 1
            tally[bh]["EarnedPts"] += int(r["bronze_pts"] if r["bronze_pts"] is not None else 3)

    for h in tally:
        tally[h]["TotalMedals"] = tally[h]["Gold"] + tally[h]["Silver"] + tally[h]["Bronze"]
        tally[h]["TP"] = tally[h]["PP"] + tally[h]["EarnedPts"]

    sorted_houses = sorted(
        houses,
        key=lambda h: (
            tally[h]["TP"],
            tally[h]["Gold"],
            tally[h]["Silver"],
            tally[h]["Bronze"],
            tally[h]["TotalMedals"]
        ),
        reverse=True
    )

    tally_html = ""
    for rank, h in enumerate(sorted_houses, start=1):
        rank_display = "👑 1" if rank == 1 else f"#{rank}"
        
        tally_html += f"""
        <div class="house-tally-row">
            <div style="font-weight:900; font-size:14px; color:#334155;">{rank_display}</div>
            <div><span class="house-box-label house-{h}">{h}</span></div>
            <div class="tally-num gold-text">{tally[h]['Gold']}</div>
            <div class="tally-num silver-text">{tally[h]['Silver']}</div>
            <div class="tally-num bronze-text">{tally[h]['Bronze']}</div>
            <div class="tally-num total-col">{tally[h]['TotalMedals']}</div>
            <div class="tally-num pp-col">{tally[h]['PP']}</div>
            <div class="tally-num tp-col">{tally[h]['TP']}</div>
        </div>
        """

    cards_html = ""
    if df.empty:
        cards_html = """
        <div style="text-align:center; padding: 50px 20px; color:#64748b; font-weight:800; font-size:18px;">
            🏆 Events are underway! Results will appear here as soon as verified by the in-charge.
        </div>
        """
    else:
        for idx, r in df.iterrows():
            gh = normalize_house(r['gold_house'])
            sh = normalize_house(r['silver_house'])
            bh = normalize_house(r['bronze_house'])

            g_pts_disp = 5 if r['gold_pts'] in [None, 0] else r['gold_pts']
            s_pts_disp = 4 if r['silver_pts'] in [None, 3, 0] else r['silver_pts']
            b_pts_disp = 3 if r['bronze_pts'] in [None, 1, 0] else r['bronze_pts']

            cards_html += f"""
            <div class="event-doc-card">
                <div class="doc-card-header">
                    <span class="doc-badge-event">{r['event_name']}</span>
                    <span class="doc-badge-cat">{r['category']}</span>
                    <span class="doc-date-badge">📅 {r['event_date']}</span>
                </div>
                <table class="doc-sub-table">
                    <thead>
                        <tr>
                            <th style="width:8%;">Place</th>
                            <th style="width:20%;">Name</th>
                            <th style="width:12%;">Class</th>
                            <th style="width:16%;">Adm. No.</th>
                            <th style="width:17%;">Ti/Ht/Dis</th>
                            <th style="width:18%;">House</th>
                            <th style="width:9%;">Pts</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr class="row-gold">
                            <td class="place-badge gold-bg">1st 🥇</td>
                            <td class="compact-name">{r['gold_student']}</td>
                            <td>{r['gold_class'] or '-'}</td>
                            <td>{r['gold_adm'] or '-'}</td>
                            <td class="perf-text">{r['gold_perf'] or '-'}</td>
                            <td><span class="mini-house-badge house-{gh}">{gh}</span></td>
                            <td class="bold-pts">+{g_pts_disp}</td>
                        </tr>
                        <tr class="row-silver">
                            <td class="place-badge silver-bg">2nd 🥈</td>
                            <td class="compact-name">{r['silver_student'] or '-'}</td>
                            <td>{r['silver_class'] or '-'}</td>
                            <td>{r['silver_adm'] or '-'}</td>
                            <td class="perf-text">{r['silver_perf'] or '-'}</td>
                            <td><span class="mini-house-badge house-{sh}">{sh}</span></td>
                            <td class="bold-pts">+{s_pts_disp}</td>
                        </tr>
                        <tr class="row-bronze">
                            <td class="place-badge bronze-bg">3rd 🥉</td>
                            <td class="compact-name">{r['bronze_student'] or '-'}</td>
                            <td>{r['bronze_class'] or '-'}</td>
                            <td>{r['bronze_adm'] or '-'}</td>
                            <td class="perf-text">{r['bronze_perf'] or '-'}</td>
                            <td><span class="mini-house-badge house-{bh}">{bh}</span></td>
                            <td class="bold-pts">+{b_pts_disp}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            """

    if scroll_speed > 0 and len(df) > 2:
        anim_css = f"animation: scrollUp {scroll_speed}s linear infinite;"
        scroll_content = cards_html
    else:
        anim_css = "animation: none; overflow-y: auto;"
        scroll_content = cards_html

    today_events = " • ".join(announcements_df['announcement'].tolist()) if not announcements_df.empty else "All championship track and field events proceeding on schedule. Standings updated live!"

    full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
    }}
    body {{
        background-color: #f1f5f9;
        padding: 4px 10px 16px 10px;
        overflow-x: hidden;
    }}

    .top-banner {{
        background: #002244;
        color: #ffffff;
        border-radius: 8px 8px 0 0;
        padding: 8px 18px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 10px rgba(0, 34, 68, 0.2);
    }}
    .banner-left {{ display: flex; align-items: center; gap: 10px; }}
    .banner-center {{ text-align: center; flex-grow: 1; }}
    .top-banner .title {{ font-size: clamp(19px, 2.7vw, 30px); font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase; color: #ffffff; line-height: 1.15; }}
    .top-banner .school-name {{ font-size: clamp(14px, 1.8vw, 20px); font-weight: 900; letter-spacing: 1.5px; color: #ffdd00; margin-top: 3px; text-transform: uppercase; }}
    .top-banner .date-bracket {{ font-size: clamp(11.5px, 1.2vw, 14px); letter-spacing: 1px; font-weight: 800; color: #93c5fd; margin-top: 2px; text-transform: uppercase; }}
    .clock-badge {{ background: rgba(0, 0, 0, 0.4); border: 1.5px solid #ffcc00; border-radius: 8px; padding: 4px 10px; text-align: right; min-width: 130px; }}
    .clock-date {{ font-size: 11px; color: #e2e8f0; font-weight: 700; }}
    .clock-time {{ font-size: 15px; color: #ffdd00; font-weight: 900; font-family: monospace; }}
    .top-ticker {{ width: 100%; background-color: {marquee_bg_color}; color: {marquee_text_color}; padding: 6px 0; font-size: {marquee_font_size}px; font-weight: 800; overflow: hidden; white-space: nowrap; border-bottom: 3px solid #f59e0b; border-radius: 0 0 8px 8px; margin-bottom: 12px; box-shadow: 0 3px 6px rgba(0,0,0,0.12); position: relative; }}
    #tickerWrapper {{ display: inline-block; white-space: nowrap; position: relative; }}
    .dashboard-grid {{ display: grid; grid-template-columns: 3.8fr 6.2fr; gap: 14px; width: 100%; }}
    @media (max-width: 1000px) {{
        .dashboard-grid {{ grid-template-columns: 1fr; gap: 10px; }}
        .winner-scroll-box {{ height: 480px !important; }}
    }}
    .main-panel {{ background: #ffffff; border: 2.5px solid #002D62; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
    .panel-top-header {{ background: #004080; color: #ffffff; padding: 9px 14px; display: flex; align-items: center; gap: 10px; }}
    .panel-top-title {{ font-size: 18px; font-weight: 900; text-transform: uppercase; letter-spacing: 0.8px; }}
    .panel-top-sub {{ font-size: 12px; font-weight: 600; color: #dbeafe; }}
    .tally-container {{ padding: 10px 6px; background: #f8fafc; }}
    .medal-icon-row {{ display: grid; grid-template-columns: 0.6fr 2.1fr 0.7fr 0.7fr 0.7fr 0.8fr 0.8fr 1.0fr; text-align: center; align-items: end; margin-bottom: 10px; font-size: 12px; font-weight: 900; color: #0f172a; }}
    .medal-header-col {{ display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; }}
    .medal-coin {{ display: flex; align-items: center; justify-content: center; width: 24px; height: 24px; border-radius: 50%; font-weight: 900; font-size: 13px; box-shadow: 0 2px 4px rgba(0,0,0,0.18); }}
    .coin-gold {{ background: radial-gradient(circle at 30% 30%, #fff6a6, #f59e0b); color: #78350f; border: 1.5px solid #d97706; }}
    .coin-silver {{ background: radial-gradient(circle at 30% 30%, #ffffff, #cbd5e1); color: #334155; border: 1.5px solid #94a3b8; }}
    .coin-bronze {{ background: radial-gradient(circle at 30% 30%, #fed7aa, #ea580c); color: #7c2d12; border: 1.5px solid #c2410c; }}
    .house-tally-row {{ display: grid; grid-template-columns: 0.6fr 2.1fr 0.7fr 0.7fr 0.7fr 0.8fr 0.8fr 1.0fr; align-items: center; text-align: center; background: #ffffff; border: 1.8px solid #cbd5e1; border-radius: 7px; margin-bottom: 8px; padding: 6px 2px; }}
    .house-box-label {{ display: inline-block; padding: 4px 4px; border-radius: 5px; font-size: 12px; font-weight: 900; text-align: center; letter-spacing: 0.4px; box-shadow: 0 1px 3px rgba(0,0,0,0.15); width: 95%; text-transform: uppercase; }}
    .house-MANEKSHAW {{ background: #D90429 !important; color: #ffffff !important; }}
    .house-CARIAPPA {{ background: #008000 !important; color: #ffffff !important; }}
    .house-SUNDARJI {{ background: #0047AB !important; color: #ffffff !important; }}
    .house-VAIDYA {{ background: #FFC300 !important; color: #111111 !important; }}
    .tally-num {{ font-size: 16px; font-weight: 900; color: #0f172a; }}
    .gold-text {{ color: #d97706 !important; }}
    .silver-text {{ color: #64748b !important; }}
    .bronze-text {{ color: #c2410c !important; }}
    .total-col {{ color: #0284c7; }}
    .pp-col {{ color: #64748b; }}
    .tp-col {{ background: #002244; color: #ffdd00 !important; border-radius: 5px; padding: 3px 2px; display: inline-block; }}
    .winner-scroll-box {{ height: 520px; overflow: hidden; position: relative; background: #f8fafc; padding: 8px; }}
    .scroll-inner {{ {anim_css} }}
    .scroll-inner:hover {{ animation-play-state: paused; }}
    @keyframes scrollUp {{ 0% {{ transform: translateY(0); }} 100% {{ transform: translateY(-50%); }} }}
    .event-doc-card {{ background: #ffffff; border: 2px solid #cbd5e1; border-radius: 8px; margin-bottom: 12px; overflow: hidden; box-shadow: 0 2px 6px rgba(0,0,0,0.05); }}
    .doc-card-header {{ background: #002D62; color: #ffffff; padding: 7px 12px; display: flex; align-items: center; justify-content: space-between; font-weight: 800; font-size: 14.5px; }}
    .doc-badge-event {{ font-size: 15.5px; color: #ffdd00; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 900; }}
    .doc-badge-cat {{ background: rgba(255, 255, 255, 0.22); padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 700; color: #fff; }}
    .doc-date-badge {{ font-size: 12px; color: #cbd5e1; font-weight: 700; }}
    .doc-sub-table {{ width: 100%; border-collapse: collapse; text-align: center; font-size: 13px; }}
    .doc-sub-table th {{ background: #e2e8f0; color: #0f172a; padding: 5px 3px; font-weight: 800; border-bottom: 2px solid #cbd5e1; }}
    .doc-sub-table td {{ padding: 6px 3px; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #334155; }}
    .compact-name {{ font-weight: 900 !important; color: #0f172a !important; text-align: left; padding-left: 6px !important; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 125px; }}
    .perf-text {{ font-weight: 800; color: #b91c1c; font-family: monospace; font-size: 12.5px; }}
    .bold-pts {{ font-weight: 900; color: #008000; }}
    .place-badge {{ font-weight: 900; border-radius: 4px; }}
    .gold-bg {{ background: #fef08a; color: #854d0e; }}
    .silver-bg {{ background: #f1f5f9; color: #475569; }}
    .bronze-bg {{ background: #fed7aa; color: #9a3412; }}
    .mini-house-badge {{ display: inline-block; padding: 2px 5px; border-radius: 4px; font-size: 10.5px; font-weight: 800; letter-spacing: 0.3px; color: #fff; }}
</style>
</head>
<body>
    <div class="top-banner">
        <div class="banner-left"><div style="font-size: 28px;">🏆</div></div>
        <div class="banner-center">
            <div class="title">ANNUAL ATHLETICS CHAMPIONSHIP 2026</div>
            <div class="school-name">ARMY PUBLIC SCHOOL, MEERUT CANTT</div>
            <div class="date-bracket">(28th October – 5th November 2026)</div>
        </div>
        <div class="clock-badge">
            <div class="clock-date" id="liveDate">28 Oct 2026</div>
            <div class="clock-time" id="liveTime">00:00:00</div>
        </div>
    </div>
    <div class="top-ticker" id="tickerBox">
        <div id="tickerWrapper">
            📢 <b>CHAMPIONSHIP UPDATES:</b> {today_events} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 🏃 Standings updated live!
        </div>
    </div>
    <div class="dashboard-grid">
        <div class="main-panel">
            <div class="panel-top-header">
                <span style="font-size:20px;">🏅</span>
                <div>
                    <div class="panel-top-title">MEDAL & POINTS TALLY</div>
                    <div class="panel-top-sub">Rankings By Total Points (TP = PP + G:5, S:4, B:3)</div>
                </div>
            </div>
            <div class="tally-container">
                <div class="medal-icon-row">
                    <div style="font-size:11.5px; color:#64748b;">POS</div>
                    <div style="text-align:center;">HOUSE</div>
                    <div class="medal-header-col"><div class="medal-coin coin-gold">1</div><div>G</div></div>
                    <div class="medal-header-col"><div class="medal-coin coin-silver">2</div><div>S</div></div>
                    <div class="medal-header-col"><div class="medal-coin coin-bronze">3</div><div>B</div></div>
                    <div style="padding-bottom:5px;">MED</div>
                    <div style="padding-bottom:5px;">PP</div>
                    <div style="padding-bottom:5px; color:#d97706;">TP</div>
                </div>
                {tally_html}
                <div style="text-align: center; margin-top: 12px; padding: 6px; background: #e0f2fe; border-radius: 6px; border: 1.5px dashed #0284c7;">
                    <span style="font-weight: 800; color: #0369a1; font-size: 13px;">🏆 More than medals...</span><br>
                    <span style="font-size: 11.5px; font-weight: 600; color: #0284c7;">Effort, teamwork and excellence!</span>
                </div>
            </div>
        </div>
        <div class="main-panel">
            <div class="panel-top-header">
                <span style="font-size:20px;">🏃</span>
                <div>
                    <div class="panel-top-title">FINAL RESULTS (EVENT-WISE)</div>
                    <div class="panel-top-sub">Official Result Sheet (28th October – 5th November 2026)</div>
                </div>
            </div>
            <div class="winner-scroll-box">
                <div class="scroll-inner">{scroll_content}</div>
            </div>
        </div>
    </div>
    <script>
        function updateClock() {{
            const now = new Date();
            const optionsDate = {{ day: '2-digit', month: 'short', year: 'numeric' }};
            document.getElementById('liveDate').textContent = now.toLocaleDateString('en-GB', optionsDate);
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            const seconds = String(now.getSeconds()).padStart(2, '0');
            document.getElementById('liveTime').textContent = hours + ':' + minutes + ':' + seconds;
        }}
        setInterval(updateClock, 1000);
        updateClock();

        const tickerBox = document.getElementById('tickerBox');
        const tickerWrapper = document.getElementById('tickerWrapper');
        let pos = tickerBox.offsetWidth;
        const velocity = {marquee_velocity};
        let lastTime = performance.now();

        function moveTicker(now) {{
            const dt = (now - lastTime) / 1000;
            lastTime = now;
            pos -= velocity * dt;
            if (pos < -tickerWrapper.offsetWidth) {{ pos = tickerBox.offsetWidth; }}
            tickerWrapper.style.transform = 'translateX(' + pos + 'px)';
            requestAnimationFrame(moveTicker);
        }}
        requestAnimationFrame(moveTicker);
    </script>
</body>
</html>
"""
    components.html(full_html, height=720, scrolling=False)

# ----------------- Session Routing -----------------
if "view_mode" not in st.session_state:
    st.session_state.view_mode = st.query_params.get("view", "login")

# =========================================================================
# 1. LOGIN & ROLE SELECTOR SCREEN
# =========================================================================
if st.session_state.view_mode == "login":
    bg_base64 = get_base64_image("final-image-green-2.png")
    
    bg_css = f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, rgba(2, 20, 45, 0.72), rgba(0, 10, 25, 0.78)), 
                    url("data:image/png;base64,{bg_base64}") no-repeat center center fixed !important;
        background-size: cover !important;
    }}
    header[data-testid="stHeader"] {{
        display: none !important;
    }}

    .main .block-container {{
        max-width: 540px !important;
        margin: 5vh auto auto auto !important;
        background: rgba(3, 20, 48, 0.90) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border-radius: 20px !important;
        padding: 34px 28px !important;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.65) !important;
        border: 2px solid rgba(255, 215, 0, 0.45) !important;
    }}

    .login-badge {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 72px;
        height: 72px;
        background: radial-gradient(circle, #023e8a, #001833);
        border-radius: 50%;
        font-size: 36px;
        margin-bottom: 12px;
        border: 3px solid #ffcc00;
        box-shadow: 0 0 22px rgba(255, 204, 0, 0.45);
    }}

    .landing-title {{
        text-align: center;
        color: #ffffff !important;
        font-size: 24px !important;
        font-weight: 900 !important;
        letter-spacing: 1.5px !important;
        line-height: 1.25 !important;
        margin: 0 !important;
        text-transform: uppercase;
        text-shadow: 0 3px 8px rgba(0, 0, 0, 0.8);
    }}
    .landing-sub {{
        text-align: center;
        color: #ffdd00 !important;
        font-size: 19px !important;
        font-weight: 900 !important;
        letter-spacing: 1.5px !important;
        margin-top: 8px !important;
        margin-bottom: 4px !important;
        text-transform: uppercase;
        text-shadow: 0 2px 6px rgba(0, 0, 0, 0.8);
    }}
    .landing-dates {{
        text-align: center;
        color: #93c5fd !important;
        font-size: 14.5px !important;
        font-weight: 800 !important;
        letter-spacing: 1.5px !important;
        margin-bottom: 22px !important;
        text-transform: uppercase;
    }}

    div[data-testid="stRadio"] > label {{
        font-size: 15px !important;
        font-weight: 800 !important;
        color: #ffffff !important;
        letter-spacing: 1px !important;
        margin-bottom: 8px !important;
        text-transform: uppercase;
    }}
    div[data-testid="stRadio"] div[role="radiogroup"] {{
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        padding: 8px 14px;
        gap: 8px;
    }}
    div[data-testid="stRadio"] label[data-baseweb="radio"] {{
        color: #f8fafc !important;
        font-weight: 700 !important;
        font-size: 16px !important;
    }}
    div[data-testid="stRadio"] label[data-baseweb="radio"] * {{
        color: #ffffff !important;
        font-size: 15px !important;
    }}

    div[data-testid="stButton"] {{
        display: flex;
        justify-content: center;
    }}
    div[data-testid="stButton"] button[kind="primary"] {{
        max-width: 320px !important;
        width: 100% !important;
        background: linear-gradient(135deg, #d90429 0%, #9b0018 100%) !important;
        color: #ffffff !important;
        font-size: 17px !important;
        font-weight: 800 !important;
        letter-spacing: 0.8px !important;
        padding: 12px 24px !important;
        border-radius: 12px !important;
        border: 1.5px solid #ff4d6d !important;
        box-shadow: 0 8px 24px rgba(217, 4, 41, 0.45) !important;
        transition: all 0.2s ease-in-out !important;
    }}
    div[data-testid="stButton"] button[kind="primary"]:hover {{
        background: linear-gradient(135deg, #ef233c 0%, #b8001f 100%) !important;
        box-shadow: 0 10px 28px rgba(217, 4, 41, 0.65) !important;
        transform: translateY(-2px);
    }}

    div[data-testid="stTextInput"] input {{
        background: #ffffff !important;
        color: #000000 !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        padding: 10px 14px !important;
    }}
    div[data-testid="stForm"] button[kind="primary"] {{
        max-width: 320px !important;
        width: 100% !important;
        margin: 10px auto 0 auto !important;
        display: block !important;
        background: linear-gradient(135deg, #0077b6 0%, #023e8a 100%) !important;
        color: #ffffff !important;
        font-size: 16px !important;
        font-weight: 800 !important;
        border-radius: 12px !important;
        border: 1px solid #90e0ef !important;
    }}
    </style>
    """
    st.markdown(bg_css, unsafe_allow_html=True)

    st.markdown("""
        <div style="text-align: center;">
            <div class="login-badge">🏆</div>
            <div class="landing-title">ANNUAL ATHLETICS CHAMPIONSHIP 2026</div>
            <div class="landing-sub">ARMY PUBLIC SCHOOL, MEERUT CANTT</div>
            <div class="landing-dates">(28th October – 5th November 2026)</div>
        </div>
    """, unsafe_allow_html=True)

    role = st.radio("Choose Access Mode:", ["📺 Open Public / IFP Display", "🔒 Score In-Charge Login"])

    if role == "📺 Open Public / IFP Display":
        st.write("")
        col_l, col_btn, col_r = st.columns([1, 4, 1])
        with col_btn:
            if st.button("🚀 Launch Live Scoreboard", type="primary", use_container_width=True):
                st.session_state.view_mode = "display"
                st.query_params["view"] = "display"
                st.rerun()
    else:
        st.write("")
        with st.form("login_form"):
            u_name = st.text_input("Username", placeholder="Enter in-charge username")
            p_word = st.text_input("Password", type="password", placeholder="Enter password")
            st.write("")
            submitted = st.form_submit_button("🔓 Access In-Charge Portal", type="primary", use_container_width=True)
            if submitted:
                if u_name == ADMIN_USER and p_word == ADMIN_PASS:
                    st.session_state.view_mode = "admin"
                    st.query_params["view"] = "admin"
                    st.success("Authenticated!")
                    st.rerun()
                else:
                    st.error("Invalid Username or Password.")

# =========================================================================
# 2. SCORE IN-CHARGE PORTAL
# =========================================================================
elif st.session_state.view_mode == "admin":
    top_c1, top_c2, top_c3 = st.columns([6, 2, 2])
    top_c1.title("📝 Score In-Charge Portal")
    if top_c2.button("🖥️ Open Live Board"):
        st.session_state.view_mode = "display"
        st.query_params["view"] = "display"
        st.rerun()
    if top_c3.button("🚪 Logout"):
        export_static_board()
        st.session_state.view_mode = "login"
        st.query_params.clear()
        st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs([
        "➕ Add Event Result", 
        "⭐ Participation Points (PP)",
        "📢 Marquee Broadcast", 
        "📋 Record Manager (Full Database & Bulk Delete)"
    ])

    category_list = ["Jr. Boys", "Jr. Girls", "Sr. Boys", "Sr. Girls"]
    classes_list = ["VI", "VII", "VIII", "IX", "X", "XI", "XII"]
    sections_list = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M"]

    events_by_category = {
        "Jr. Boys": [
            "100M", "200M", "400M", "4X100M RELAY", 
            "LONG JUMP", "HIGH JUMP", "SHOT PUT", "CROSS COUNTRY"
        ],
        "Jr. Girls": [
            "100M", "200M", "400M", "4X100M RELAY", 
            "LONG JUMP", "HIGH JUMP", "SHOT PUT", "CROSS COUNTRY"
        ],
        "Sr. Boys": [
            "100M", "200M", "400M", "800M", "4X100M RELAY", 
            "LONG JUMP", "HIGH JUMP", "SHOT PUT", "DISCUS", "JAVELIN", "CROSS COUNTRY"
        ],
        "Sr. Girls": [
            "100M", "200M", "400M", "800M", "4X100M RELAY", 
            "LONG JUMP", "HIGH JUMP", "SHOT PUT", "DISCUS", "CROSS COUNTRY"
        ]
    }

    # --- TAB 1: Add Event Result ---
    with tab1:
        st.subheader("Record Event Winners")
        
        m1, m2, m3 = st.columns([1.5, 2.5, 2.0])
        e_date = m1.date_input("Event Date", date.today())
        e_cat = m2.selectbox("Category", category_list, key="selected_cat")
        e_name = m3.selectbox("Event Name", events_by_category[e_cat], key="selected_event")

        with st.form("compact_score_entry", clear_on_submit=True):
            st.write("---")
            # 🥇 GOLD
            st.markdown("##### 🥇 1st Place (Gold: 5 Pts)")
            g1, g2, g3, g4, g5, g6, g7 = st.columns([2.2, 0.9, 0.9, 1.4, 1.5, 1.5, 0.8])
            g_name = g1.text_input("Student Name *", key="g_name")
            g_cls_val = g2.selectbox("Class", classes_list, index=2, key="g_cls")
            g_sec_val = g3.selectbox("Sec", sections_list, index=0, key="g_sec")
            g_adm = g4.text_input("Adm. No", placeholder="V-30394", key="g_adm")
            g_perf = g5.text_input("Ti/Ht/Dis", placeholder="12:12:34", key="g_perf")
            g_h = g6.selectbox("House", houses, index=0, key="g_h")
            g_pts = g7.number_input("Pts", min_value=0, value=5, key="g_pts")

            st.write("---")
            # 🥈 SILVER
            st.markdown("##### 🥈 2nd Place (Silver: 4 Pts)")
            s1, s2, s3, s4, s5, s6, s7 = st.columns([2.2, 0.9, 0.9, 1.4, 1.5, 1.5, 0.8])
            silv_name = s1.text_input("Student Name", key="s_name")
            s_cls_val = s2.selectbox("Class", classes_list, index=2, key="s_cls")
            s_sec_val = s3.selectbox("Sec", sections_list, index=1, key="s_sec")
            silv_adm = s4.text_input("Adm. No", placeholder="M-22426", key="s_adm")
            silv_perf = s5.text_input("Ti/Ht/Dis", placeholder="12:13:28", key="s_perf")
            silv_h = s6.selectbox("House", houses, index=1, key="s_h")
            silv_pts = s7.number_input("Pts", min_value=0, value=4, key="s_pts")

            st.write("---")
            # 🥉 BRONZE
            st.markdown("##### 🥉 3rd Place (Bronze: 3 Pts)")
            b1, b2, b3, b4, b5, b6, b7 = st.columns([2.2, 0.9, 0.9, 1.4, 1.5, 1.5, 0.8])
            bron_name = b1.text_input("Student Name", key="b_name")
            b_cls_val = b2.selectbox("Class", classes_list, index=2, key="b_cls")
            b_sec_val = b3.selectbox("Sec", sections_list, index=2, key="b_sec")
            bron_adm = b4.text_input("Adm. No", placeholder="M-30351", key="b_adm")
            bron_perf = b5.text_input("Ti/Ht/Dis", placeholder="12:14:06", key="b_perf")
            bron_h = b6.selectbox("House", houses, index=2, key="b_h")
            bron_pts = b7.number_input("Pts", min_value=0, value=3, key="b_pts")

            st.write("")
            if st.form_submit_button("💾 Save Event Result & Update Scoreboard", type="primary", use_container_width=True):
                if g_name.strip():
                    final_g_cls = f"{g_cls_val} {g_sec_val}"
                    final_s_cls = f"{s_cls_val} {s_sec_val}" if silv_name.strip() else ""
                    final_b_cls = f"{b_cls_val} {b_sec_val}" if bron_name.strip() else ""

                    conn = get_connection()
                    conn.execute('''
                        INSERT INTO results (
                            event_date, event_name, category,
                            gold_student, gold_class, gold_adm, gold_perf, gold_house, gold_pts,
                            silver_student, silver_class, silver_adm, silver_perf, silver_house, silver_pts,
                            bronze_student, bronze_class, bronze_adm, bronze_perf, bronze_house, bronze_pts
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        str(e_date), e_name, e_cat,
                        g_name.strip(), final_g_cls, g_adm.strip(), g_perf.strip(), g_h, g_pts,
                        silv_name.strip(), final_s_cls, silv_adm.strip(), silv_perf.strip(), silv_h, silv_pts,
                        bron_name.strip(), final_b_cls, bron_adm.strip(), bron_perf.strip(), bron_h, bron_pts
                    ))
                    conn.commit()
                    conn.close()
                    export_static_board()
                    st.success(f"Result for {e_name} ({e_cat}) saved successfully!")
                    st.rerun()
                else:
                    st.error("Please enter at least the 1st Place Winner Name.")

    # --- TAB 2: Participation Points (PP) ---
    with tab2:
        st.subheader("⭐ House Participation Points (PP)")
        st.info("Participation points are default 0. Fill or adjust these at the conclusion of all events.")
        conn = get_connection()
        pp_df = pd.read_sql_query("SELECT house_code, pp_points FROM house_points", conn)
        conn.close()

        current_pp = {normalize_house(r['house_code']): r['pp_points'] for _, r in pp_df.iterrows()}

        with st.form("pp_form"):
            c_c, c_m, c_s, c_v = st.columns(4)
            new_c = c_c.number_input("CARIAPPA PP", min_value=0, value=int(current_pp.get("CARIAPPA", 0)))
            new_m = c_m.number_input("MANEKSHAW PP", min_value=0, value=int(current_pp.get("MANEKSHAW", 0)))
            new_s = c_s.number_input("SUNDARJI PP", min_value=0, value=int(current_pp.get("SUNDARJI", 0)))
            new_v = c_v.number_input("VAIDYA PP", min_value=0, value=int(current_pp.get("VAIDYA", 0)))

            if st.form_submit_button("Update Participation Points", type="primary"):
                conn = get_connection()
                c = conn.cursor()
                for h_code, pts in [("CARIAPPA", new_c), ("MANEKSHAW", new_m), ("SUNDARJI", new_s), ("VAIDYA", new_v)]:
                    c.execute("INSERT OR REPLACE INTO house_points (house_code, pp_points) VALUES (?, ?)", (h_code, pts))
                conn.commit()
                conn.close()
                export_static_board()
                st.success("House Participation Points (PP) updated successfully!")
                st.rerun()

    # --- TAB 3: Ticker Announcements ---
    with tab3:
        st.subheader("📢 Send Live Announcement to Marquee")
        with st.form("broadcast_form", clear_on_submit=True):
            tick_msg = st.text_input("Announcement Message", placeholder="e.g. 400M Sr. Boys starting shortly on Track 1!")
            if st.form_submit_button("Broadcast to Marquee"):
                if tick_msg.strip():
                    conn = get_connection()
                    conn.execute("INSERT INTO announcements (event_date, announcement) VALUES (?, ?)", (str(date.today()), tick_msg.strip()))
                    conn.commit()
                    conn.close()
                    export_static_board()
                    st.success("Broadcasted!")
                    st.rerun()

        st.write("---")
        st.subheader("Manage Active Announcements")
        conn = get_connection()
        ann_df = pd.read_sql_query("SELECT id, event_date, announcement FROM announcements ORDER BY id DESC", conn)
        conn.close()

        if not ann_df.empty:
            for _, arow in ann_df.iterrows():
                ac1, ac2 = st.columns([8, 2])
                ac1.write(f"[{arow['event_date']}] {arow['announcement']}")
                if ac2.button("🗑️ Delete", key=f"del_ann_{arow['id']}"):
                    conn = get_connection()
                    conn.execute("DELETE FROM announcements WHERE id = ?", (int(arow['id']),))
                    conn.commit()
                    conn.close()
                    export_static_board()
                    st.rerun()
        else:
            st.caption("No announcements currently in ticker.")

    # --- TAB 4: Full Database Record Manager & Bulk Deletion ---
    with tab4:
        st.subheader("📋 Championship Master Database (All Days)")
        conn = get_connection()
        records_df = pd.read_sql_query("SELECT * FROM results ORDER BY id DESC", conn)
        conn.close()

        if records_df.empty:
            st.warning("No records found in database. Results entered from any day will persist here.")
        else:
            st.markdown(f"**Total Records:** `{len(records_df)}` events recorded.")
            
            with st.expander("🗑️ Bulk Delete Records (Select Multiple)", expanded=False):
                st.write("Select records to permanently remove from the database:")
                selected_del_ids = []
                for _, r in records_df.iterrows():
                    chk = st.checkbox(
                        f"ID {r['id']} | {r['event_date']} - {r['event_name']} ({r['category']}) | 🥇 {r['gold_student']} ({r['gold_house']})",
                        key=f"bulk_chk_{r['id']}"
                    )
                    if chk:
                        selected_del_ids.append(int(r['id']))

                if selected_del_ids:
                    if st.button(f"🚨 Delete Selected ({len(selected_del_ids)}) Records Now", type="primary"):
                        conn = get_connection()
                        c = conn.cursor()
                        placeholders = ",".join("?" * len(selected_del_ids))
                        c.execute(f"DELETE FROM results WHERE id IN ({placeholders})", selected_del_ids)
                        conn.commit()
                        conn.close()
                        export_static_board()
                        st.success(f"Deleted {len(selected_del_ids)} records!")
                        st.rerun()

            st.write("---")
            st.markdown("##### ✏️ Direct In-Table Editor")
            records_df["event_date"] = pd.to_datetime(records_df["event_date"]).dt.date
            edited_df = st.data_editor(
                records_df,
                num_rows="dynamic",
                disabled=["id"],
                use_container_width=True,
                hide_index=True,
                key="doc_format_editor"
            )

            if st.button("💾 Apply In-Table Changes to Database", type="primary"):
                original_ids = set(records_df["id"].tolist())
                current_ids = set(edited_df["id"].dropna().astype(int).tolist())

                conn = get_connection()
                c = conn.cursor()

                for del_id in (original_ids - current_ids):
                    c.execute("DELETE FROM results WHERE id = ?", (int(del_id),))

                for _, row in edited_df.iterrows():
                    if pd.notna(row["id"]):
                        c.execute("""
                            UPDATE results SET
                                event_date=?, event_name=?, category=?,
                                gold_student=?, gold_class=?, gold_adm=?, gold_perf=?, gold_house=?, gold_pts=?,
                                silver_student=?, silver_class=?, silver_adm=?, silver_perf=?, silver_house=?, silver_pts=?,
                                bronze_student=?, bronze_class=?, bronze_adm=?, bronze_perf=?, bronze_house=?, bronze_pts=?
                            WHERE id=?
                        """, (
                            str(row["event_date"]), str(row["event_name"]), str(row["category"]),
                            str(row["gold_student"]), str(row["gold_class"]), str(row["gold_adm"]), str(row["gold_perf"]), normalize_house(row["gold_house"]), int(row["gold_pts"]),
                            str(row["silver_student"]), str(row["silver_class"]), str(row["silver_adm"]), str(row["silver_perf"]), normalize_house(row["silver_house"]), int(row["silver_pts"]),
                            str(row["bronze_student"]), str(row["bronze_class"]), str(row["bronze_adm"]), str(row["bronze_perf"]), normalize_house(row["bronze_house"]), int(row["bronze_pts"]),
                            int(row["id"])
                        ))

                conn.commit()
                conn.close()
                export_static_board()
                st.success("Database updated successfully!")
                st.rerun()

# =========================================================================
# 3. LIVE FULL-SCREEN DISPLAY BOARD (OBS / YOUTUBE / IFP OPTIMIZED)
# =========================================================================
elif st.session_state.view_mode == "display":
    with st.sidebar:
        if st.button("⬅️ Switch to In-Charge Login"):
            st.session_state.view_mode = "login"
            st.query_params["view"] = "login"
            st.rerun()
        
        st.markdown("### 🎛️ Live Display Controls")
        scroll_speed = st.slider("Winners Auto-Scroll Speed (seconds)", min_value=0, max_value=180, value=75, step=5,
                                 help="Higher value = slower scrolling. 0 = stop scroll.")
        
        st.markdown("---")
        st.markdown("### 📢 Marquee Ticker Controls")
        marquee_velocity = st.slider(
            "Marquee Speed (Pixels / Sec)", 
            min_value=25, 
            max_value=250, 
            value=80, 
            step=5,
            help="Smooth speed control. Speed remains constant even if text is added or deleted."
        )
        marquee_font_size = st.slider("Marquee Font Size (px)", min_value=14, max_value=32, value=19, step=1)
        marquee_bg_color = st.color_picker("Marquee Background Color", "#002244")
        marquee_text_color = st.color_picker("Marquee Text Color", "#FFDD00")

    st.markdown("""
        <style>
        .block-container {
            padding: 0rem !important;
            max-width: 100% !important;
        }
        header[data-testid="stHeader"] {
            display: none;
        }
        </style>
    """, unsafe_allow_html=True)

    # Calling module-level fragment with stable ID
    render_live_screen(scroll_speed, marquee_velocity, marquee_font_size, marquee_bg_color, marquee_text_color)
