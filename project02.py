import streamlit as st
import pandas as pd
import gspread
import datetime
import base64
import json

st.set_page_config(layout="wide", page_title="דשבורד מנהלת מרה\"ס")

@st.cache_data(ttl=0)
def get_data():
    # כאן הקסם: הוא לא מחפש קובץ במחשב, אלא לוקח את הסיסמה מההגדרות של האתר
    creds_dict = json.loads(st.secrets["gspread"]["credentials"])
    gc = gspread.service_account_from_dict(creds_dict)
    
    sh = gc.open_by_url('https://docs.google.com/spreadsheets/d/1G-YKpuL3bBzesW0iEORf-x0WxvyeAM4At5RePg_OTKA/edit')
    worksheet = sh.worksheet('גיליון1')
    rows = worksheet.get_all_values()
    df = pd.DataFrame(rows[1:], columns=rows[0])
    
    # ניקוי בסיסי
    for col in ["מסגרת שעות", "ניצול", "יתרה"]:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0).astype(int)
    
    return df

df = get_data()
st.write("הנתונים נטענו בהצלחה!")
st.dataframe(df)
