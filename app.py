import streamlit as st
import pandas as pd
import numpy as np
import requests

API_KEY = "071c48a3ee374d04bbcfeb42e452d2d4"
EXCEL_FILE = "Book1.xlsx"

# Tag dan poin
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

def load_data():
    df = pd.read_excel(EXCEL_FILE)
    df["tags"] = df["tags"].apply(lambda x: [t.strip().lower() for t in str(x).split(",")])
    return df

def get_weather(kecamatan):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={kecamatan},ID&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url).json()
        main = response["weather"][0]["main"]
        temp = response["main"]["temp"]
        if main == "Clear" and temp > 30:
            return "panas terik"
        elif main in ["Rain", "Drizzle", "Thunderstorm"]:
            return "hujan"
        else:
            return "berawan"
    except:
        return "berawan"

def calculate_score(tags, mood, cuaca):
    score = 0
    score += sum([MOOD_TAGS.get(mood, {}).get(tag, 0) for tag in tags])
    score += sum([CUACA_TAGS.get(cuaca, {}).get(tag, 0) for tag in tags])
    return score

st.title("🍽️ MoodyFoody (Excel + Streamlit)")

df = load_data()
kecamatan_list = sorted(df["kecamatan"].unique())

mood = st.selectbox("Pilih Mood Kamu", options=["senang", "sedih", "marah", "bosan"])
kecamatan = st.selectbox("Pilih Kecamatan", options=kecamatan_list)

if st.button("Cari Rekomendasi"):
    cuaca = get_weather(kecamatan)
    df_filtered = df[df["kecamatan"].str.lower() == kecamatan.lower()].copy()
    df_filtered["skor"] = df_filtered["tags"].apply(lambda tags: calculate_score(tags, mood, cuaca))
    df_filtered = df_filtered[df_filtered["skor"] > 0]

    df_filtered["rating"] = pd.to_numeric(df_filtered["rating"].astype(str).str.replace(",", "."), errors="coerce").fillna(0)
    df_filtered["jumlah_rating"] = df_filtered["jumlah_rating"].astype(str).str.replace(".", "").str.replace(",", "")
    df_filtered["jumlah_rating"] = pd.to_numeric(df_filtered["jumlah_rating"], errors="coerce").fillna(0)
    df_filtered["feedback_score"] = df_filtered.apply(lambda row: row["rating"] * np.log10(row["jumlah_rating"] + 1), axis=1)

    # Kategori 1
    kategori_1 = df_filtered.sort_values(["skor", "feedback_score"], ascending=[False, False])
    kategori_1 = kategori_1.groupby("jenis_makanan", as_index=False).first()
    kategori_1["jempol"] = True

    # Kategori 2
    sisa = df_filtered[~df_filtered["nama"].isin(kategori_1["nama"])]
    key_tags = set(KEY_TAGS.get(mood, []))
    kategori_2 = sisa[sisa["tags"].apply(lambda tags: any(tag in key_tags for tag in tags))].copy()
    kategori_2["jempol"] = True

    # Kategori 3
    kategori_3 = kategori_1.copy()
    kategori_3["jempol"] = False

    final_df = pd.concat([kategori_1, kategori_2, kategori_3], ignore_index=True)
    final_df = final_df.sort_values(["jempol", "skor", "feedback_score"], ascending=[False, False, False])

    st.subheader(f"Rekomendasi untuk *{mood}* di *{kecamatan}* (cuaca: *{cuaca}*)")

    for _, row in final_df.iterrows():
        st.markdown(f"### {row['nama']}")
        st.write(f"⭐ {row['rating']} ({int(row['jumlah_rating'])} ulasan)")
        st.write(f"🎯 Skor: {row['skor']}")
        st.write(f"[📍 Google Maps]({row['g_link']})")
        if row["jempol"]:
            st.write("👍 Rekomendasi Utama")
        st.markdown("---")
