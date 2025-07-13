import streamlit as st
import pandas as pd
import joblib
import os
from pathlib import Path

# === CONFIGURASI STREAMLIT ===
st.set_page_config(page_title="Prediksi TPT Jawa Tengah", layout="centered")
st.title("📊 Prediksi Tingkat Pengangguran Terbuka (TPT) Jawa Tengah")
st.markdown("Masukkan tahun yang ingin kamu prediksi untuk mengetahui estimasi TPT di Jawa Tengah.")

# === LOAD MODEL ===
model = joblib.load("model_tpt.pkl")

# === INPUT USER ===
input_tahun = st.number_input("🗓️ Masukkan tahun prediksi", min_value=2020, max_value=2100, step=1)

# === SESSION STATE INISIAL ===
if 'kab_page' not in st.session_state:
    st.session_state.kab_page = 0
if 'manual_data' not in st.session_state:
    st.session_state.manual_data = []

# === OPSIONAL: INPUT DATA KABUPATEN ===
st.markdown("#### (Opsional) Masukkan Data Kabupaten untuk Tahun Ini")

with st.expander("➕ Tambahkan Data Kabupaten (opsional)"):
    num_rows = st.number_input("Jumlah Kabupaten yang ingin dimasukkan", min_value=0, max_value=36, value=len(st.session_state.manual_data), key="total_kab_input")
    rows_per_page = 5
    total_pages = (num_rows + rows_per_page - 1) // rows_per_page

    # === IMPORT CSV ===
    st.markdown("📌 Format CSV harus memiliki kolom berikut: `kabupaten`, `laki_laki`, `perempuan`, `tahun`, dan `presentase`")
    uploaded_file = st.file_uploader("📥 Upload CSV", type="csv")
    if uploaded_file:
        df_uploaded = pd.read_csv(uploaded_file)
        save_folder = Path("data/tpt_jk")
        save_folder.mkdir(parents=True, exist_ok=True)

        save_path = save_folder / f"tpt_jk{input_tahun}.csv"
        df_uploaded.to_csv(save_path, index=False)
        st.info(f"📂 Data disimpan ke: `{save_path}`")
        st.session_state.manual_data = []
        for _, row in df_uploaded.iterrows():
            st.session_state.manual_data.append({
                "kabupaten": row['kabupaten'],
                "laki_laki": float(row['laki_laki']),
                "perempuan": float(row['perempuan']),
                "jumlah": float(row['laki_laki']) + float(row['perempuan']),
                "tahun": input_tahun,
                "presentase": float(row['jumlah'])
            })
        st.success("✅ Data dari CSV berhasil dimuat!")

    # === INISIALISASI MANUAL DATA ===
    while len(st.session_state.manual_data) < num_rows:
        st.session_state.manual_data.append({
            "kabupaten": "",
            "laki_laki": 0.0,
            "perempuan": 0.0,
            "jumlah": 0.0,
            "tahun": input_tahun,
            "presentase": 0.0
        })

    # === PAGINATION ===
    if total_pages > 1:
        col_prev, col_info, col_next = st.columns([1, 2, 1])

        with col_prev:
            if st.button("⏮️ Prev", disabled=st.session_state.kab_page == 0):
                st.session_state.kab_page -= 1
                st.rerun()

        with col_next:
            if st.button("Next ⏭️", disabled=st.session_state.kab_page >= total_pages - 1):
                st.session_state.kab_page += 1
                st.rerun()

        with col_info:
            st.markdown(
                f"<center>Halaman {st.session_state.kab_page + 1} dari {total_pages}</center>",
                unsafe_allow_html=True
            )

    # === INPUT TIAP HALAMAN ===
    start_idx = st.session_state.kab_page * rows_per_page
    end_idx = min(start_idx + rows_per_page, num_rows)

    for i in range(start_idx, end_idx):
        st.markdown(f"##### Kabupaten #{i+1}")
        st.session_state.manual_data[i]['kabupaten'] = st.text_input(f"Nama Kabupaten #{i+1}", key=f"kab_{i}", value=st.session_state.manual_data[i]['kabupaten'])
        st.session_state.manual_data[i]['laki_laki'] = st.number_input(f"Laki-laki (ribu orang) #{i+1}", key=f"laki_{i}", min_value=0.0, value=st.session_state.manual_data[i]['laki_laki'])
        st.session_state.manual_data[i]['perempuan'] = st.number_input(f"Perempuan (ribu orang) #{i+1}", key=f"perempuan_{i}", min_value=0.0, value=st.session_state.manual_data[i]['perempuan'])
        st.session_state.manual_data[i]['presentase'] = st.number_input(f"Presentase TPT (%) #{i+1}", key=f"persen_{i}", min_value=0.0, value=st.session_state.manual_data[i]['presentase'])
        st.session_state.manual_data[i]['jumlah'] = st.session_state.manual_data[i]['laki_laki'] + st.session_state.manual_data[i]['perempuan']
        st.session_state.manual_data[i]['tahun'] = input_tahun

# === TOMBOL PREDIKSI ===
if st.button("🔮 Prediksi TPT"):
    manual_data = st.session_state.manual_data

    if manual_data:
        presentases = [d["presentase"] for d in manual_data if d["presentase"] is not None]
        if presentases:
            prediksi_manual = sum(presentases) / len(presentases)
            st.success(f"🎯 Prediksi TPT berdasarkan input manual: **{prediksi_manual:.2f}%**")
        else:
            st.warning("⚠️ Presentase belum diisi di input manual.")
    else:
        prediksi = model.predict(pd.DataFrame({'tahun': [input_tahun]}))
        st.success(f"🎯 Prediksi TPT untuk tahun **{input_tahun}** adalah **{prediksi[0]:.2f}%**")

    # === TAMPILKAN TABEL DATA KABUPATEN ===
    if manual_data:
        st.subheader("📄 Data Kabupaten yang Kamu Masukkan")
        df_manual = pd.DataFrame(manual_data)
        st.dataframe(df_manual[['kabupaten', 'laki_laki', 'perempuan', 'jumlah', 'tahun', 'presentase']])
    else:
        # Load dari file seperti biasa
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

        jk_filtered = df_jk[df_jk['tahun'] == input_tahun]
        kb_filtered = df_kb[df_kb['tahun'] == input_tahun]

        merged = pd.merge(jk_filtered, kb_filtered, on=['kabupaten', 'tahun'], how='inner')

        if not merged.empty:
            st.subheader("📄 Data Kabupaten dari Dataset")
            st.dataframe(merged[['kabupaten', 'laki_laki', 'perempuan', 'jumlah', 'tahun', 'presentase']])
        else:
            st.warning("⚠️ Data untuk tahun tersebut belum tersedia di file.")
