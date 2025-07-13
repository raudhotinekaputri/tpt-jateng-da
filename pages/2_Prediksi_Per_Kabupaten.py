import streamlit as st
import pandas as pd
import joblib
from pathlib import Path

# === SETUP ===
st.set_page_config(page_title="Prediksi TPT Per Kabupaten", layout="centered")
st.title("🔍 Prediksi TPT Berdasarkan Kabupaten & Jenis Kelamin")
st.markdown("Prediksi TPT menggunakan model Random Forest berdasarkan kabupaten, jenis kelamin, dan tahun.")

# === LOAD MODEL ===
@st.cache_resource
def load_model_encoder():
    model = joblib.load("model_rf_kab.pkl")
    encoder = joblib.load("encoder_rf_kab.pkl")
    return model, encoder

rf_model, le_kab = load_model_encoder()

# === INPUT TAHUN ===
input_tahun = st.number_input("🗓️ Masukkan tahun prediksi", min_value=2020, max_value=2100, step=1)

# === SESSION STATE ===
if 'kab_page' not in st.session_state:
    st.session_state.kab_page = 0
if 'manual_data' not in st.session_state:
    st.session_state.manual_data = []

# === INPUT MANUAL / CSV ===
st.markdown("#### (Opsional) Masukkan Data Kabupaten")
with st.expander("➕ Tambahkan Data Kabupaten (opsional)"):
    num_rows = st.number_input("Jumlah Kabupaten yang ingin dimasukkan", min_value=0, max_value=36, value=len(st.session_state.manual_data), key="total_kab_input")
    rows_per_page = 5
    total_pages = (num_rows + rows_per_page - 1) // rows_per_page

    st.markdown("📌 Format CSV harus berisi: `kabupaten`, `laki_laki`, `perempuan`, `tahun`")

    uploaded_file = st.file_uploader("📥 Upload CSV", type="csv")
    if uploaded_file:
        df_uploaded = pd.read_csv(uploaded_file)
        required_cols = ['kabupaten', 'laki_laki', 'perempuan', 'tahun']
        if not all(col in df_uploaded.columns for col in required_cols):
            st.error(f"❌ Kolom CSV harus berisi: {', '.join(required_cols)}")
        else:
            save_folder = Path("data/tpt_prediksi")
            save_folder.mkdir(parents=True, exist_ok=True)
            save_path = save_folder / f"tpt_prediksi{input_tahun}.csv"
            df_uploaded.to_csv(save_path, index=False)
            st.info(f"📂 Data disimpan ke: `{save_path}`")

            st.session_state.manual_data = []
            for _, row in df_uploaded.iterrows():
                st.session_state.manual_data.append({
                    "kabupaten": row['kabupaten'],
                    "laki_laki": float(row['laki_laki']),
                    "perempuan": float(row['perempuan']),
                    "jumlah": float(row['laki_laki']) + float(row['perempuan']),
                    "tahun": int(row['tahun'])
                })
            st.success("✅ Data dari CSV berhasil dimuat!")

    # Tambahkan data kosong jika belum cukup
    while len(st.session_state.manual_data) < num_rows:
        st.session_state.manual_data.append({
            "kabupaten": "",
            "laki_laki": 0.0,
            "perempuan": 0.0,
            "jumlah": 0.0,
            "tahun": input_tahun
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
            st.markdown(f"<center>Halaman {st.session_state.kab_page + 1} dari {total_pages}</center>", unsafe_allow_html=True)

    # === INPUT FORM ===
    start_idx = st.session_state.kab_page * rows_per_page
    end_idx = min(start_idx + rows_per_page, num_rows)

    for i in range(start_idx, end_idx):
        st.markdown(f"##### Kabupaten #{i+1}")
        st.session_state.manual_data[i]['kabupaten'] = st.text_input(
            f"Nama Kabupaten #{i+1}", key=f"kab_{i}", value=st.session_state.manual_data[i]['kabupaten']
        )
        st.session_state.manual_data[i]['laki_laki'] = st.number_input(
            f"Laki-laki (ribu orang) #{i+1}", key=f"laki_{i}", min_value=0.0, value=st.session_state.manual_data[i]['laki_laki']
        )
        st.session_state.manual_data[i]['perempuan'] = st.number_input(
            f"Perempuan (ribu orang) #{i+1}", key=f"perempuan_{i}", min_value=0.0, value=st.session_state.manual_data[i]['perempuan']
        )
        st.session_state.manual_data[i]['jumlah'] = st.session_state.manual_data[i]['laki_laki'] + st.session_state.manual_data[i]['perempuan']
        st.session_state.manual_data[i]['tahun'] = input_tahun

# === TOMBOL PREDIKSI ===
if st.button("🔮 Prediksi TPT"):
    manual_data = st.session_state.manual_data
    if manual_data:
        results = []
        for d in manual_data:
            kab_input = ' '.join(d['kabupaten'].strip().split(' ')[1:]).title()
            matched_kab = [k for k in le_kab.classes_ if kab_input == k]

            if not matched_kab:
                results.append({**d, "prediksi": None, "keterangan": f"❌ Tidak ditemukan: {kab_input}"})
            else:
                kab_final = matched_kab[0]
                encoded_kab = le_kab.transform([kab_final])[0]
                df_test = pd.DataFrame([{
                    "tahun": d["tahun"],
                    "kabupaten_encoded": encoded_kab,
                    "laki_laki": d["laki_laki"],
                    "perempuan": d["perempuan"],
                    "jumlah": d["jumlah"]
                }])
                pred = rf_model.predict(df_test)[0]
                results.append({**d, "prediksi": pred, "keterangan": f"✅ {kab_final}"})

        df_result = pd.DataFrame(results)
        df_display = df_result[['kabupaten', 'laki_laki', 'perempuan', 'jumlah', 'tahun', 'prediksi', 'keterangan']]
        st.success("🎯 Prediksi berhasil dihitung!")
        st.subheader("📄 Hasil Prediksi TPT")
        st.dataframe(df_display)

        avg_pred = df_result["prediksi"].dropna().mean()
        if not pd.isna(avg_pred):
            st.info(f"📌 Rata-rata TPT dari data yang valid: **{avg_pred:.2f}%**")
    else:
        st.warning("⚠️ Belum ada data untuk diprediksi.")
