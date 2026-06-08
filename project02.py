import streamlit as st
import pandas as pd
import gspread
import datetime
import json

# הגדרת דף לרוחב מלא
st.set_page_config(layout="wide", page_title="דשבורד מנהלת מרה\"ס")

@st.cache_data(ttl=0)
def get_data():
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
    
    return df

# כפתור ריענון
if st.sidebar.button("🔄 רענן נתונים"):
    st.cache_data.clear()
    st.rerun()

df = get_data()

# עיצוב כותרת ראשית
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>📊 דשבורד ניהול יועצים - מנהלת מרה\"ס 🚀</h1>", unsafe_allow_html=True)
st.markdown("---")

# סינון תחום בסיידבר
selected_tkhum = st.sidebar.selectbox("🔍 בחר תחום:", ["הכל"] + list(df['תחום'].unique()))
if selected_tkhum != "הכל":
    df = df[df['תחום'] == selected_tkhum]

# כרטיסי נתונים מעוצבים
st.subheader("💡 תמונת מצב כללית")
col1, col2, col3, col4 = st.columns(4)
col1.metric("👤 סה\"כ יועצים", len(df))
col2.metric("📅 ממוצע ניצול", f"{df['אחוז ניצול'].mean():.0f}%")
col3.metric("💰 סה\"כ יתרה", f"{df['יתרה'].sum():,}")
col4.metric("📉 הזמנות פעילות", df[df['יתרה'] > 0].shape[0])

st.markdown("---")

# דשבורד תכנון מול ביצוע
st.subheader("📈 גרף תכנון מול ביצוע לפי תחום")
df_grouped = df.groupby('תחום')[['מסגרת שעות', 'ניצול']].sum()
st.bar_chart(df_grouped)

# טבלת נתונים
st.subheader("📋 פירוט יועצים מפורט")

# חישוב המלצה
today = datetime.datetime.now()
df['המלצה'] = df.apply(lambda row: f"מומלץ לנצל {int(round(row['יתרה'] / max(0.1, (row['תאריך סיום הזמנה'] - today).days / 30)))} שעות/חודש" if pd.notna(row['תאריך סיום הזמנה']) and (row['תאריך סיום הזמנה'] - today).days > 0 else "ההזמנה הסתיימה", axis=1)

# הכנה לתצוגה
df_display = df[["תחום", "שם יועץ", "תאריך סיום הזמנה", "מסגרת שעות", "ניצול", "יתרה", "אחוז ניצול", "המלצה"]].copy()
df_display['תאריך סיום הזמנה'] = df_display['תאריך סיום הזמנה'].dt.strftime('%m/%Y')
df_display.columns = ["תחום", "שם יועץ", "תאריך סיום", "מסגרת שעות", "ניצול", "יתרה", "אחוז ניצול", "המלצה"]

st.dataframe(df_display, use_container_width=True)
