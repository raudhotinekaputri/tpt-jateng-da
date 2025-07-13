# app.py
import streamlit as st
import pandas as pd
import os
from pathlib import Path

# === CONFIG STREAMLIT ===
st.set_page_config(page_title="Dashboard TPT", layout="wide")
st.title("📊 Dashboard TPT Jawa Tengah")
st.markdown("Analisis data Tingkat Pengangguran Terbuka (TPT) berdasarkan kabupaten, jenis kelamin, dan waktu.")

# === LOAD DATA ===
base_path = Path("./data")
jk_folder = base_path / "tpt_jk"
kb_folder = base_path / "tpt_kb"

df_jk = pd.concat([
    pd.read_csv(jk_folder / file)
    for file in sorted(os.listdir(jk_folder)) if file.endswith(".csv")
], ignore_index=True)

df_kb = pd.concat([
    pd.read_csv(kb_folder / file)
    for file in sorted(os.listdir(kb_folder)) if file.endswith(".csv")
], ignore_index=True)

df_jk.columns = df_jk.columns.str.strip().str.lower().str.replace(" ", "_")
df_kb.columns = df_kb.columns.str.strip().str.lower().str.replace(" ", "_")

df_jk['tahun'] = pd.to_numeric(df_jk['tahun'], errors='coerce')
df_kb['tahun'] = pd.to_numeric(df_kb['tahun'], errors='coerce')

for col in ['laki_laki', 'perempuan', 'jumlah']:
    df_jk[col] = pd.to_numeric(df_jk[col], errors='coerce')
df_kb['presentase'] = pd.to_numeric(df_kb['presentase'], errors='coerce')

# === SIDEBAR FILTER ===
st.sidebar.header("🎯 Filter Data")
all_kab = sorted(df_jk["kabupaten"].unique())
selected_kab = st.sidebar.selectbox("Pilih Kabupaten", all_kab)
selected_year = st.sidebar.selectbox("Pilih Tahun", sorted(df_jk["tahun"].dropna().unique()))

# === SECTION: Tren Provinsi Secara Umum ===
with st.container():
    st.subheader("🗓️ Tren Umum TPT Provinsi Jawa Tengah")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📉 Rata-rata TPT per Tahun")
        rata2_tpt = df_kb.groupby("tahun")["presentase"].mean().reset_index()
        st.line_chart(rata2_tpt.rename(columns={"presentase": "Rata-rata TPT (%)"}).set_index("tahun"))
        st.caption("Grafik ini menunjukkan rata-rata TPT seluruh kabupaten/kota setiap tahun.")

    with col2:
        st.markdown("#### 🔮 Prediksi TPT Tahun Berikutnya")
        latest_year = df_jk["tahun"].max()
        df_latest = df_jk[df_jk["tahun"] == latest_year]
        jumlah_total = df_latest["jumlah"].sum()
        prediksi_tpt = jumlah_total / 100  # bisa ganti rumus
        st.metric("Prediksi TPT", f"{prediksi_tpt:.2f} %", delta=f"Dari tahun {latest_year}")
        st.caption("Estimasi TPT tahun depan berdasarkan jumlah pengangguran saat ini.")

# === SECTION: Pengangguran Terbanyak ===
with st.container():
    st.subheader("🚩 Kabupaten dengan Pengangguran Tertinggi")

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("#### 📍 Tertinggi per Tahun")
        max_kab = df_jk.loc[df_jk.groupby("tahun")["jumlah"].idxmax()].copy()
        max_kab["nama_tahun"] = max_kab["tahun"].astype(str)
        st.bar_chart(max_kab.set_index("nama_tahun")["jumlah"])
        st.caption("Kabupaten dengan jumlah pengangguran paling banyak setiap tahun.")

    with col4:
        st.markdown("#### 🔥 Top 5 Tertinggi Tahun Terbaru")
        top5 = df_kb[df_kb["tahun"] == latest_year].nlargest(5, "presentase")
        st.bar_chart(top5.set_index("kabupaten")["presentase"])
        st.caption("Lima besar kabupaten dengan persentase TPT tertinggi di tahun terbaru.")

# === SECTION: Data Berdasarkan Gender ===
with st.container():
    st.subheader("👫 Total Pengangguran Berdasarkan Jenis Kelamin")

    gender_per_year = df_jk.groupby("tahun")[["laki_laki", "perempuan"]].sum()
    st.line_chart(gender_per_year)
    st.caption("Tren jumlah pengangguran laki-laki dan perempuan setiap tahun.")

# === SECTION: Detail Kabupaten Terpilih ===
with st.container():
    st.subheader(f"📈 Tren & Ringkasan: {selected_kab}")

    col5, col6 = st.columns(2)

    with col5:
        st.markdown("#### 📊 Tren TPT Kabupaten")

        if selected_kab == "3300 Provinsi Jawa Tengah":
            trend_kab = df_kb[df_kb["kabupaten"] != "3300 Provinsi Jawa Tengah"].groupby("tahun")["presentase"].mean().reset_index()
            trend_kab = trend_kab.set_index("tahun").rename(columns={"presentase": "TPT Provinsi"})
            st.line_chart(trend_kab)
            st.caption("Grafik ini menunjukkan TPT Provinsi Jawa Tengah berdasarkan rata-rata semua kabupaten setiap tahun.")
        else:
            trend_kab = df_kb[df_kb["kabupaten"] == selected_kab][["tahun", "presentase"]].set_index("tahun")
            st.line_chart(trend_kab.rename(columns={"presentase": f"TPT {selected_kab}"}))
            st.caption(f"Grafik TPT {selected_kab} dari tahun ke tahun.")

    with col6:
        st.markdown("#### 📌 Ringkasan Data")
        if selected_kab == "3300 Provinsi Jawa Tengah":
            total = df_jk[df_jk["tahun"] == selected_year]["jumlah"].sum()
            laki = df_jk[df_jk["tahun"] == selected_year]["laki_laki"].sum()
            perempuan = df_jk[df_jk["tahun"] == selected_year]["perempuan"].sum()
            st.metric("Total Pengangguran", f"{total:.2f} ribu")
            st.metric("Laki-laki", f"{laki:.2f} ribu")
            st.metric("Perempuan", f"{perempuan:.2f} ribu")
        else:
            filtered = df_jk[(df_jk["kabupaten"] == selected_kab) & (df_jk["tahun"] == selected_year)]
            if not filtered.empty:
                st.metric("Total Pengangguran", f"{filtered['jumlah'].values[0]:.2f} ribu")
                st.metric("Laki-laki", f"{filtered['laki_laki'].values[0]:.2f} ribu")
                st.metric("Perempuan", f"{filtered['perempuan'].values[0]:.2f} ribu")
            else:
                st.warning("Data tidak tersedia untuk kombinasi tersebut.")
