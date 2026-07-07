import streamlit as st
import pandas as pd
import gspread
import cloudinary
import cloudinary.uploader

from datetime import date, datetime
from oauth2client.service_account import ServiceAccountCredentials
from PIL import Image
from PIL.ExifTags import TAGS
from streamlit_js_eval import streamlit_js_eval
from math import radians, sin, cos, sqrt, atan2
from pathlib import Path


# =====================================
# PAGE CONFIG
# =====================================
st.set_page_config(
    page_title="Form Kunjungan Salesman",
    layout="centered"
)


# =====================================
# PATH LOGO
# =====================================
BASE_DIR = Path(__file__).parent
SIG_LOGO = BASE_DIR / "assets" / "sig.png"
SMBR_LOGO = BASE_DIR / "assets" / "smbr.jpg"


# =====================================
# CLOUDINARY CONFIG
# =====================================
cloudinary.config(
    cloud_name=st.secrets["cloudinary"]["cloud_name"],
    api_key=st.secrets["cloudinary"]["api_key"],
    api_secret=st.secrets["cloudinary"]["api_secret"]
)


# =====================================
# CUSTOM CSS
# =====================================
st.markdown("""
<style>

.stApp {
    background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
}

.block-container {
    background-color: white;
    padding: 2rem 2.5rem;
    border-radius: 18px;
    box-shadow: 0 8px 28px rgba(0,0,0,0.08);
    max-width: 900px;
}

.header-card {
    background: linear-gradient(90deg, #00796B 0%, #009688 100%);
    border-radius: 18px;
    padding: 18px 22px;
    margin-bottom: 22px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.12);
}

.header-title {
    text-align: center;
    color: white;
    font-size: 34px;
    font-weight: 800;
    margin: 0;
    line-height: 1.2;
}

.header-subtitle {
    text-align: center;
    color: #e0f2f1;
    font-size: 15px;
    margin-top: 6px;
}

.logo-box {
    background-color: white;
    border-radius: 14px;
    padding: 8px;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 82px;
}

.section-card {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 20px;
    margin-top: 18px;
    margin-bottom: 18px;
    box-shadow: 0 3px 12px rgba(0,0,0,0.04);
}

.section-title {
    font-size: 20px;
    font-weight: 800;
    color: #064e3b;
    margin-bottom: 14px;
    padding-bottom: 8px;
    border-bottom: 2px solid #d1fae5;
}

label {
    color: #374151 !important;
    font-weight: 700 !important;
    font-size: 14px !important;
}

.stTextInput input,
.stNumberInput input,
.stTextArea textarea {
    background-color: white !important;
    color: #111827 !important;
    border: 1px solid #d1d5db !important;
    border-radius: 10px !important;
}

.stTextInput input:disabled {
    -webkit-text-fill-color: #111827 !important;
    color: #111827 !important;
    background-color: #f1f5f9 !important;
    opacity: 1 !important;
    border: 1px solid #cbd5e1 !important;
}

.stSelectbox div[data-baseweb="select"] {
    background-color: white !important;
    color: #111827 !important;
    border-radius: 10px !important;
}

.stDateInput input {
    background-color: white !important;
    color: #111827 !important;
    border-radius: 10px !important;
}

[data-testid="stFileUploader"] {
    background-color: white;
    border-radius: 12px;
    border: 1px dashed #94a3b8;
    padding: 1rem;
}

.stButton > button {
    background: linear-gradient(90deg, #00796B 0%, #009688 100%);
    color: white !important;
    border-radius: 12px;
    height: 52px;
    width: 100%;
    font-size: 17px;
    font-weight: 800;
    border: none;
    transition: 0.3s;
}

.stButton > button p {
    color: white !important;
    font-weight: 800 !important;
}

.stButton > button:hover {
    background: linear-gradient(90deg, #00695C 0%, #00897B 100%);
    color: white !important;
    transform: translateY(-1px);
}

[data-testid="stDialog"] {
    border-radius: 18px;
}

</style>
""", unsafe_allow_html=True)


# =====================================
# GOOGLE SHEET MASTER DATA
# =====================================
SHEET_URL = "https://docs.google.com/spreadsheets/d/1JZ5L-witlH_9E5ehJIMsRlXzrtP0BWXeg-qkFsx3XuE/export?format=csv"


@st.cache_data(ttl=300)
def load_master_data():
    df = pd.read_csv(SHEET_URL)
    return df.fillna("")


df_master = load_master_data()


# =====================================
# CONNECT GOOGLE SHEET
# =====================================
@st.cache_resource
def connect_gsheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            st.secrets["gcp_service_account"],
            scope
        )
    except:
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "service_account.json",
            scope
        )

    client = gspread.authorize(creds)
    return client


@st.cache_resource
def open_result_sheet():
    client_sheet = connect_gsheet()
    return client_sheet.open("Hasil PNT").sheet1


sheet_hasil = open_result_sheet()


# =====================================
# FUNCTIONS
# =====================================
def upload_to_cloudinary(uploaded_file):
    uploaded_file.seek(0)
    result = cloudinary.uploader.upload(
        uploaded_file,
        folder="PNT_UPLOAD"
    )
    return result["secure_url"]


def get_exif_data(uploaded_file):
    try:
        image = Image.open(uploaded_file)
        exif_data = image._getexif()

        if not exif_data:
            return None

        exif = {}

        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            exif[tag] = value

        return exif

    except:
        return None


def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1))
        * cos(radians(lat2))
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c

    return round(distance, 2)


# =====================================
# SESSION STATE
# =====================================
if "form_key" not in st.session_state:
    st.session_state.form_key = 0


# =====================================
# SUCCESS DIALOG
# =====================================
@st.dialog("Notifikasi")
def success_dialog():
    st.success("✅ Data berhasil disimpan!")

    st.markdown("""
    <div style="color:#111827;font-size:16px;margin-top:10px;">
        Data kunjungan salesman berhasil direcord ke sistem.
    </div>
    """, unsafe_allow_html=True)

    if st.button("OK"):
        st.session_state.form_key += 1
        st.rerun()


# =====================================
# HEADER
# =====================================
st.markdown('<div class="header-card">', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1.1, 4, 1.1])

with col1:
    st.markdown('<div class="logo-box">', unsafe_allow_html=True)
    if SIG_LOGO.exists():
        st.image(str(SIG_LOGO), width=95)
    else:
        st.warning("Logo SIG tidak ditemukan")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown("""
    <h1 class="header-title">FORM KUNJUNGAN SALESMAN</h1>
    <div class="header-subtitle">
        Sistem Monitoring Kunjungan Toko - PT Semen Baturaja Tbk
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown('<div class="logo-box">', unsafe_allow_html=True)
    if SMBR_LOGO.exists():
        st.image(str(SMBR_LOGO), width=95)
    else:
        st.warning("Logo SMBR tidak ditemukan")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)


# =====================================
# GET GEOLOCATION
# =====================================
location = streamlit_js_eval(
    js_expressions="""
    new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                resolve({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude
                })
            },
            (error) => {
                resolve(null)
            }
        )
    })
    """,
    key="get_location"
)

latitude = ""
longitude = ""
koordinat = ""
jarak_selisih = ""

if location:
    latitude = location.get("latitude", "")
    longitude = location.get("longitude", "")
    koordinat = f"{latitude}, {longitude}"


# =====================================
# SELECT ID TOKO
# =====================================
df_master["Toko Display"] = (
    df_master["ID Toko"].astype(str)
    + " - "
    + df_master["Nama Toko"].astype(str)
)

list_toko = [""] + df_master["Toko Display"].tolist()


st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">🏪 Data Toko</div>', unsafe_allow_html=True)

selected_toko = st.selectbox(
    "Cari ID / Nama Toko",
    list_toko,
    key=f"id_toko_{st.session_state.form_key}"
)


# =====================================
# GET STORE DATA
# =====================================
if selected_toko != "":
    id_toko = selected_toko.split(" - ")[0]

    data_toko = df_master[
        df_master["ID Toko"].astype(str) == id_toko
    ].iloc[0]

    nama_toko = data_toko["Nama Toko"]
    alamat = data_toko["Alamat"]
    distrik = data_toko["Distrik"]
    dist1 = data_toko["Distributor 1"]
    dist2 = data_toko["Distributor 2"]
    dist3 = data_toko["Distributor 3"]

    master_lat = float(data_toko["Latitude"])
    master_lon = float(data_toko["Longitude"])
    koordinat_toko = f"{master_lat}, {master_lon}"

    if latitude and longitude:
        try:
            jarak_selisih = calculate_distance(
                master_lat,
                master_lon,
                float(latitude),
                float(longitude)
            )
        except:
            jarak_selisih = ""

else:
    id_toko = ""
    nama_toko = ""
    alamat = ""
    distrik = ""
    dist1 = ""
    dist2 = ""
    dist3 = ""
    master_lat = 0
    master_lon = 0
    koordinat_toko = ""
    jarak_selisih = ""


st.text_input("Nama Toko", value=nama_toko, disabled=True)
st.text_input("Alamat Toko", value=alamat, disabled=True)
st.text_input("Distrik Toko", value=distrik, disabled=True)

col_d1, col_d2, col_d3 = st.columns(3)

with col_d1:
    st.text_input("Distributor 1", value=dist1, disabled=True)

with col_d2:
    st.text_input("Distributor 2", value=dist2, disabled=True)

with col_d3:
    st.text_input("Distributor 3", value=dist3, disabled=True)

st.text_input("Koordinat Toko", value=koordinat_toko, disabled=True)

st.markdown('</div>', unsafe_allow_html=True)


# =====================================
# DATA SALESMAN
# =====================================
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">👤 Data Salesman & Kunjungan</div>', unsafe_allow_html=True)

col_salesman, col_tanggal = st.columns(2)

with col_salesman:
    tso = st.text_input(
        "Nama Salesman",
        key=f"tso_{st.session_state.form_key}"
    )

with col_tanggal:
    tanggal = st.date_input(
        "Tanggal Kunjungan",
        value=date.today()
    )

st.text_input(
    "Koordinat Lokasi Saat Ini",
    value=koordinat,
    disabled=True
)

if jarak_selisih != "":
    st.info(f"Jarak dari titik toko: {jarak_selisih} meter")

st.markdown('</div>', unsafe_allow_html=True)


# =====================================
# FOTO KUNJUNGAN
# =====================================
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">📸 Bukti Kunjungan</div>', unsafe_allow_html=True)

st.info("Gunakan kamera HP langsung saat mengambil foto kunjungan.")

bukti = st.file_uploader(
    "Ambil Foto Kunjungan",
    type=["jpg", "jpeg", "png"],
    key=f"bukti_{st.session_state.form_key}",
    accept_multiple_files=False
)

st.markdown('</div>', unsafe_allow_html=True)


# =====================================
# SHARE OF WALLET
# =====================================
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">📊 Share of Wallet & Info Pesaing</div>', unsafe_allow_html=True)

st.caption("Isi estimasi porsi pembelian toko. Total SOW maksimal 100%.")

sow_sig = st.number_input(
    "SOW SIG (%)",
    min_value=0.0,
    max_value=100.0,
    step=1.0,
    key=f"sow_sig_{st.session_state.form_key}"
)

st.markdown("#### Data Pesaing")

col_p1a, col_p1b = st.columns([3, 1])
with col_p1a:
    info_pesaing_1 = st.text_input(
        "Info Pesaing 1",
        placeholder="Contoh: Conch / Tiga Roda / Merah Putih, harga, program, stok",
        key=f"info_pesaing_1_{st.session_state.form_key}"
    )
with col_p1b:
    sow_pesaing_1 = st.number_input(
        "SOW 1 (%)",
        min_value=0.0,
        max_value=100.0,
        step=1.0,
        key=f"sow_pesaing_1_{st.session_state.form_key}"
    )

col_p2a, col_p2b = st.columns([3, 1])
with col_p2a:
    info_pesaing_2 = st.text_input(
        "Info Pesaing 2",
        key=f"info_pesaing_2_{st.session_state.form_key}"
    )
with col_p2b:
    sow_pesaing_2 = st.number_input(
        "SOW 2 (%)",
        min_value=0.0,
        max_value=100.0,
        step=1.0,
        key=f"sow_pesaing_2_{st.session_state.form_key}"
    )

col_p3a, col_p3b = st.columns([3, 1])
with col_p3a:
    info_pesaing_3 = st.text_input(
        "Info Pesaing 3",
        key=f"info_pesaing_3_{st.session_state.form_key}"
    )
with col_p3b:
    sow_pesaing_3 = st.number_input(
        "SOW 3 (%)",
        min_value=0.0,
        max_value=100.0,
        step=1.0,
        key=f"sow_pesaing_3_{st.session_state.form_key}"
    )

col_p4a, col_p4b = st.columns([3, 1])
with col_p4a:
    info_pesaing_4 = st.text_input(
        "Info Pesaing 4",
        key=f"info_pesaing_4_{st.session_state.form_key}"
    )
with col_p4b:
    sow_pesaing_4 = st.number_input(
        "SOW 4 (%)",
        min_value=0.0,
        max_value=100.0,
        step=1.0,
        key=f"sow_pesaing_4_{st.session_state.form_key}"
    )

col_p5a, col_p5b = st.columns([3, 1])
with col_p5a:
    info_pesaing_5 = st.text_input(
        "Info Pesaing 5",
        key=f"info_pesaing_5_{st.session_state.form_key}"
    )
with col_p5b:
    sow_pesaing_5 = st.number_input(
        "SOW 5 (%)",
        min_value=0.0,
        max_value=100.0,
        step=1.0,
        key=f"sow_pesaing_5_{st.session_state.form_key}"
    )

total_sow = (
    sow_sig
    + sow_pesaing_1
    + sow_pesaing_2
    + sow_pesaing_3
    + sow_pesaing_4
    + sow_pesaing_5
)

st.progress(min(total_sow / 100, 1.0))

if total_sow < 100:
    st.warning(f"Total SOW saat ini {total_sow:.0f}%. Masih tersisa {100 - total_sow:.0f}%.")

elif total_sow == 100:
    st.success("Total SOW sudah 100%.")

else:
    st.error(f"Total SOW {total_sow:.0f}%. Tidak boleh lebih dari 100%.")

st.markdown('</div>', unsafe_allow_html=True)


# =====================================
# SUBMIT
# =====================================
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">💾 Simpan Data</div>', unsafe_allow_html=True)

if st.button("SIMPAN DATA KUNJUNGAN"):

    if id_toko == "":
        st.error("Silakan pilih ID Toko.")

    elif tso == "":
        st.error("Nama Salesman wajib diisi.")

    elif bukti is None:
        st.error("Bukti Kunjungan wajib diupload.")

    elif total_sow > 100:
        st.error("Total SOW tidak boleh lebih dari 100%.")

    else:
        exif = get_exif_data(bukti)

        if exif is None:
            st.error(
                "Foto tidak memiliki metadata EXIF. "
                "Gunakan kamera HP langsung."
            )
            st.stop()

        photo_time = exif.get("DateTime")

        if photo_time:
            try:
                photo_datetime = datetime.strptime(
                    photo_time,
                    "%Y:%m:%d %H:%M:%S"
                )

                now = datetime.now()
                diff_minutes = (now - photo_datetime).total_seconds() / 60

                if diff_minutes > 10:
                    st.error(
                        "Foto terlalu lama. "
                        "Ambil foto maksimal 10 menit terakhir."
                    )
                    st.stop()

            except:
                pass

        with st.spinner("Menyimpan data..."):

            try:
                link_file = upload_to_cloudinary(bukti)

                sheet_hasil.append_row([
                    str(id_toko),
                    str(nama_toko),
                    str(alamat),
                    str(distrik),
                    str(dist1),
                    str(dist2),
                    str(dist3),
                    str(tso),
                    str(tanggal),
                    str(koordinat_toko),
                    str(koordinat),
                    str(jarak_selisih),
                    str(link_file),
                    str(sow_sig),
                    str(info_pesaing_1),
                    str(sow_pesaing_1),
                    str(info_pesaing_2),
                    str(sow_pesaing_2),
                    str(info_pesaing_3),
                    str(sow_pesaing_3),
                    str(info_pesaing_4),
                    str(sow_pesaing_4),
                    str(info_pesaing_5),
                    str(sow_pesaing_5)
                ])

                success_dialog()

            except Exception as e:
                st.error(f"Terjadi error: {e}")

st.markdown('</div>', unsafe_allow_html=True)