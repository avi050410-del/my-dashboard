import streamlit as st
import pandas as pd
import gspread
import datetime
import base64
import json

# הגדרת דף לרוחב מלא
st.set_page_config(layout="wide", page_title="דשבורד מנהלת מרה\"ס")

# פונקציה לטעינת תמונה (וודא שהיא קיימת בתיקייה)
def get_image_base64(path):
    try:
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except:
        return None

img_b64 = get_image_base64("image_2fbe80.jpg")
banner_style = f"background-image: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url('data:image/jpeg;base64,{img_b64}');" if img_b64 else "background-color: #2E86C1;"

st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"] {{ direction: rtl; }}
    .header-banner {{
        {banner_style}
        background-size: cover;
        background-position: center;
        height: 200px;
        border-radius: 20px;
        margin-bottom: 30px;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        padding-right: 50px;
        color: white;
        text-shadow: 2px 2px 10px #000000;
    }}
    .stDataFrame {{ direction: rtl !important; text-align: right !important; }}
    </style>
    <div class="header-banner">
        <h1>📊 דשבורד ניהול יועצים - מנהלת מרה"ס</h1>
    </div>
""", unsafe_allow_html=True)

if st.sidebar.button("🔄 רענן נתונים"):
    st.cache_data.clear()
    st.rerun()

@st.cache_data(ttl=0)
def get_data():
    # חיבור מאובטח דרך ה-Secrets של Streamlit
    creds_dict = json.loads(st.secrets["gspread"]["credentials"])
    gc = gspread.service_account_from_dict(creds_dict)
    
    sh = gc.open_by_url('https://docs.google.com/spreadsheets/d/1G-YKpuL3bBzesW0iEORf-x0WxvyeAM4At5RePg_OTKA/edit')
    worksheet = sh.worksheet('גיליון1')
    rows = worksheet.get_all_values()
    df = pd.DataFrame(rows[1:], columns=rows[0])
    
    # ניקוי נתונים
    for col in ["מסגרת שעות", "ניצול", "יתרה"]:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0).astype(int)
    
    df['אחוז ניצול'] = pd.to_numeric(df['אחוז ניצול'].astype(str).str.replace('%', '').replace('#DIV/0!', '0'), errors='coerce').fillna(0).astype(int)
    df['תאריך סיום הזמנה'] = pd.to_datetime(df['תאריך סיום הזמנה'].str.strip(), dayfirst=True, errors='coerce')
    
    return df[["שם יועץ", "תחום", "מסגרת שעות", "ניצול", "יתרה", "אחוז ניצול", "תאריך סיום הזמנה"]]

df = get_data()
today = datetime.datetime.now()

def calculate_recommendation(row):
    if pd.isna(row['תאריך סיום הזמנה']): return "נתונים חסרים"
    months_left = (row['תאריך סיום הזמנה'] - today).days / 30
    if months_left <= 0: return "ההזמנה הסתיימה"
    return f"מומלץ לנצל {int(round(row['יתרה'] / max(0.1, months_left)))} שעות בחודש"

df['המלצה'] = df.apply(calculate_recommendation, axis=1)

selected_tkhum = st.sidebar.selectbox("🔍 בחר תחום:", ["הכל"] + list(df['תחום'].unique()))
if selected_tkhum != "הכל":
    df = df[df['תחום'] == selected_tkhum]

col1, col2, col3 = st.columns(3)
col1.metric("👤 סה\"כ יועצים", len(df))
col2.metric("📉 ממוצע ניצול", f"{df['אחוז ניצול'].mean():.0f}%")
col3.metric("💰 סה\"כ יתרה", f"{df['יתרה'].sum():,}")

st.subheader("📋 פירוט מצב יועצים")

df_display = df.rename(columns={
    "שם יועץ": "👤 שם יועץ",
    "תחום": "🏢 תחום",
    "מסגרת שעות": "📅 מסגרת שעות",
    "ניצול": "📊 ניצול",
    "יתרה": "💰 יתרה",
    "אחוז ניצול": "📈 אחוז ניצול",
    "תאריך סיום הזמנה": "⏳ תאריך סיום"
})

def format_date(val):
    if pd.isna(val): return "לא הוגדר"
    return val.strftime('%d/%m/%Y')

df_display['⏳ תאריך סיום'] = df_display['⏳ תאריך סיום'].apply(format_date)
st.dataframe(df_display, use_container_width=True)

st.subheader("⚠️ התראות דחופות")
for _, row in df[df['אחוז ניצול'] > 90].iterrows():
    st.warning(f"**{row['שם יועץ']}** ({row['תחום']}): {row['המלצה']}")
