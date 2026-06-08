import streamlit as st
import pandas as pd
import gspread
import datetime
import json
import base64

# הגדרת דף לרוחב מלא
st.set_page_config(layout="wide", page_title="דשבורד יועצים")

def get_image_base64(path):
    try:
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except: return None

img_b64 = get_image_base64("image_2fbe80.jpg") 
bg_style = f"background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('data:image/jpeg;base64,{img_b64}'); background-size: cover; background-position: center;" if img_b64 else "background-color: #2E7D32;"

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

# כותרת
st.markdown(f"""<div style="{bg_style} padding: 50px; border-radius: 20px; text-align: center; color: white;"><h1>📊 דשבורד ניהול יועצים</h1></div>""", unsafe_allow_html=True)

# סינון
all_tkhumim = [t for t in df['תחום'].unique() if t != 'מנהלת מעבר']
selected_tkhum = st.sidebar.selectbox("🔍 בחר תחום:", ["הכל"] + list(all_tkhumim))
if selected_tkhum != "הכל": df = df[df['תחום'] == selected_tkhum]
else: df = df[df['תחום'] != 'מנהלת מעבר']

# גרף
st.subheader("📈 השוואת תכנון מול ביצוע")
st.bar_chart(df.groupby('תחום')[['מסגרת שעות', 'ניצול']].sum(), color=["#006400", "#90EE90"])

# לוגיקה משולבת: המלצה + סימן חריגה (⚠️)
today = datetime.datetime.now()
def process_row(row):
    months_left = max(0.1, (row['תאריך סיום הזמנה'] - today).days / 30) if pd.notna(row['תאריך סיום הזמנה']) else 1
    
    # חישוב המלצה
    recommendation = f"מומלץ: {int(round(row['יתרה'] / months_left))} שעות/חודש" if (row['תאריך סיום הזמנה'] - today).days > 0 else "ההזמנה הסתיימה"
    
    # חישוב חריגה (35%)
    expected_balance = (row['מסגרת שעות'] / 12) * months_left
    alert = "⚠️" if row['יתרה'] < (expected_balance * 0.65) else ""
    
    return recommendation, alert

df[['המלצה', 'חריגה']] = df.apply(lambda row: pd.Series(process_row(row)), axis=1)

# הצגת הטבלה
df_display = df[["תחום", "שם יועץ", "תאריך סיום הזמנה", "מסגרת שעות", "ניצול", "יתרה", "אחוז ניצול", "המלצה", "חריגה"]].copy()
df_display['תאריך סיום הזמנה'] = df_display['תאריך סיום הזמנה'].dt.strftime('%m/%Y')
df_display.columns = ["🏢 תחום", "👤 שם יועץ", "⏳ תאריך סיום", "📅 מסגרת שעות", "📊 ניצול", "💰 יתרה", "📈 אחוז ניצול", "💡 המלצה", "⚠️"]

st.subheader("📋 פירוט יועצים")
st.dataframe(df_display, use_container_width=True)
