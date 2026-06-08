import streamlit as st
import pandas as pd
import gspread
import datetime
import base64
import json

# הגדרת דף לרוחב מלא
st.set_page_config(layout="wide", page_title="דשבורד מנהלת מרה\"ס")

@st.cache_data(ttl=0)
def get_data():
    # חיבור מאובטח דרך ה-Secrets של Streamlit
    creds_dict = json.loads(st.secrets["gspread"]["credentials"])
    gc = gspread.service_account_from_dict(creds_dict)
    
    sh = gc.open_by_url('https://docs.google.com/spreadsheets/d/1G-YKpuL3bBzesW0iEORf-x0WxvyeAM4At5RePg_OTKA/edit')
    worksheet = sh.worksheet('גיליון1')
    rows = worksheet.get_all_values()
    df = pd.DataFrame(rows[1:], columns=rows[0])
    
    # ניקוי ועיבוד נתונים
    for col in ["מסגרת שעות", "ניצול", "יתרה"]:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0).astype(int)
    
    df['אחוז ניצול'] = pd.to_numeric(df['אחוז ניצול'].astype(str).str.replace('%', '').replace('#DIV/0!', '0'), errors='coerce').fillna(0).astype(int)
    df['תאריך סיום הזמנה'] = pd.to_datetime(df['תאריך סיום הזמנה'].str.strip(), dayfirst=True, errors='coerce')
    
    return df

df = get_data()

# עיצוב וכותרות
st.markdown("<h1>📊 דשבורד ניהול יועצים - מנהלת מרה\"ס</h1>", unsafe_allow_html=True)

# סינון תחום
selected_tkhum = st.sidebar.selectbox("🔍 בחר תחום:", ["הכל"] + list(df['תחום'].unique()))
if selected_tkhum != "הכל":
    df = df[df['תחום'] == selected_tkhum]

# מטריקות
col1, col2, col3 = st.columns(3)
col1.metric("👤 סה\"כ יועצים", len(df))
col2.metric("📉 ממוצע ניצול", f"{df['אחוז ניצול'].mean():.0f}%")
col3.metric("💰 סה\"כ יתרה", f"{df['יתרה'].sum():,}")

# תצוגת טבלה מעוצבת
df_display = df.rename(columns={
    "שם יועץ": "👤 שם יועץ",
    "תחום": "🏢 תחום",
    "מסגרת שעות": "📅 מסגרת שעות",
    "ניצול": "📊 ניצול",
    "יתרה": "💰 יתרה",
    "אחוז ניצול": "📈 אחוז ניצול",
    "תאריך סיום הזמנה": "⏳ תאריך סיום"
})

st.dataframe(df_display, use_container_width=True)
