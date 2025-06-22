import streamlit as st
import pandas as pd
import numpy as np
import requests
import math

API_KEY = "071c48a3ee374d04bbcfeb42e452d2d4"
EXCEL_FILE = "Book1.xlsx"

MOOD_TAGS = {
    "sedih": {"snack": 1, "comfort": 1, "manis": 1, "siapsaji": 1, "creamy": 1, "gurih": 1, "hangat": 1},
    "marah": {"pedas": 1, "siapsaji": 1, "snack": 1, "crunchy": 1, "berbumbu": 1, "berminyak": 1},
    "senang": {"healthy": 2, "segar": 2, "fresh": 2, "buah": 2, "salad": 2, "jus": 2, "comfort": 1},
    "bosan": {"autentik": 2, "mahal": 2, "fusion": 2, "aesthetic": 2},
}

CUACA_TAGS = {
    "panas terik": {"dingin": 1, "es": 1, "salad": 1, "buah": 1},
    "hujan": {"kuah": 1, "hangat": 1, "pedas": 1, "rebus": 1, "comfort": 1},
    "berawan": {"ringan": 2, "snack": 2, "netral": 2},
}

KEY_TAGS = {
    "marah": ["pedas", "crunchy", "snack", "berminyak"],
    "sedih": ["comfort", "hangat", "siapsaji", "manis"],
}

def load_data():
    df = pd.read_excel(EXCEL_FILE)
    df["tags"] = df["tags"].apply(lambda x: [t.strip().lower() for t in str(x).split(",")])
    return df

def get_weather(kecamatan):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={kecamatan},ID&appid={API_KEY}&units=metric&lang=id"
    try:
        r = requests.get(url).json()
        main = r["weather"][0]["main"]
        temp = r["main"]["temp"]
        display_weather = {
            "Clear": "Cerah", "Rain": "Hujan", "Drizzle": "Gerimis", "Thunderstorm": "Badai Petir",
            "Clouds": "Berawan", "Mist": "Berkabut", "Fog": "Berkabut", "Haze": "Kabut Tipis"
        }.get(main, "Berawan")
        moodify_weather = "panas terik" if main == "Clear" and temp > 30 else \
                          "hujan" if main in ["Rain", "Drizzle", "Thunderstorm"] else "berawan"
        return display_weather, moodify_weather
    except:
        return "Berawan", "berawan"

def calculate_score(tags, mood, cuaca):
    score = sum([MOOD_TAGS.get(mood, {}).get(tag, 0) for tag in tags])
    score += sum([CUACA_TAGS.get(cuaca, {}).get(tag, 0) for tag in tags])
    return score

# UI
st.set_page_config(page_title="MoodyFoody", layout="wide")
st.title("🍽️ MoodyFoody")

df = load_data()
kecamatan_list = sorted(df["kecamatan"].unique())

col1, col2 = st.columns([1, 2])
with col1:
    mood = st.selectbox("Pilih Mood:", ["", "senang", "sedih", "marah", "bosan"])
with col2:
    kecamatan = st.selectbox("Pilih Kecamatan:", [""] + kecamatan_list)

if mood and kecamatan:
    st.markdown("---")
    cuaca_display, cuaca_kondisi = get_weather(kecamatan)
    st.subheader(f"Rekomendasi untuk kamu yang merasa **{mood}** di **{kecamatan}**, cuacanya **{cuaca_display}** ☁️")

    df_filtered = df[df["kecamatan"].str.lower() == kecamatan.lower()].copy()
    df_filtered["skor"] = df_filtered["tags"].apply(lambda x: calculate_score(x, mood, cuaca_kondisi))

    df_filtered["rating"] = pd.to_numeric(df_filtered["rating"].astype(str).str.replace(",", "."), errors="coerce")
    df_filtered["jumlah_rating"] = pd.to_numeric(df_filtered["jumlah_rating"].astype(str).str.replace(".", ""), errors="coerce")
    df_filtered = df_filtered[df_filtered["skor"] > 0].copy()
    df_filtered["feedback_score"] = df_filtered.apply(lambda r: r["rating"] * math.log10(r["jumlah_rating"] + 1), axis=1)

    kategori_1 = df_filtered.sort_values(["skor", "feedback_score"], ascending=[False, False])
    kategori_1 = kategori_1.groupby("jenis_makanan", as_index=False).first()
    kategori_1["jempol"] = True

    sisa = df_filtered[~df_filtered["nama"].isin(kategori_1["nama"])]
    key_tags = set(KEY_TAGS.get(mood, []))
    kategori_2 = sisa[sisa["tags"].apply(lambda x: any(tag in key_tags for tag in x))].copy()
    kategori_2["jempol"] = True

    kategori_3 = kategori_1.copy()
    kategori_3["jempol"] = False

    final_df = pd.concat([kategori_1, kategori_2, kategori_3], ignore_index=True)
    final_df = final_df.sort_values(["jempol", "skor", "feedback_score"], ascending=[False, False, False])

    for _, row in final_df.iterrows():
        with st.container():
            st.markdown(f"### {row['nama']}")
            st.markdown(f"⭐ **{row['rating']}** ({int(row['jumlah_rating'])} rating) &nbsp; 🎯 Skor: {row['skor']}")
            st.markdown(f"[Lihat di Maps]({row['g_link']})")
            if row['jempol']:
                st.markdown("👍 Rekomendasi utama")
            st.markdown("---")
