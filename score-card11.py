import base64
from datetime import datetime, date
import os
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ----------------- App Configuration -----------------
st.set_page_config(
    page_title="ANNUAL ATHLETICS CHAMPIONSHIP 2026",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ----------------- Helper: Base64 Background Encoder -----------------
def get_base64_image(image_path):
  if os.path.exists(image_path):
    with open(image_path, "rb") as img_file:
      return base64.b64encode(img_file.read()).decode()
  return ""


# ----------------- Google Sheets Live Endpoints -----------------
SPREADSHEET_ID = "1SvVfpeE99a5KqPGxMjD_tQVYoMd-YUUT4ZGhelNE_FE"
RESULTS_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&sheet=Results"
PP_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&sheet=House_Points"
CREDS_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&sheet=Credentials"
ANNOUNCE_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&sheet=Announcements"


def fetch_live_data():
  try:
    results_df = pd.read_csv(RESULTS_CSV_URL)
    results_df.columns = [
        c.strip().lower().replace(" ", "_").replace("/", "_").replace(".", "")
        for c in results_df.columns
    ]
  except Exception:
    results_df = pd.DataFrame()

  try:
    pp_df = pd.read_csv(PP_CSV_URL)
    pp_df.columns = [c.strip().lower() for c in pp_df.columns]
  except Exception:
    pp_df = pd.DataFrame(columns=["house", "pp_points"])

  try:
    announce_df = pd.read_csv(ANNOUNCE_CSV_URL)
    announce_df.columns = [c.strip().lower() for c in announce_df.columns]
  except Exception:
    announce_df = pd.DataFrame()

  return results_df, pp_df, announce_df


def fetch_credentials():
  try:
    creds_df = pd.read_csv(CREDS_CSV_URL)
    creds_df.columns = [c.strip().lower() for c in creds_df.columns]
    # Return dictionary of username: password
    return dict(zip(creds_df["username"].astype(str), creds_df["password"].astype(str)))
  except Exception:
    return {"incharge1": "apspass2026", "incharge2": "apspass2026"}


# ----------------- Canonical House Definitions -----------------
houses = ["CARIAPPA", "MANEKSHAW", "SUNDARJI", "VAIDYA"]


def normalize_house(name):
  if not name or pd.isna(name):
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


# ----------------- Session Routing -----------------
if "view_mode" not in st.session_state:
  st.session_state.view_mode = st.query_params.get("view", "login")

# =========================================================================
# 1. LOGIN & IN-CHARGE AUTHENTICATION (AUTHENTICATES FROM GOOGLE SHEET)
# =========================================================================
if st.session_state.view_mode == "login":
  bg_base64 = get_base64_image("final-image-green-2.png")

  bg_css = f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, rgba(2, 20, 45, 0.78), rgba(0, 10, 25, 0.85)), 
                    url("data:image/png;base64,{bg_base64}") no-repeat center center fixed !important;
        background-size: cover !important;
    }}
    header[data-testid="stHeader"] {{
        display: none !important;
    }}
    .main .block-container {{
        max-width: 550px !important;
        margin: 6vh auto auto auto !important;
        background: rgba(3, 20, 48, 0.95) !important;
        backdrop-filter: blur(16px) !important;
        border-radius: 20px !important;
        padding: 34px 28px !important;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.75) !important;
        border: 2px solid rgba(255, 215, 0, 0.5) !important;
    }}
    .login-badge {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 74px;
        height: 74px;
        background: radial-gradient(circle, #023e8a, #001833);
        border-radius: 50%;
        font-size: 38px;
        margin-bottom: 12px;
        border: 3px solid #ffcc00;
        box-shadow: 0 0 22px rgba(255, 204, 0, 0.5);
    }}
    .landing-title {{
        text-align: center;
        color: #ffffff !important;
        font-size: 24px !important;
        font-weight: 900 !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase;
        margin: 0 !important;
    }}
    .landing-sub {{
        text-align: center;
        color: #ffdd00 !important;
        font-size: 19px !important;
        font-weight: 900 !important;
        letter-spacing: 1.5px !important;
        margin-top: 6px !important;
        text-transform: uppercase;
    }}
    .landing-dates {{
        text-align: center;
        color: #93c5fd !important;
        font-size: 14.5px !important;
        font-weight: 800 !important;
        margin-bottom: 22px !important;
    }}
    div[data-testid="stRadio"] > label {{
        font-size: 15px !important;
        font-weight: 800 !important;
        color: #ffffff !important;
        letter-spacing: 1px !important;
    }}
    div[data-testid="stRadio"] div[role="radiogroup"] {{
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.25);
        border-radius: 12px;
        padding: 8px 14px;
    }}
    div[data-testid="stButton"] button[kind="primary"] {{
        background: linear-gradient(135deg, #d90429 0%, #9b0018 100%) !important;
        color: #ffffff !important;
        font-size: 17px !important;
        font-weight: 800 !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
    }}
    </style>
    """
  st.markdown(bg_css, unsafe_allow_html=True)

  st.markdown(
      """
        <div style="text-align: center;">
            <div class="login-badge">🏆</div>
            <div class="landing-title">ANNUAL ATHLETICS CHAMPIONSHIP 2026</div>
            <div class="landing-sub">ARMY PUBLIC SCHOOL, MEERUT CANTT</div>
            <div class="landing-dates">(28th October – 5th November 2026)</div>
        </div>
    """,
      unsafe_allow_html=True,
  )

  role = st.radio(
      "Choose Access Mode:",
      ["📺 Open Public / IFP Display", "🔒 Score In-Charge Portal"],
  )

  if role == "📺 Open Public / IFP Display":
    st.write("")
    _, col_btn, _ = st.columns([1, 4, 1])
    with col_btn:
      if st.button("🚀 Launch Live Scoreboard", type="primary", use_container_width=True):
        st.session_state.view_mode = "display"
        st.query_params["view"] = "display"
        st.rerun()
  else:
    st.write("")
    with st.form("login_form"):
      st.markdown("##### 🔑 In-Charge Login (Credentials Verified via Master Sheet)")
      u_name = st.text_input("Username", placeholder="e.g. incharge1 or incharge2").strip()
      p_word = st.text_input("Password", type="password", placeholder="Enter password").strip()
      st.write("")
      submitted = st.form_submit_button("🔓 Access In-Charge Portal", type="primary", use_container_width=True)
      if submitted:
        valid_creds = fetch_credentials()
        if u_name in valid_creds and valid_creds[u_name] == p_word:
          st.session_state.view_mode = "admin"
          st.session_state.logged_user = u_name
          st.query_params["view"] = "admin"
          st.success(f"Authenticated as {u_name}!")
          st.rerun()
        else:
          st.error("Invalid Username or Password. Credentials can be verified in the 'Credentials' sheet.")

# =========================================================================
# 2. SCORE IN-CHARGE PORTAL
# =========================================================================
elif st.session_state.view_mode == "admin":
  top_c1, top_c2, top_c3 = st.columns([6, 2, 2])
  top_c1.title(f"📝 Score In-Charge Portal ({st.session_state.get('logged_user', 'Authorized')})")
  if top_c2.button("🖥️ Open Live Board"):
    st.session_state.view_mode = "display"
    st.query_params["view"] = "display"
    st.rerun()
  if top_c3.button("🚪 Logout"):
    st.session_state.view_mode = "login"
    st.session_state.pop("logged_user", None)
    st.query_params.clear()
    st.rerun()

  st.success("Authorized Session Active • Synchronized with Google Sheets Cloud Database")

  st.markdown(f"""
        ### 📊 In-Charge Controls
        1. **Direct Google Sheet Access**:
           👉 **[Click Here to Open and Edit the Google Sheet](https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit)**
        2. **Tabs Available in the Spreadsheet**:
           * **`Results`**: Add new winners, select event, category, and house from dropdowns. For relays, set class to `TEAM` and stack names using Alt+Enter.
           * **`Announcements`**: Edit the scrolling ticker text and type custom messages for the AI avatar to announce on the stadium speakers.
           * **`Credentials`**: In-charge login passwords can be updated here securely.
    """)

  st.write("---")
  st.subheader("📋 Current Master Results in Cloud Sheet")
  res_df, _, _ = fetch_live_data()
  if not res_df.empty:
    st.dataframe(res_df, use_container_width=True)
  else:
    st.warning("No data retrieved from Google Sheet. Please check sharing permissions.")

# =========================================================================
# 3. LIVE FULL-SCREEN DISPLAY BOARD (40-SEC REFRESH, AVATAR AUDIO, FLIP CLOCK & AQI)
# =========================================================================
elif st.session_state.view_mode == "display":
  with st.sidebar:
    if st.button("⬅️ Switch to In-Charge Login"):
      st.session_state.view_mode = "login"
      st.query_params["view"] = "login"
      st.rerun()

    st.markdown("### 🎛️ Live Display Controls")
    scroll_speed = st.slider(
        "Winners Auto-Scroll Speed (seconds)",
        min_value=0,
        max_value=180,
        value=75,
        step=5,
        help="Higher value = slower scrolling. 0 = stop scroll.",
    )

    st.markdown("---")
    st.markdown("### 📢 Marquee Ticker Controls")
    marquee_velocity = st.slider("Marquee Speed (Pixels / Sec)", min_value=25, max_value=250, value=85, step=5)
    marquee_font_size = st.slider("Marquee Font Size (px)", min_value=14, max_value=32, value=19, step=1)
    marquee_bg_color = st.color_picker("Marquee Background Color", "#001833")
    marquee_text_color = st.color_picker("Marquee Text Color", "#FFE600")

  st.markdown(
      """
        <style>
        .block-container {
            padding: 0rem !important;
            max-width: 100% !important;
        }
        header[data-testid="stHeader"] {
            display: none;
        }
        </style>
    """,
      unsafe_allow_html=True,
  )

  # Auto-refreshes every 40 seconds directly from Google Sheets
  @st.fragment(run_every=40)
  def render_live_screen():
    df, pp_df, ann_df = fetch_live_data()

    # Pre-process dates: Parse properly and sort descending (newest dates first)
    if not df.empty and "event_date" in df.columns:
      df["parsed_date"] = pd.to_datetime(df["event_date"], format="mixed", dayfirst=True, errors="coerce")
      df = df.sort_values(by="parsed_date", ascending=False).reset_index(drop=True)
      df["display_date"] = df["parsed_date"].dt.strftime("%d-%m-%Y")
      df["display_date"] = df["display_date"].fillna(df["event_date"])
    elif not df.empty:
      df["display_date"] = ""

    # Build clean PP Dictionary
    pp_dict = {}
    if not pp_df.empty and "house" in pp_df.columns and "pp_points" in pp_df.columns:
      for _, r in pp_df.iterrows():
        pp_dict[normalize_house(r["house"])] = int(r["pp_points"] if pd.notna(r["pp_points"]) else 0)

    tally = {
        h: {
            "Gold": 0,
            "Silver": 0,
            "Bronze": 0,
            "TotalMedals": 0,
            "PP": int(pp_dict.get(h, 0)),
            "EarnedPts": 0,
            "TP": 0,
        }
        for h in houses
    }

    if not df.empty:
      for _, r in df.iterrows():
        gh = normalize_house(r.get("gold_house", ""))
        sh = normalize_house(r.get("silver_house", ""))
        bh = normalize_house(r.get("bronze_house", ""))

        if gh in tally:
          tally[gh]["Gold"] += 1
          g_val = r.get("gold_points", 5)
          try:
            tally[gh]["EarnedPts"] += int(float(g_val))
          except Exception:
            tally[gh]["EarnedPts"] += 5

        if sh in tally:
          tally[sh]["Silver"] += 1
          s_val = r.get("silver_points", 4)
          try:
            tally[sh]["EarnedPts"] += int(float(s_val))
          except Exception:
            tally[sh]["EarnedPts"] += 4

        if bh in tally:
          tally[bh]["Bronze"] += 1
          b_val = r.get("bronze_points", 3)
          try:
            tally[bh]["EarnedPts"] += int(float(b_val))
          except Exception:
            tally[bh]["EarnedPts"] += 3

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
            tally[h]["TotalMedals"],
        ),
        reverse=True,
    )

    tally_html = ""
    for rank, h in enumerate(sorted_houses, start=1):
      rank_display = "👑 1" if rank == 1 else f"#{rank}"
      tally_html += f"""
            <div class="house-tally-row">
                <div style="font-weight:900; font-size:15px; color:#1e293b;">{rank_display}</div>
                <div><span class="house-box-label house-{h}">{h}</span></div>
                <div class="tally-num gold-text">{tally[h]['Gold']}</div>
                <div class="tally-num silver-text">{tally[h]['Silver']}</div>
                <div class="tally-num bronze-text">{tally[h]['Bronze']}</div>
                <div class="tally-num total-col">{tally[h]['TotalMedals']}</div>
                <div class="tally-num pp-col">{tally[h]['PP']}</div>
                <div class="tally-num tp-col">{tally[h]['TP']}</div>
            </div>
            """

    # Fetch Dynamic Marquee & Custom Avatar Speech from Sheet
    marquee_msg = "🏆 ANNUAL ATHLETICS CHAMPIONSHIP 2026 IS LIVE! Results and House Points updated directly from official records."
    avatar_custom_msg = ""
    if not ann_df.empty and "type" in ann_df.columns and "content" in ann_df.columns:
      m_row = ann_df[ann_df["type"].str.lower() == "marquee"]
      if not m_row.empty:
        marquee_msg = str(m_row.iloc[0]["content"])
      a_row = ann_df[ann_df["type"].str.lower() == "avatar_custom"]
      if not a_row.empty:
        avatar_custom_msg = str(a_row.iloc[0]["content"])

    # Build Avatar Speech with Appreciation and Weather Context
    speech_text = ""
    if not df.empty:
      top_e = df.iloc[0]
      g_first_name = str(top_e.get("gold_student_name", "")).split("\n")[0].split(",")[0].strip()
      speech_text = (
          f"Attention athletes and supporters! Breaking news from the track: Heartiest congratulations to {g_first_name} "
          f"from {normalize_house(top_e.get('gold_house', ''))} House for securing the Gold medal in {top_e.get('event_name', '')} "
          f"for {top_e.get('category', '')} with a stellar mark of {top_e.get('gold_perf_(time_ht_dis)', '')}! "
          f"Outstanding dedication and sportsmanship shown by all competitors! "
      )
    if avatar_custom_msg and len(avatar_custom_msg.strip()) > 5:
      speech_text += f" Special Announcement: {avatar_custom_msg}. "
    speech_text += "Weather in Meerut Cantt is ideal for athletics. Keep the spirit high!"

    cards_html = ""
    if df.empty:
      cards_html = """
            <div style="text-align:center; padding: 60px 20px; color:#1e293b; font-weight:900; font-size:20px;">
                🏆 Events are underway! Results will appear here as soon as verified in Google Sheets.
            </div>
            """
    else:
      for idx, r in df.iterrows():
        gh = normalize_house(r.get("gold_house", ""))
        sh = normalize_house(r.get("silver_house", ""))
        bh = normalize_house(r.get("bronze_house", ""))

        def format_stacked(val):
          if pd.isna(val) or not str(val).strip():
            return "-"
          return str(val).replace("\n", "<br>")

        g_name_html = format_stacked(r.get("gold_student_name", ""))
        s_name_html = format_stacked(r.get("silver_student_name", ""))
        b_name_html = format_stacked(r.get("bronze_student_name", ""))

        g_adm_html = format_stacked(r.get("gold_adm_no", ""))
        s_adm_html = format_stacked(r.get("silver_adm_no", ""))
        b_adm_html = format_stacked(r.get("bronze_adm_no", ""))

        g_pts_disp = r.get("gold_points", 5)
        s_pts_disp = r.get("silver_points", 4)
        b_pts_disp = r.get("bronze_points", 3)

        cards_html += f"""
                <div class="event-doc-card">
                    <div class="doc-card-header">
                        <span class="doc-badge-event">{r.get('event_name', '')}</span>
                        <span class="doc-badge-cat">{r.get('category', '')}</span>
                        <span class="doc-date-badge">📅 {r.get('display_date', '')}</span>
                    </div>
                    <table class="doc-sub-table">
                        <thead>
                            <tr>
                                <th style="width:8%;">Place</th>
                                <th style="width:25%;">Team / Athlete</th>
                                <th style="width:12%;">Class/Sec</th>
                                <th style="width:17%;">Adm. No.</th>
                                <th style="width:14%;">Ti/Ht/Dis</th>
                                <th style="width:15%;">House</th>
                                <th style="width:9%;">Pts</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr class="row-gold">
                                <td class="place-badge gold-bg">1st 🥇</td>
                                <td class="daylight-name">{g_name_html}</td>
                                <td class="daylight-bold-class">{r.get('gold_class_sec', '-')}</td>
                                <td class="daylight-bold-adm">{g_adm_html}</td>
                                <td class="daylight-bold-perf">{r.get('gold_perf_(time_ht_dis)', '-')}</td>
                                <td><span class="mini-house-badge house-{gh}">{gh}</span></td>
                                <td class="bold-pts">+{g_pts_disp}</td>
                            </tr>
                            <tr class="row-silver">
                                <td class="place-badge silver-bg">2nd 🥈</td>
                                <td class="daylight-name">{s_name_html}</td>
                                <td class="daylight-bold-class">{r.get('silver_class_sec', '-')}</td>
                                <td class="daylight-bold-adm">{s_adm_html}</td>
                                <td class="daylight-bold-perf">{r.get('silver_perf_(time_ht_dis)', '-')}</td>
                                <td><span class="mini-house-badge house-{sh}">{sh}</span></td>
                                <td class="bold-pts">+{s_pts_disp}</td>
                            </tr>
                            <tr class="row-bronze">
                                <td class="place-badge bronze-bg">3rd 🥉</td>
                                <td class="daylight-name">{b_name_html}</td>
                                <td class="daylight-bold-class">{r.get('bronze_class_sec', '-')}</td>
                                <td class="daylight-bold-adm">{b_adm_html}</td>
                                <td class="daylight-bold-perf">{r.get('bronze_perf_(time_ht_dis)', '-')}</td>
                                <td><span class="mini-house-badge house-{bh}">{bh}</span></td>
                                <td class="bold-pts">+{b_pts_disp}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                """

    if scroll_speed > 0 and len(df) > 0:
      anim_css = f"animation: seamlessScrollUp {scroll_speed}s linear infinite;"
      scroll_content = cards_html + cards_html
    else:
      anim_css = "animation: none; overflow-y: auto;"
      scroll_content = cards_html

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
        background-color: #cbd5e1;
        padding: 4px 10px 16px 10px;
        overflow-x: hidden;
    }}

    .top-banner {{
        background: linear-gradient(90deg, #001f3f 0%, #002b54 100%);
        color: #ffffff;
        border-radius: 8px 8px 0 0;
        padding: 10px 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 6px 16px rgba(0, 31, 63, 0.4);
        border-bottom: 3.5px solid #ffcc00;
    }}

    .avatar-widget {{
        display: flex;
        align-items: center;
        gap: 12px;
        background: rgba(0, 0, 0, 0.45);
        border: 2px solid #ffd700;
        border-radius: 10px;
        padding: 6px 12px;
        min-width: 260px;
    }}
    .avatar-circle {{
        width: 50px;
        height: 50px;
        border-radius: 50%;
        border: 2px solid #ffdd00;
        background: radial-gradient(circle, #023e8a, #001226);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 26px;
        position: relative;
    }}
    .speaking-pulse {{
        animation: pulseRing 1.2s infinite ease-in-out;
    }}
    @keyframes pulseRing {{
        0% {{ box-shadow: 0 0 0 0 rgba(255, 221, 0, 0.7); }}
        70% {{ box-shadow: 0 0 0 12px rgba(255, 221, 0, 0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(255, 221, 0, 0); }}
    }}
    .avatar-info {{
        display: flex;
        flex-direction: column;
    }}
    .avatar-title {{
        font-size: 13.5px;
        font-weight: 900;
        color: #ffdd00;
        letter-spacing: 0.5px;
    }}
    .audio-btn {{
        background: #f59e0b;
        color: #000;
        border: none;
        padding: 3px 10px;
        font-size: 11px;
        font-weight: 900;
        border-radius: 5px;
        cursor: pointer;
        margin-top: 4px;
        width: fit-content;
        transition: 0.2s;
    }}

    .banner-center {{
        text-align: center;
        flex-grow: 1;
        padding: 0 10px;
    }}
    .top-banner .title {{
        font-size: clamp(20px, 2.5vw, 30px);
        font-weight: 900;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #ffffff;
        line-height: 1.15;
        text-shadow: 0 2px 4px rgba(0,0,0,0.6);
    }}
    .top-banner .school-name {{
        font-size: clamp(15px, 1.8vw, 22px);
        font-weight: 900;
        letter-spacing: 2px;
        color: #ffd700;
        margin-top: 2px;
        text-transform: uppercase;
        text-shadow: 0 2px 4px rgba(0,0,0,0.6);
    }}
    .top-banner .date-bracket {{
        font-size: clamp(11.5px, 1.2vw, 14px);
        letter-spacing: 1.5px;
        font-weight: 800;
        color: #93c5fd;
        text-transform: uppercase;
    }}

    .banner-right {{
        display: flex;
        align-items: center;
        gap: 12px;
    }}
    .weather-aqi-card {{
        background: rgba(0, 0, 0, 0.45);
        border: 1.5px solid #38bdf8;
        border-radius: 8px;
        padding: 5px 10px;
        text-align: right;
    }}
    .weather-row {{
        font-size: 11.5px;
        font-weight: 800;
        color: #f8fafc;
    }}
    .aqi-pill {{
        display: inline-block;
        background: #ea580c;
        color: #fff;
        padding: 1px 6px;
        border-radius: 4px;
        font-weight: 900;
        font-size: 11px;
    }}

    .flip-clock {{
        display: flex;
        align-items: center;
        gap: 3px;
        background: #000000;
        border: 2px solid #ffd700;
        border-radius: 8px;
        padding: 5px 8px;
        box-shadow: inset 0 2px 6px rgba(0,0,0,0.8), 0 2px 8px rgba(0,0,0,0.4);
    }}
    .flap-card {{
        background: linear-gradient(180deg, #1c1c1e 48%, #111112 52%);
        color: #ffd700;
        font-family: 'Courier New', Courier, monospace;
        font-size: 21px;
        font-weight: 900;
        padding: 3px 6px;
        border-radius: 4px;
        border: 1px solid #333336;
        min-width: 28px;
        text-align: center;
    }}
    .flap-colon {{
        color: #ffffff;
        font-weight: 900;
        font-size: 20px;
    }}
    .flap-label {{
        font-size: 10.5px;
        color: #94a3b8;
        font-weight: 800;
        text-align: center;
        margin-top: 2px;
    }}

    .top-ticker {{
        width: 100%;
        background-color: {marquee_bg_color};
        color: {marquee_text_color};
        padding: 7px 0;
        font-size: {marquee_font_size}px;
        font-weight: 900;
        overflow: hidden;
        white-space: nowrap;
        border-bottom: 3.5px solid #f59e0b;
        border-radius: 0 0 8px 8px;
        margin-bottom: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.18);
        position: relative;
    }}
    #tickerWrapper {{
        display: inline-block;
        white-space: nowrap;
        position: relative;
    }}

    .dashboard-grid {{
        display: grid;
        grid-template-columns: 3.8fr 6.2fr;
        gap: 14px;
        width: 100%;
    }}

    @media (max-width: 1050px) {{
        .dashboard-grid {{
            grid-template-columns: 1fr;
            gap: 10px;
        }}
    }}

    .main-panel {{
        background: #ffffff;
        border: 3px solid #002244;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 6px 16px rgba(0,0,0,0.14);
    }}
    .panel-top-header {{
        background: linear-gradient(90deg, #002244 0%, #003875 100%);
        color: #ffffff;
        padding: 11px 16px;
        display: flex;
        align-items: center;
        gap: 12px;
    }}
    .panel-top-title {{
        font-size: 19px;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    .panel-top-sub {{
        font-size: 12.5px;
        font-weight: 700;
        color: #dbeafe;
    }}

    .tally-container {{
        padding: 12px 6px;
        background: #f8fafc;
    }}
    .medal-icon-row {{
        display: grid;
        grid-template-columns: 0.6fr 2.1fr 0.7fr 0.7fr 0.7fr 0.8fr 0.8fr 1.0fr;
        text-align: center;
        align-items: end;
        margin-bottom: 12px;
        font-size: 13px;
        font-weight: 900;
        color: #0f172a;
    }}
    .medal-header-col {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 2px;
    }}
    .medal-coin {{
        display: flex;
        align-items: center;
        justify-content: center;
        width: 26px;
        height: 26px;
        border-radius: 50%;
        font-weight: 900;
        font-size: 14px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.25);
    }}
    .coin-gold {{ background: radial-gradient(circle at 30% 30%, #fff6a6, #f59e0b); color: #78350f; border: 1.5px solid #d97706; }}
    .coin-silver {{ background: radial-gradient(circle at 30% 30%, #ffffff, #cbd5e1); color: #334155; border: 1.5px solid #94a3b8; }}
    .coin-bronze {{ background: radial-gradient(circle at 30% 30%, #fed7aa, #ea580c); color: #7c2d12; border: 1.5px solid #c2410c; }}

    .house-tally-row {{
        display: grid;
        grid-template-columns: 0.6fr 2.1fr 0.7fr 0.7fr 0.7fr 0.8fr 0.8fr 1.0fr;
        align-items: center;
        text-align: center;
        background: #ffffff;
        border: 2px solid #94a3b8;
        border-radius: 8px;
        margin-bottom: 9px;
        padding: 8px 2px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.06);
    }}

    .house-box-label {{
        display: inline-block;
        padding: 5px 4px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 900;
        text-align: center;
        letter-spacing: 0.6px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.25);
        width: 95%;
        text-transform: uppercase;
    }}

    .house-MANEKSHAW {{ background: #E60000 !important; color: #ffffff !important; }}
    .house-CARIAPPA {{ background: #008800 !important; color: #ffffff !important; }}
    .house-SUNDARJI {{ background: #0044CC !important; color: #ffffff !important; }}
    .house-VAIDYA {{ background: #FFB800 !important; color: #000000 !important; font-weight: 900 !important; }}

    .tally-num {{ font-size: 17px; font-weight: 900; color: #000000; }}
    .gold-text {{ color: #d97706 !important; font-size: 19px !important; }}
    .silver-text {{ color: #334155 !important; font-size: 19px !important; }}
    .bronze-text {{ color: #c2410c !important; font-size: 19px !important; }}
    .total-col {{ color: #0284c7; font-size: 19px !important; }}
    .pp-col {{ color: #334155; }}
    .tp-col {{
        background: #002244;
        color: #ffdd00 !important;
        border-radius: 6px;
        padding: 4px 4px;
        display: inline-block;
        font-size: 19px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }}

    .winner-scroll-box {{
        height: 520px;
        overflow: hidden;
        position: relative;
        background: #f1f5f9;
        padding: 10px;
    }}
    .scroll-inner {{
        display: flex;
        flex-direction: column;
        will-change: transform;
        {anim_css}
    }}
    .scroll-inner:hover {{
        animation-play-state: paused !important;
    }}
    @keyframes seamlessScrollUp {{
        0% {{ transform: translateY(0); }}
        100% {{ transform: translateY(-50%); }}
    }}

    .event-doc-card {{
        background: #ffffff;
        border: 2.5px solid #64748b;
        border-radius: 9px;
        margin-bottom: 14px;
        overflow: hidden;
        box-shadow: 0 4px 10px rgba(0,0,0,0.12);
    }}
    .doc-card-header {{
        background: #002244;
        color: #ffffff;
        padding: 9px 14px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-weight: 900;
        font-size: 15px;
    }}
    .doc-badge-event {{
        font-size: 17px;
        color: #ffd700;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 900;
    }}
    .doc-badge-cat {{
        background: #ffffff;
        color: #002244;
        padding: 3px 10px;
        border-radius: 5px;
        font-size: 13px;
        font-weight: 900;
    }}
    .doc-date-badge {{
        font-size: 13.5px;
        color: #cbd5e1;
        font-weight: 900;
        font-family: monospace;
    }}

    .doc-sub-table {{
        width: 100%;
        border-collapse: collapse;
        text-align: center;
        font-size: 14px;
    }}
    .doc-sub-table th {{
        background: #cbd5e1;
        color: #000000;
        padding: 8px 4px;
        font-weight: 900;
        border-bottom: 2px solid #94a3b8;
    }}
    .doc-sub-table td {{
        padding: 8px 4px;
        border-bottom: 1.5px solid #cbd5e1;
        vertical-align: middle;
    }}
    
    .daylight-name {{
        font-weight: 900 !important;
        color: #000000 !important;
        text-align: left;
        padding-left: 12px !important;
        line-height: 1.45;
        font-size: 14.5px;
    }}
    .daylight-bold-class {{
        font-weight: 900 !important;
        color: #000000 !important;
        font-size: 14px;
    }}
    .daylight-bold-adm {{
        font-family: monospace;
        font-weight: 900 !important;
        color: #0f172a !important;
        line-height: 1.45;
        font-size: 13.5px;
    }}
    .daylight-bold-perf {{
        font-weight: 900 !important;
        color: #b91c1c !important;
        font-family: monospace;
        font-size: 14px;
    }}
    .bold-pts {{
        font-weight: 900 !important;
        color: #008000 !important;
        font-size: 15px;
    }}
    .place-badge {{
        font-weight: 900;
        border-radius: 4px;
    }}
    .gold-bg {{ background: #fef08a; color: #854d0e; font-size: 13.5px; }}
    .silver-bg {{ background: #f1f5f9; color: #1e293b; font-size: 13.5px; }}
    .bronze-bg {{ background: #fed7aa; color: #9a3412; font-size: 13.5px; }}

    .mini-house-badge {{
        display: inline-block;
        padding: 3px 6px;
        border-radius: 4px;
        font-size: 11.5px;
        font-weight: 900;
        letter-spacing: 0.4px;
    }}
</style>
</head>
<body>

    <div class="top-banner">
        <div class="avatar-widget">
            <div class="avatar-circle" id="avatarCircle">🎙️</div>
            <div class="avatar-info">
                <span class="avatar-title">APS AI ANNOUNCER</span>
                <button class="audio-btn" id="audioToggleBtn" onclick="toggleAudioSpeech()">▶️ Enable AI Voice</button>
            </div>
        </div>

        <div class="banner-center">
            <div class="title">ANNUAL ATHLETICS CHAMPIONSHIP 2026</div>
            <div class="school-name">ARMY PUBLIC SCHOOL, MEERUT CANTT</div>
            <div class="date-bracket">(28th October – 5th November 2026)</div>
        </div>

        <div class="banner-right">
            <div class="weather-aqi-card">
                <div class="weather-row">🌤️ Meerut: <span id="meerutTemp">27°C</span> | 💧 <span id="meerutHumidity">45%</span></div>
                <div class="weather-row" style="margin-top:2px;">AQI: <span class="aqi-pill" id="meerutAQI">Moderate (138)</span></div>
            </div>
            <div>
                <div class="flip-clock">
                    <div class="flap-card" id="flipH">00</div>
                    <div class="flap-colon">:</div>
                    <div class="flap-card" id="flipM">00</div>
                    <div class="flap-colon">:</div>
                    <div class="flap-card" id="flipS">00</div>
                </div>
                <div class="flap-label" id="liveDate">29-OCT-2026</div>
            </div>
        </div>
    </div>

    <div class="top-ticker" id="tickerBox">
        <div id="tickerWrapper">
            📢 <b>CHAMPIONSHIP UPDATES:</b> {marquee_msg} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 🏃
        </div>
    </div>

    <div class="dashboard-grid">
        <div class="main-panel">
            <div class="panel-top-header">
                <span style="font-size:22px;">🏅</span>
                <div>
                    <div class="panel-top-title">MEDAL & POINTS TALLY</div>
                    <div class="panel-top-sub">Rankings By Total Points (TP = PP + G:5, S:4, B:3 | Relays: 10, 8, 6)</div>
                </div>
            </div>
            <div class="tally-container">
                <div class="medal-icon-row">
                    <div style="font-size:12px; color:#475569;">POS</div>
                    <div style="text-align:center;">HOUSE</div>
                    <div class="medal-header-col">
                        <div class="medal-coin coin-gold">1</div>
                        <div>G</div>
                    </div>
                    <div class="medal-header-col">
                        <div class="medal-coin coin-silver">2</div>
                        <div>S</div>
                    </div>
                    <div class="medal-header-col">
                        <div class="medal-coin coin-bronze">3</div>
                        <div>B</div>
                    </div>
                    <div style="padding-bottom:5px;">MED</div>
                    <div style="padding-bottom:5px;">PP</div>
                    <div style="padding-bottom:5px; color:#d97706;">TP</div>
                </div>
                {tally_html}
                <div style="text-align: center; margin-top: 14px; padding: 7px; background: #e0f2fe; border-radius: 6px; border: 1.5px dashed #0284c7;">
                    <span style="font-weight: 900; color: #0369a1; font-size: 13.5px;">🏆 More than medals...</span><br>
                    <span style="font-size: 12px; font-weight: 800; color: #0284c7;">Effort, teamwork and excellence!</span>
                </div>
            </div>
        </div>

        <div class="main-panel">
            <div class="panel-top-header">
                <span style="font-size:22px;">🏃</span>
                <div>
                    <div class="panel-top-title">FINAL RESULTS (EVENT-WISE)</div>
                    <div class="panel-top-sub">Official Results • Displayed in Descending Date Order</div>
                </div>
            </div>
            <div class="winner-scroll-box">
                <div class="scroll-inner">
                    {scroll_content}
                </div>
            </div>
        </div>
    </div>

    <script>
        // 1. AIRPORT FLIP CLOCK
        function updateFlipClock() {{
            const now = new Date();
            const h = String(now.getHours()).padStart(2, '0');
            const m = String(now.getMinutes()).padStart(2, '0');
            const s = String(now.getSeconds()).padStart(2, '0');
            
            document.getElementById('flipH').textContent = h;
            document.getElementById('flipM').textContent = m;
            document.getElementById('flipS').textContent = s;

            const opt = {{ day: '2-digit', month: 'short', year: 'numeric' }};
            document.getElementById('liveDate').textContent = now.toLocaleDateString('en-GB', opt).replace(/ /g, '-').toUpperCase();
        }}
        setInterval(updateFlipClock, 1000);
        updateFlipClock();

        // 2. MEERUT WEATHER & AQI API FETCH (Lat: 28.9845, Lon: 77.7064)
        async function fetchMeerutWeatherAQI() {{
            try {{
                const wRes = await fetch("https://api.open-meteo.com/v1/forecast?latitude=28.9845&longitude=77.7064&current=temperature_2m,relative_humidity_2m,wind_speed_10m");
                const wData = await wRes.json();
                if (wData && wData.current) {{
                    document.getElementById('meerutTemp').textContent = Math.round(wData.current.temperature_2m) + "°C";
                    document.getElementById('meerutHumidity').textContent = wData.current.relative_humidity_2m + "%";
                }}

                const aqiRes = await fetch("https://air-quality-api.open-meteo.com/v1/air-quality?latitude=28.9845&longitude=77.7064&current=european_aqi,pm2_5");
                const aqiData = await aqiRes.json();
                if (aqiData && aqiData.current) {{
                    const pm = Math.round(aqiData.current.pm2_5 || 120);
                    let label = "Moderate";
                    let bg = "#ea580c";
                    if (pm < 50) {{ label = "Good"; bg = "#16a34a"; }}
                    else if (pm > 150) {{ label = "Poor"; bg = "#dc2626"; }}
                    const pill = document.getElementById('meerutAQI');
                    pill.textContent = label + " (" + pm + ")";
                    pill.style.backgroundColor = bg;
                }}
            }} catch(e) {{
                console.log("Weather fallback active");
            }}
        }}
        fetchMeerutWeatherAQI();
        setInterval(fetchMeerutWeatherAQI, 300000);

        // 3. AI AVATAR SPEECH SYNTHESIS ENGINE
        let voiceUnlocked = localStorage.getItem('aps_voice_active') === 'true';
        const audioBtn = document.getElementById('audioToggleBtn');
        const avatarCircle = document.getElementById('avatarCircle');
        const speechPayload = "{speech_text}";

        function syncAudioButtonUI() {{
            if (voiceUnlocked) {{
                audioBtn.textContent = "🔊 Voice: Unmuted (Active)";
                audioBtn.style.background = "#22c55e";
                audioBtn.style.color = "#ffffff";
            }} else {{
                audioBtn.textContent = "▶️ Click to Enable AI Voice";
                audioBtn.style.background = "#f59e0b";
                audioBtn.style.color = "#000000";
            }}
        }}
        syncAudioButtonUI();

        function executeSpeech(text) {{
            if (!('speechSynthesis' in window)) return;
            window.speechSynthesis.cancel();

            const utter = new SpeechSynthesisUtterance(text);
            utter.rate = 0.94;
            utter.pitch = 1.05;

            // Pick an English voice
            const voices = window.speechSynthesis.getVoices();
            const preferredVoice = voices.find(v => v.lang.includes('en') || v.lang.includes('hi')) || voices[0];
            if (preferredVoice) utter.voice = preferredVoice;

            utter.onstart = () => avatarCircle.classList.add('speaking-pulse');
            utter.onend = () => avatarCircle.classList.remove('speaking-pulse');
            utter.onerror = () => avatarCircle.classList.remove('speaking-pulse');

            window.speechSynthesis.speak(utter);
        }}

        function toggleAudioSpeech() {{
            voiceUnlocked = !voiceUnlocked;
            localStorage.setItem('aps_voice_active', voiceUnlocked);
            syncAudioButtonUI();

            if (voiceUnlocked) {{
                executeSpeech("AI commentary initialized! " + speechPayload);
            }} else {{
                if ('speechSynthesis' in window) window.speechSynthesis.cancel();
                avatarCircle.classList.remove('speaking-pulse');
            }}
        }}

        // If previously enabled by user, trigger commentary after gentle delay
        if (voiceUnlocked) {{
            setTimeout(() => {{ executeSpeech(speechPayload); }}, 1500);
        }}

        // Repeat commentary every 5 minutes (300,000 ms)
        setInterval(() => {{
            if (voiceUnlocked && speechPayload.length > 5) {{
                executeSpeech(speechPayload);
            }}
        }}, 300000);

        // 4. CONTINUOUS MARQUEE
        const tickerBox = document.getElementById('tickerBox');
        const tickerWrapper = document.getElementById('tickerWrapper');
        let pos = tickerBox.offsetWidth;
        const velocity = {marquee_velocity};
        let lastTime = performance.now();

        function moveTicker(now) {{
            const dt = (now - lastTime) / 1000;
            lastTime = now;
            pos -= velocity * dt;
            if (pos < -tickerWrapper.offsetWidth) {{
                pos = tickerBox.offsetWidth;
            }}
            tickerWrapper.style.transform = 'translateX(' + pos + 'px)';
            requestAnimationFrame(moveTicker);
        }}
        requestAnimationFrame(moveTicker);
    </script>

</body>
</html>
"""
    components.html(full_html, height=735, scrolling=False)

  render_live_screen()
