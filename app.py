import streamlit as st
import pandas as pd
import numpy as np
import requests
import os

# Konstanta
API_KEY = "071c48a3ee374d04bbcfeb42e452d2d4"
EXCEL_FILE = "Book1.xlsx"

def load_data():
    df = pd.read_excel(EXCEL_FILE)
    df["tags"] = df["tags"].apply(lambda x: [t.strip().lower() for t in str(x).split(",")])
    return df

def get_weather(kecamatan):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={kecamatan},ID&appid={API_KEY}&units=metric&lang=id"
    try:
        response = requests.get(url).json()
        weather_main = response["weather"][0]["main"]
        temp = response["main"]["temp"]

        if weather_main == "Clear" and temp > 30:
            return "Cerah", "panas terik"
        elif weather_main in ["Rain", "Drizzle", "Thunderstorm"]:
            return "Hujan", "hujan"
        elif weather_main in ["Clouds", "Mist", "Haze", "Fog"]:
            return "Berawan", "berawan"
        else:
            return "Berawan", "berawan"
    except:
        return "Berawan", "berawan"

def calculate_score(tags, mood, cuaca):
    skor = 0
    if mood in MOOD_TAGS:
        skor += sum([MOOD_TAGS[mood].get(t, 0) for t in tags])
    if cuaca in CUACA_TAGS:
        skor += sum([CUACA_TAGS[cuaca].get(t, 0) for t in tags])
    return skor

# Tag dan Poin
MOOD_TAGS = {
    "sedih": {"snack": 1, "comfort": 1, "manis": 1, "siapsaji": 1, "creamy": 1, "gurih": 1, "hangat": 1},
    "marah": {"pedas": 1, "siapsaji": 1, "snack": 1, "crunchy": 1, "berbumbu": 1, "berminyak": 1},
    "senang": {"healthy": 2, "segar": 2, "fresh": 2, "buah": 2, "salad": 2, "jus": 2, "comfort": 1},
    "bosan": {"autentik": 2, "mahal": 2, "fusion": 2, "aesthetic": 2}
}
CUACA_TAGS = {
    "panas terik": {"dingin": 1, "es": 1, "salad": 1, "buah": 1},
    "hujan": {"kuah": 1, "hangat": 1, "pedas": 1, "rebus": 1, "comfort": 1},
    "berawan": {"ringan": 2, "snack": 2, "netral": 2}
}
KEY_TAGS = {
    "marah": ["pedas", "crunchy", "snack", "berminyak"],
    "sedih": ["comfort", "hangat", "siapsaji", "manis"]
}

# UI
st.set_page_config(page_title="MoodyFoody", layout="centered")
st.markdown("""
    <style>
        body { background-color: #FFF9F0; }
        .resto-box {
            background-color: white;
            border-radius: 16px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 16px;
            margin-bottom: 16px;
        }
        .resto-title {
            font-size: 20px;
            font-weight: bold;
            color: #FFAD60;
        }
        .resto-rating, .resto-link {
            font-size: 14px;
            color: #555;
        }
        .jempol {
            font-size: 18px;
            color: green;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #FFAD60;'>🍽️ MoodyFoody 🍽️</h1>", unsafe_allow_html=True)

mood = st.radio("Pilih Mood Kamu", ["senang", "sedih", "marah", "bosan"], horizontal=True)
df = load_data()
kecamatan_list = sorted(df["kecamatan"].unique())
kecamatan = st.selectbox("Pilih Kecamatan", kecamatan_list)

if kecamatan:
    cuaca_display, cuaca_penilaian = get_weather(kecamatan)
    st.markdown(f"### Mood: **{mood.capitalize()}**, Cuaca di **{kecamatan.title()}**: {cuaca_display}")

    df_filtered = df[df["kecamatan"].str.lower() == kecamatan.lower()].copy()
    df_filtered["skor"] = df_filtered["tags"].apply(lambda tags: calculate_score(tags, mood, cuaca_penilaian))
    df_filtered = df_filtered[df_filtered["skor"] > 0].copy()

    df_filtered["rating"] = pd.to_numeric(df_filtered["rating"].astype(str).str.replace(",", "."), errors="coerce")
    df_filtered["jumlah_rating"] = pd.to_numeric(df_filtered["jumlah_rating"].astype(str).str.replace(".", "", regex=False).str.replace(",", ""), errors="coerce")
    df_filtered["feedback_score"] = df_filtered.apply(lambda row: row["rating"] * np.log10(row["jumlah_rating"] + 1), axis=1)

    kategori_1 = df_filtered.sort_values(["skor", "feedback_score"], ascending=[False, False]).groupby("jenis_makanan", as_index=False).first()
    kategori_1["jempol"] = True

    sisa = df_filtered[~df_filtered["nama"].isin(kategori_1["nama"])]
    key_tags = set(KEY_TAGS.get(mood, []))
    kategori_2 = sisa[sisa["tags"].apply(lambda tags: any(tag in key_tags for tag in tags))].copy()
    kategori_2["jempol"] = True

    kategori_3 = kategori_1.copy()
    kategori_3["jempol"] = False

    final_df = pd.concat([kategori_1, kategori_2, kategori_3], ignore_index=True)
    final_df = final_df.sort_values(["jempol", "skor", "feedback_score"], ascending=[False, False, False])

    for _, row in final_df.iterrows():
        st.markdown(f"""
        <div class='resto-box'>
            <div class='resto-title'>{row['nama']} {'<span class="jempol">👍</span>' if row['jempol'] else ''}</div>
            <div class='resto-rating'>⭐ {row['rating']} ({int(row['jumlah_rating'])} ulasan)</div>
            <div class='resto-link'><a href='{row['g_link']}' target='_blank'>Lihat di Maps</a></div>
        </div>
        """, unsafe_allow_html=True)
