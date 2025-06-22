import streamlit as st
import pandas as pd
import requests
import os

# Load data restoran
EXCEL_FILE = os.path.join(os.path.dirname(__file__), 'Book1.xlsx')
df = pd.read_excel(EXCEL_FILE)

# Tag poin sistem
MOOD_TAG_POINTS = {
    "sedih": ["snack", "comfort", "manis", "siapsaji", "creamy", "gurih", "hangat"],
    "marah": ["pedas", "snack", "crunchy", "berbumbu", "berminyak"],
    "senang": ["healthy", "segar", "fresh", "buah", "salad", "jus", " comfort"],
    "bosan": ["autentik", "mahal", "fusion", "aesthetic"],
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


# Set default hanya sekali
if "show_popup" not in st.session_state:
    st.session_state.show_popup = True
# Tampilkan simulasi popup sederhana
# Jika mood belum dipilih, tampilkan modal palsu
if "selected_mood" not in st.session_state:
    with st.container():
        st.markdown("""
            <style>
                .popup-container {
                    position: fixed;
                    top: 0; left: 0; right: 0; bottom: 0;
                    background-color: rgba(0,0,0,0.5);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 9999;
                }
                .popup-box {
                    background-color: #FFF9F0;
                    padding: 30px;
                    border-radius: 16px;
                    text-align: center;
                    max-width: 400px;
                    width: 90%;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                }
            </style>
            <div class="popup-container">
                <div class="popup-box">
                    <h3 style="color: #FFAD60;">Apa mood kamu hari ini?</h3>
                </div>
            </div>
        """, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("😊", key="mood_senang"):
                st.session_state.selected_mood = "senang"
        with col2:
            if st.button("😢", key="mood_sedih"):
                st.session_state.selected_mood = "sedih"
        with col3:
            if st.button("😠", key="mood_marah"):
                st.session_state.selected_mood = "marah"
        with col4:
            if st.button("😐", key="mood_bosan"):
                st.session_state.selected_mood = "bosan"

        st.stop()





 
# Dropdown kecamatan
kecamatan_list = df["kecamatan"].dropna().unique().tolist()
kecamatan = st.selectbox("Pilih Kecamatan", sorted(kecamatan_list), key="kec_drop")

if st.button("Cari Rekomendasi"):
    if "selected_mood" not in st.session_state:
        st.warning("Silakan pilih mood terlebih dahulu melalui popup di atas.")
        st.stop()
    
    selected_mood = st.session_state.selected_mood

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
