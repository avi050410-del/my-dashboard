import streamlit as st
import pandas as pd
import gspread
import datetime
import json
import base64

# הגדרת דף לרוחב מלא
st.set_page_config(layout="wide", page_title="דשבורד מנהלת מרה\"ס")

# פונקציה לטעינת תמונה לרקע הכותרת
def get_image_base64(path):
    try:
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except:
        return None

img_b64 = get_image_base64("image_2fbe80.jpg") # שנה לשם התמונה שלך
bg_style = f"background-image: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url('data:image/jpeg;base64,{img_b64}');" if img_b64 else "background-color: #1E3A8A;"

@st.cache_data(ttl=0)
def get_data():
    creds_dict = json.loads(st.secrets["gspread"]["credentials"])
    gc = gspread.service_account_from_dict(creds_dict)
    sh = gc.open_by_url('https://docs.google.com/spreadsheets/d/1G-YKpuL3bBzesW0iEORf-x0WxvyeAM4At5RePg_OTKA/edit')
    worksheet = sh.worksheet('גיליון1')
    rows = worksheet.get_all_values()
    df = pd.DataFrame(rows[1:], columns=rows[0])
    
    for col in ["מסגרת שעות", "ניצול", "יתרה"]:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0).astype(int)
    
    df['אחוז ניצול'] = pd.to_numeric(df['אחוז ניצול'].astype(str).str.replace('%', '').replace('#DIV/0!', '0'), errors='coerce').fillna(0).astype(int)
    df['תאריך סיום הזמנה'] = pd.to_datetime(df['תאריך סיום הזמנה'].str.strip(), dayfirst=True, errors='coerce')
    return df

if st.sidebar.button("🔄 רענן נתונים"):
    st.cache_data.clear()
    st.rerun()

df = get_data()

# כותרת מעוצבת עם רקע
st.markdown(f"""
    <div style="{bg_style} padding: 40px; border-radius: 15px; text-align: center; color: white;">
        <h1 style='margin: 0;'>📊 דשבורד ניהול יועצים - מנהלת מרה"ס</h1>
    </div>
""", unsafe_allow_html=True)

# סינון
selected_tkhum = st.sidebar.selectbox("🔍 בחר תחום:", ["הכל"] + list(df['תחום'].unique()))
if selected_tkhum != "הכל":
    df = df[df['תחום'] == selected_tkhum]

# גרף תכנון מול ביצוע (צבעים שונים)
st.subheader("📈 השוואת תכנון מול ביצוע")
chart_data = df.groupby('תחום')[['מסגרת שעות', 'ניצול']].sum()
st.bar_chart(chart_data, color=["#3498db", "#e74c3c"]) # כחול לתכנון, אדום לניצול

# טבלה
st.subheader("📋 פירוט יועצים 📋")
today = datetime.datetime.now()
df['המלצה'] = df.apply(lambda row: f"מומלץ לנצל {int(round(row['יתרה'] / max(0.1, (row['תאריך סיום הזמנה'] - today).days / 30)))} שעות/חודש" if pd.notna(row['תאריך סיום הזמנה']) and (row['תאריך סיום הזמנה'] - today).days > 0 else "ההזמנה הסתיימה", axis=1)

df_display = df[["תחום", "שם יועץ", "תאריך סיום הזמנה", "מסגרת שעות", "ניצול", "יתרה", "אחוז ניצול", "המלצה"]].copy()
df_display['תאריך סיום הזמנה'] = df_display['תאריך סיום הזמנה'].dt.strftime('%m/%Y')
df_display.columns = ["תחום", "שם יועץ", "תאריך סיום", "מסגרת שעות", "ניצול", "יתרה", "אחוז ניצול", "המלצה"]

st.dataframe(df_display, use_container_width=True)
