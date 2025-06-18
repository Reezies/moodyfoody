from flask import Flask, render_template, request
import pandas as pd
import requests
import numpy as np
import os

app = Flask(__name__)
API_KEY = "071c48a3ee374d04bbcfeb42e452d2d4"
EXCEL_FILE = os.path.join(os.path.dirname(__file__), 'Book1.xlsx')

def load_data():
    df = pd.read_excel(EXCEL_FILE)
    return df


# Tag dan poin
MOOD_TAGS = {
    "sedih": {
        "snack": 1,
        "comfort": 1,
        "manis": 1,
        "siapsaji": 1,
        "creamy": 1,
        "gurih": 1,
        "hangat": 1
    },
    "marah": {
        "pedas": 1,
        "snack": 1,
        "crunchy": 1,
        "berbumbu": 1,
        "berminyak": 1
    },
    "senang": {
        "healthy": 2,
        "segar": 2,
        "fresh": 2,
        "buah": 2,
        "salad": 2,
        "jus": 2
    },
    "bosan": {
        "autentik": 2,
        "mahal": 2,
        "fusion": 2,
        "aesthetic": 2,
    }
}

CUACA_TAGS = {
    "panas terik": {
        "dingin": 1,
        "es": 1,
        "salad": 1,
        "buah": 1
    },
    "hujan": {
        "kuah": 1,
        "hangat": 1,
        "pedas": 1,
        "rebus": 1,
        "comfort": 1
    },
    "berawan": {
        "ringan": 2,
        "snack": 2,
        "netral": 2
    }
}

# Load data
def load_data():
    df = pd.read_excel(EXCEL_FILE)
    df["tags"] = df["tags"].apply(lambda x: [t.strip().lower() for t in str(x).split(",")])
    return df

# Get cuaca real-time
def get_weather(kecamatan):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={kecamatan},ID&appid={API_KEY}&units=metric&lang=id"
    try:
        response = requests.get(url).json()
        weather_main = response["weather"][0]["main"]
        temperature = response["main"]["temp"]

        display_weather = {
            "Clear": "Cerah",
            "Rain": "Hujan",
            "Drizzle": "Gerimis",
            "Thunderstorm": "Badai Petir",
            "Clouds": "Berawan",
            "Mist": "Berkabut",
            "Fog": "Berkabut",
            "Haze": "Kabut Tipis"
        }.get(weather_main, "Berawan")

        if weather_main == "Clear" and temperature > 30:
            moodify_weather = "panas terik"
        elif weather_main in ["Rain", "Drizzle", "Thunderstorm"]:
            moodify_weather = "hujan"
        elif weather_main in ["Clouds", "Mist", "Haze", "Fog"]:
            moodify_weather = "berawan"
        else:
            moodify_weather = "berawan"

        return display_weather, moodify_weather

    except:
        return "Berawan", "berawan"

# Hitung skor
def calculate_score(tags, mood, cuaca):
    skor = 0
    tags = [t.strip().lower() for t in tags]
    if mood in MOOD_TAGS:
        skor += sum([MOOD_TAGS[mood].get(t, 0) for t in tags])
    if cuaca in CUACA_TAGS:
        skor += sum([CUACA_TAGS[cuaca].get(t, 0) for t in tags])
    return skor

@app.route("/", methods=["GET"])
def index():
    df = load_data()
    kecamatan_list = sorted(df["kecamatan"].unique())
    return render_template("index.html", kecamatan_list=kecamatan_list, rekomendasi=None)

@app.route("/rekomendasi", methods=["POST"])
def rekomendasi():
    df = load_data()
    mood = request.form.get("mood")
    kecamatan = request.form.get("kecamatan")

    cuaca_display, cuaca_penilaian = get_weather(kecamatan)

    df_filtered = df[df["kecamatan"].str.lower() == kecamatan.lower()].copy()

    if df_filtered.empty:
        return render_template("index.html", rekomendasi=[], mood=mood, kecamatan=kecamatan, cuaca=cuaca_display, top_score=0, kecamatan_list=sorted(df["kecamatan"].unique()))

    df_filtered["skor"] = df_filtered["tags"].apply(lambda tags: calculate_score(tags, mood, cuaca_penilaian))
    df_filtered = df_filtered[df_filtered["skor"] > 0].copy()

    df_filtered["rating"] = pd.to_numeric(df_filtered["rating"], errors="coerce").fillna(0)
    df_filtered["j_rating"] = pd.to_numeric(df_filtered["j_rating"], errors="coerce").fillna(0)
    df_filtered["feedback_score"] = df_filtered.apply(lambda row: row["rating"] * np.log10(row["j_rating"] + 1), axis=1)

    kategori_1 = df_filtered.sort_values(["skor", "feedback_score"], ascending=[False, False])
    kategori_1 = kategori_1.groupby("j_makanan", as_index=False).first()
    kategori_1["jempol"] = True

    sisa = df_filtered[~df_filtered["nama"].isin(kategori_1["nama"])]

    key_tags = set(MOOD_TAGS.get(mood, {}))
    sisa["has_key_tag"] = sisa["tags"].apply(lambda tags: any(tag in key_tags for tag in tags))
    kategori_2 = sisa[sisa["has_key_tag"]].copy()
    kategori_2["jempol"] = True

    kategori_3 = sisa[~sisa["nama"].isin(kategori_2["nama"])]
    kategori_3["jempol"] = False

    final_df = pd.concat([kategori_1, kategori_2, kategori_3], ignore_index=True)
    final_df = final_df.sort_values(["jempol", "skor", "feedback_score"], ascending=[False, False, False])

    top_score = final_df["skor"].max()
    rekomendasi = final_df[["nama", "rating", "j_rating", "link", "skor", "jempol"]].to_dict(orient="records")

    return render_template("index.html", rekomendasi=rekomendasi, mood=mood, kecamatan=kecamatan, cuaca=cuaca_display, top_score=top_score, kecamatan_list=sorted(df["kecamatan"].unique()))

if __name__ == "__main__":
    app.run(debug=True)
