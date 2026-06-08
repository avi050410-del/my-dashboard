import streamlit as st
import pandas as pd
import gspread
import datetime
import json
import base64

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
    
    # ניקוי נתונים
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

# חישוב המלצה וחריגות
today = datetime.datetime.now()
df['המלצה'] = df.apply(lambda row: f"מומלץ: {int(round(row['יתרה'] / max(0.1, (row['תאריך סיום הזמנה'] - today).days / 30)))} שעות/חודש" if pd.notna(row['תאריך סיום הזמנה']) and (row['תאריך סיום הזמנה'] - today).days > 0 else "ההזמנה הסתיימה", axis=1)

st.subheader("📋 פירוט יועצים")
st.dataframe(df.rename(columns={"תחום": "🏢 תחום", "שם יועץ": "👤 שם יועץ"}), use_container_width=True)

# אזור החריגות
st.markdown("---")
st.subheader("⚠️ התראות חריגה בניצול")

# בדיקת חריגה (אם הניצול בפועל חורג ב-30% מהממוצע)
# כאן אנחנו בודקים אם הניצול הנוכחי גבוה מ-1.3 * ממוצע חודשי
df['ממוצע_חודשי'] = df['מסגרת שעות'] / 12 # נניח ממוצע שנתי
df['חריג'] = df['ניצול'] > (df['ממוצע_חודשי'] * 1.3)

chorigim = df[df['חריג'] == True]

if not chorigim.empty:
    for index, row in chorigim.iterrows():
        st.warning(f"🚨 **{row['שם יועץ']}**: חריגה משמעותית בניצול! (ניצול בפועל גבוה ב-30% מהצפוי).")
else:
    st.success("✅ אין יועצים בחריגת ניצול מעל הרף המוגדר.")
