import streamlit as st
import pandas as pd
import requests
import os

# Load data restoran
EXCEL_FILE = os.path.join(os.path.dirname(__file__), 'Book1.xlsx')
df = pd.read_excel(EXCEL_FILE)

# Tag poin sistem
MOOD_TAG_POINTS = {
    "sedih": ["snack", "comfort", "manis", "junkfood", "creamy", "gurih", "hangat"],
    "marah": ["pedas", "snack", "crunchy", "berbumbu", "berminyak"],
    "senang": ["healthy", "segar", "fresh", "buah", "salad", "jus"],
    "bosan": ["autentik", "mahal", "fusion", "aesthetic", "berwarna"],
}
MOOD_TAG_WEIGHT = {"sedih": 1, "marah": 1, "senang": 2, "bosan": 2}

WEATHER_TAG_POINTS = {
    "Clear": ["dingin"],
    "Rain": ["kuah", "hangat"],
    "Clouds": []
}
WEATHER_TAG_WEIGHT = {"Clear": 2, "Rain": 1, "Clouds": 0}

# API Cuaca
API_KEY = "071c48a3ee374d04bbcfeb42e452d2d4"

def get_weather(city):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city},ID&appid={API_KEY}&units=metric"
        res = requests.get(url).json()
        return res['weather'][0]['main']
    except:
        return ""

# UI START
st.set_page_config(page_title="MoodyFoody", layout="centered")
st.markdown("<style>body { background-color: #FFF9F0; }</style>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center; color: #FFAD60;'>MoodyFoody</h1>", unsafe_allow_html=True)

# Popup mood pilihan
if "selected_mood" not in st.session_state:
    with st.modal("Apa mood kamu hari ini?"):
        st.write("Pilih salah satu mood untuk dapatkan rekomendasi makanan:")
        cols = st.columns(4)
        for i, mood in enumerate(["sedih", "marah", "senang", "bosan"]):
            if cols[i].button(mood.capitalize()):
                st.session_state.selected_mood = mood
                st.rerun()

# Dropdown kecamatan
kecamatan_list = df["kecamatan"].dropna().unique().tolist()
kecamatan = st.selectbox("Pilih Kecamatan", sorted(kecamatan_list), key="kec_drop")

if st.button("Cari Rekomendasi"):
    selected_mood = st.session_state.get("selected_mood", "sedih")
    weather = get_weather("Yogyakarta")

    st.markdown(f"<div class='result-mood-box'>Mood: <b>{selected_mood.capitalize()}</b> | Cuaca: <b>{weather}</b></div>", unsafe_allow_html=True)

    # Scoring
    def hitung_skor(tags):
        skor = 0
        for tag in str(tags).split(","):
            tag = tag.strip().lower()
            if tag in MOOD_TAG_POINTS[selected_mood]:
                skor += MOOD_TAG_WEIGHT[selected_mood]
            if tag in WEATHER_TAG_POINTS.get(weather, []):
                skor += WEATHER_TAG_WEIGHT[weather]
        return skor

    filtered = df[df["kecamatan"] == kecamatan].copy()
    filtered["skor"] = filtered["tags"].apply(hitung_skor)
    filtered = filtered.sort_values(by="skor", ascending=False)

    # Tampilkan hasil
    st.markdown("<div class='results-scroll-container'>", unsafe_allow_html=True)
    for idx, row in filtered.iterrows():
        st.markdown("""
            <div class='resto-box {highlight}'>
                <div class='resto-row'>
                    <div class='resto-name'>{name}</div>
                    <div class='resto-rating'>⭐ {rating}</div>
                    <div><a href='{link}' target='_blank'>Maps</a></div>
                    {icon}
                </div>
            </div>
        """.format(
            name=row["nama"],
            rating=row["rating"],
            link=row["link"],
            icon="<div class='icon'>👍</div>" if row["skor"] == filtered["skor"].max() and row["skor"] > 0 else "",
            highlight="highlight" if row["skor"] == filtered["skor"].max() and row["skor"] > 0 else ""
        ), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Tambahan CSS
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
