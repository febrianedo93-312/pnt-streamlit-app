import streamlit as st
import pandas as pd
import gspread
import cloudinary
import cloudinary.uploader

from datetime import date
from datetime import datetime

from oauth2client.service_account import ServiceAccountCredentials

from PIL import Image
from PIL.ExifTags import TAGS

from streamlit_js_eval import streamlit_js_eval

from math import radians, sin, cos, sqrt, atan2


# =====================================
# PAGE CONFIG
# =====================================
st.set_page_config(
    page_title="PNT Form",
    layout="centered"
)


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

/* Background utama */
.stApp {
    background-color: #f3f4f6;
}

/* Container form */
.block-container {
    background-color: white;
    padding: 2.5rem;
    border-radius: 18px;
    box-shadow: 0 4px 18px rgba(0,0,0,0.08);
    max-width: 850px;
}

/* Judul */
h1 {
    color: #111827 !important;
    font-weight: 700 !important;
}

/* Sub heading */
h2, h3, h4, h5, h6 {
    color: #111827 !important;
}

/* Paragraph */
p {
    color: #6b7280;
}

/* Label field */
label {
    color: #374151 !important;
    font-weight: 700 !important;
    font-size: 15px !important;
}

/* Text input */
.stTextInput input {
    background-color: white !important;
    color: #111827 !important;
    border: 1px solid #d1d5db !important;
    border-radius: 10px !important;
}

/* Selectbox */
.stSelectbox div[data-baseweb="select"] {
    background-color: white !important;
    color: #111827 !important;
    border-radius: 10px !important;
}

/* Date input */
.stDateInput input {
    background-color: white !important;
    color: #111827 !important;
    border-radius: 10px !important;
}

/* Disabled autofill */
.stTextInput input:disabled {

    -webkit-text-fill-color: #111827 !important;
    color: #111827 !important;

    background-color: #eef2f7 !important;

    opacity: 1 !important;
}

/* Submit button */
.stButton > button {
    background-color: #009688;
    color: white !important;
    border-radius: 10px;
    height: 48px;
    width: 100%;
    font-size: 16px;
    font-weight: 700;
    border: none;
    transition: 0.3s;
}

/* Submit button text */
.stButton > button p {
    color: white !important;
    font-weight: 700 !important;
}

/* Hover button */
.stButton > button:hover {
    background-color: #00796b;
    color: white !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background-color: white;
    border-radius: 12px;
    border: 1px dashed #cbd5e1;
    padding: 1rem;
}

/* Dialog popup */
[data-testid="stDialog"] {
    border-radius: 18px;
}

/* Spinner */
[data-testid="stSpinner"] {
    color: #009688 !important;
}


</style>
""", unsafe_allow_html=True)


# =====================================
# GOOGLE SHEET MASTER DATA
# =====================================
SHEET_URL = "https://docs.google.com/spreadsheets/d/1JZ5L-witlH_9E5ehJIMsRlXzrtP0BWXeg-qkFsx3XuE/export?format=csv"


# =====================================
# LOAD MASTER DATA
# =====================================
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

        # STREAMLIT CLOUD
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            st.secrets["gcp_service_account"],
            scope
        )

    except:

        # LOCAL PC
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "service_account.json",
            scope
        )

    client = gspread.authorize(creds)

    return client


# =====================================
# OPEN RESULT SHEET
# =====================================
@st.cache_resource
def open_result_sheet():

    client_sheet = connect_gsheet()

    return client_sheet.open("Hasil PNT").sheet1


sheet_hasil = open_result_sheet()


# =====================================
# UPLOAD TO CLOUDINARY
# =====================================
def upload_to_cloudinary(uploaded_file):

    # RESET FILE POINTER
    uploaded_file.seek(0)

    result = cloudinary.uploader.upload(
        uploaded_file,
        folder="PNT_UPLOAD"
    )

    return result["secure_url"]


# =====================================
# GET EXIF DATA
# =====================================
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

# =====================================
# CALCULATE DISTANCE
# =====================================
def calculate_distance(lat1, lon1, lat2, lon2):

    R = 6371000  # meter

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
# FORM RESET KEY
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
    <div style="
        color:#111827;
        font-size:16px;
        margin-top:10px;
    ">
    Data PNT berhasil direcord ke sistem.
    </div>
    """, unsafe_allow_html=True)

    if st.button("OK"):

        st.session_state.form_key += 1

        st.rerun()


# =====================================
# TITLE
# =====================================
st.markdown("""
# Pemasangan Papan Nama Toko (PNT)

Silakan isi data pemasangan papan nama toko dengan lengkap dan benar.
""")

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

if location:

    latitude = location.get("latitude", "")
    longitude = location.get("longitude", "")
    
    koordinat = f"{latitude}, {longitude}"
    
    else:
    
        Koordinat = ""
    
    jarak_selisih = ""
# =====================================
# SELECT ID TOKO
# =====================================
df_master["Toko Display"] = (
    df_master["ID Toko"].astype(str)
    + " - "
    + df_master["Nama Toko"].astype(str)
)

list_toko = [""] + df_master["Toko Display"].tolist()

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
    
    # =====================================
    # CALCULATE DISTANCE
    # =====================================
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

    nama_toko = ""
    alamat = ""
    distrik = ""
    dist1 = ""
    dist2 = ""
    dist3 = ""
    koordinat_toko = ""
    
    master_lat = 0
    master_lon = 0



# =====================================
# AUTO FILL
# =====================================
st.text_input(
    "Nama Toko",
    value=nama_toko,
    disabled=True
)

st.text_input(
    "Alamat Toko",
    value=alamat,
    disabled=True
)

st.text_input(
    "Distrik Toko",
    value=distrik,
    disabled=True
)

st.text_input(
    "Nama Distributor 1",
    value=dist1,
    disabled=True
)

st.text_input(
    "Nama Distributor 2",
    value=dist2,
    disabled=True
)

st.text_input(
    "Nama Distributor 3",
    value=dist3,
    disabled=True)
    
st.text_input(
    "Latitude Toko",
    value=str(master_lat),
    disabled=True
)

st.text_input(
    "Longitude Toko",
    value=str(master_lon),
    disabled=True
)


# =====================================
# USER INPUT
# =====================================
tso = st.text_input(
    "Nama TSO",
    key=f"tso_{st.session_state.form_key}"
)

tanggal = st.date_input(
    "Tanggal Pemasangan",
    value=date.today()
)

st.info(
    "Gunakan kamera HP langsung saat mengambil foto pemasangan."
)

bukti = st.file_uploader(
    "Ambil Foto Pemasangan",
    type=["jpg", "jpeg", "png"],
    key=f"bukti_{st.session_state.form_key}",
    accept_multiple_files=False
)

# =====================================
# SHOW GEOLOCATION
# =====================================
st.text_input(
    "Koordinat Lokasi",
    value=koordinat,
    disabled=True
)

# =====================================
# SUBMIT BUTTON
# =====================================
if st.button("Submit"):

    # VALIDATION
    if id_toko == "":

        st.error("Silakan pilih ID Toko.")

    elif tso == "":

        st.error("Nama TSO wajib diisi.")

    elif bukti is None:

        st.error("Bukti pemasangan wajib diupload.")

    else:

        # =====================================
        # CHECK EXIF
        # =====================================
        exif = get_exif_data(bukti)

        if exif is None:

            st.error(
                "Foto tidak memiliki metadata EXIF. "
                "Gunakan kamera HP langsung."
            )

            st.stop()

        # =====================================
        # CHECK PHOTO TIME
        # =====================================
        photo_time = exif.get("DateTime")

        if photo_time:

            try:

                photo_datetime = datetime.strptime(
                    photo_time,
                    "%Y:%m:%d %H:%M:%S"
                )

                now = datetime.now()

                diff_minutes = (
                    now - photo_datetime
                ).total_seconds() / 60

                if diff_minutes > 10:

                    st.error(
                        "Foto terlalu lama. "
                        "Ambil foto maksimal 10 menit terakhir."
                    )

                    st.stop()

            except:
                pass

        # =====================================
        # SAVE PROCESS
        # =====================================
        with st.spinner("Menyimpan data..."):

            try:

                # UPLOAD FILE
                link_file = upload_to_cloudinary(bukti)

                # SAVE GOOGLE SHEET
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
                    str(link_file)
                ])

                # SUCCESS
                success_dialog()

            except Exception as e:

                st.error(f"Terjadi error: {e}")