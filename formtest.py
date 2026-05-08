import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import cloudinary
import cloudinary.uploader

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
# CUSTOM UI
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

/* File uploader modern */
[data-testid="stFileUploader"] {
    background-color: white;
    border-radius: 14px;
    border: 2px dashed #009688;
    padding: 1.2rem;
}

/* Upload button */
[data-testid="stFileUploader"] section button {
    background-color: #009688 !important;
    color: white !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    border: none !important;
}

/* Upload button hover */
[data-testid="stFileUploader"] section button:hover {
    background-color: #00796b !important;
}

/* Uploaded filename */
[data-testid="stFileUploaderFileName"] {
    color: #111827 !important;
    font-weight: 600;
}

</style>
""", unsafe_allow_html=True)

# =====================================
# GOOGLE SHEET MASTER DATA
# =====================================
SHEET_URL = "https://docs.google.com/spreadsheets/d/1JZ5L-witlH_9E5ehJIMsRlXzrtP0BWXeg-qkFsx3XuE/export?format=csv"

# =====================================
# GOOGLE DRIVE FOLDER ID
# =====================================
FOLDER_ID = "1U18yrzWhEeOqr_TdqLY9JbD-4y3Bqnfv"

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

        # STREAMLIT CLOUDs
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            st.secrets["gcp_service_account"],
            scope
        )

    except Exception:

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
# GOOGLE DRIVE AUTH
# =====================================

# =====================================
# UPLOAD FILE TO CLOUDINARY
# =====================================
def upload_to_drive(uploaded_file):

    result = cloudinary.uploader.upload(
        uploaded_file,
        folder="PNT_UPLOAD"
    )

    return result["secure_url"]    

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

    st.markdown("""
    <div style="
        background-color:#16a34a;
        padding:14px;
        border-radius:10px;
        color:white;
        font-weight:700;
        font-size:16px;
        margin-bottom:20px;
    ">
    ✅ Data berhasil disimpan!
    </div>

    <div style="
        color:white;
        font-size:18px;
        font-weight:700;
        margin-bottom:10px;
    ">
    Data PNT berhasil direcord ke sistem.
    </div>

    <div style="
        color:#d1d5db;
        font-size:15px;
        margin-bottom:20px;
    ">
    Silakan lanjutkan input toko berikutnya.
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
# SELECT ID TOKO
# =====================================
list_toko = [""] + df_master["ID Toko"].astype(str).tolist()

id_toko = st.selectbox(
    "ID Toko",
    list_toko,
    key=f"id_toko_{st.session_state.form_key}"
)

# =====================================
# GET STORE DATA
# =====================================
if id_toko != "":

    data_toko = df_master[
        df_master["ID Toko"].astype(str) == id_toko
    ].iloc[0]

    nama_toko = data_toko["Nama Toko"]
    alamat = data_toko["Alamat"]
    distrik = data_toko["Distrik"]
    dist1 = data_toko["Distributor 1"]
    dist2 = data_toko["Distributor 2"]
    dist3 = data_toko["Distributor 3"]

else:

    nama_toko = ""
    alamat = ""
    distrik = ""
    dist1 = ""
    dist2 = ""
    dist3 = ""

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
    "Pastikan papan nama toko terlihat jelas pada foto."
)

bukti = st.file_uploader(
    "Ambil / Upload Foto Pemasangan",
    type=["jpg", "jpeg", "png"],
    key=f"bukti_{st.session_state.form_key}",
    accept_multiple_files=False
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

        with st.spinner("Menyimpan data..."):

            try:

                # =====================================
                # UPLOAD FILE
                # =====================================
                link_file = upload_to_drive(bukti)

                # =====================================
                # SAVE TO GOOGLE SHEET
                # =====================================
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
                    str(link_file)
                ])

                # =====================================
                # SHOW SUCCESS DIALOG
                # =====================================
                success_dialog()

            except Exception as e:

                st.error(f"Terjadi error: {e}")