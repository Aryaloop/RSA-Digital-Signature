import streamlit as st
import qrcode
from PIL import Image
import io
import base64
# HAPUS IMPORT CV2 & NUMPY, GANTI DENGAN PYZBAR
from pyzbar.pyzbar import decode 
from streamlit_option_menu import option_menu

# LIBRARY KRIPTOGRAFI
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="RSA Digital Signature", layout="wide")

# --- CSS STYLING ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #ffffff !important; color: #2c3e50; }
    [data-testid="stSidebar"] { background-color: #f8f9fa !important; border-right: 1px solid #dee2e6; }
    .main-header { font-size: 2rem; font-weight: 700; color: #1e293b; margin-bottom: 1rem; }
    .stTextArea textarea { font-size: 1rem; }
    .stButton button { width: 100%; }
    
    .key-box {
        padding: 15px; border-radius: 10px; margin-bottom: 10px;
        font-family: monospace; font-size: 0.8rem;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# FUNGSI HELPER & UTAMA (DENGAN PREFIX arya20221310006_)
# ==============================================================================

def arya20221310006_scan_qr_image(uploaded_file):
    """
    Fungsi membaca QR Code menggunakan Pyzbar
    """
    try:
        # 1. Buka gambar langsung menggunakan PIL (Pillow)
        image = Image.open(uploaded_file)
        
        # 2. Decode menggunakan pyzbar
        decoded_objects = decode(image)
        
        # 3. Ambil data pertama yang ditemukan
        if decoded_objects:
            # Data dalam bentuk bytes, harus di-decode ke string
            return decoded_objects[0].data.decode("utf-8")
        else:
            return None
    except Exception as e:
        return None

def arya20221310006_generate_keys():
    """
    Fungsi membuat pasangan kunci RSA 2048-bit
    """
    key = RSA.generate(2048)
    private_key = key.export_key().decode()
    public_key = key.publickey().export_key().decode()
    return private_key, public_key

def arya20221310006_sign_data(data, private_key_str):
    """
    Fungsi untuk menandatangani data (Hashing -> Enkripsi Private Key)
    """
    try:
        key = RSA.import_key(private_key_str)
        if isinstance(data, str):
            data_bytes = data.encode('utf-8')
        else:
            data_bytes = data   
        h = SHA256.new(data_bytes)
        signature = pkcs1_15.new(key).sign(h)
        return base64.b64encode(signature).decode()
    except Exception as e:
        return None

def arya20221310006_verify_data(data, signature_b64, public_key_str):
    """
    Fungsi untuk memverifikasi tanda tangan (Dekripsi Public Key -> Bandingkan Hash)
    """
    try:
        key = RSA.import_key(public_key_str)
        if isinstance(data, str):
            data_bytes = data.encode('utf-8')
        else:
            data_bytes = data
        h = SHA256.new(data_bytes)
        signature = base64.b64decode(signature_b64)
        pkcs1_15.new(key).verify(h, signature)
        return True
    except (ValueError, TypeError):
        return False

# ==============================================================================
# MAIN PROGRAM (STREAMLIT UI)
# ==============================================================================

# --- SESSION STATE ---
if 'rsa_private' not in st.session_state:
    st.session_state['rsa_private'] = None
if 'rsa_public' not in st.session_state:
    st.session_state['rsa_public'] = None

# --- SIDEBAR NAVIGASI ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2092/2092663.png", width=50)
    st.markdown("### RSA Signer")
    
    selected = option_menu(
        menu_title=None,
        options=["1. Buat Kunci (Key Gen)", "2. Buat Signature (Sender)", "3. Verifikasi (Receiver)"],
        icons=["key", "pen-fill", "shield-check"],
        default_index=0,
        styles={"nav-link-selected": {"background-color": "#4F8BF9"}}
    )

# --- HALAMAN 1: GENERATE KEYS ---
if selected == "1. Buat Kunci (Key Gen)":
    st.markdown("<div class='main-header'>1. Generator Kunci RSA</div>", unsafe_allow_html=True)
    st.info("Klik tombol di bawah untuk membuat pasangan kunci (Private & Public).")
    
    if st.button("Generate Pasangan Kunci Baru", type="primary"):
        # MEMANGGIL FUNGSI DENGAN NAMA BARU
        priv, pub = arya20221310006_generate_keys()
        
        st.session_state['rsa_private'] = priv
        st.session_state['rsa_public'] = pub
        st.toast("Kunci baru berhasil dibuat!", icon="🔑")

    st.markdown("---")

    if st.session_state['rsa_private'] is not None:
        col1, col2 = st.columns(2)
        with col1:
            st.error("PRIVATE KEY (Simpan Kerahasiaan Ini!)")
            st.text_area("Preview Private Key", st.session_state['rsa_private'], height=200, label_visibility="collapsed")
            st.download_button("⬇ Unduh Private Key", st.session_state['rsa_private'], "private_key.pem", "text/plain", type="secondary")
            
        with col2:
            st.success("PUBLIC KEY (Bagikan ke Penerima)")
            st.text_area("Preview Public Key", st.session_state['rsa_public'], height=200, label_visibility="collapsed")
            st.download_button("⬇ Unduh Public Key", st.session_state['rsa_public'], "public_key.pem", "text/plain", type="secondary")
    else:
        st.caption("Belum ada kunci yang dibuat. Silakan klik tombol Generate di atas.")

# --- HALAMAN 2: SENDER (SIGNING & QR) ---
elif selected == "2. Buat Signature (Sender)":
    st.markdown("<div class='main-header'>2. Pengirim Pesan (Signing)</div>", unsafe_allow_html=True)
    
    col_input, col_result = st.columns([1, 1], gap="large")

    with col_input:
        input_type = st.radio("Jenis Input:", ["Pesan Teks", "Upload Dokumen"], horizontal=True)
        data_to_sign = None
        
        if input_type == "Pesan Teks":
            data_to_sign = st.text_area("Isi Pesan:", height=150, placeholder="Tulis pesan Anda di sini...")
        else:
            uploaded_doc = st.file_uploader("Upload Dokumen", type=['pdf', 'docx', 'txt', 'png', 'jpg'])
            if uploaded_doc:
                data_to_sign = uploaded_doc.getvalue()
                st.info(f"File '{uploaded_doc.name}' siap ditandatangani.")
        
        st.markdown("---")
        default_priv = st.session_state['rsa_private'] if st.session_state['rsa_private'] else ""
        private_key_input = st.text_area("Private Key:", value=default_priv, height=100, placeholder="Paste Private Key di sini...")
        generate_btn = st.button("Buat Digital Signature", type="primary")

    with col_result:
        if generate_btn:
            if not data_to_sign or not private_key_input:
                st.error("Data input atau Private Key belum lengkap!")
            else:
                # MEMANGGIL FUNGSI DENGAN NAMA BARU
                signature = arya20221310006_sign_data(data_to_sign, private_key_input)
                
                if signature:
                    st.success("Signature Berhasil Dibuat!")
                    qr = qrcode.QRCode(version=1, box_size=10, border=4)
                    qr.add_data(signature)
                    qr.make(fit=True)
                    img_qr = qr.make_image(fill_color="black", back_color="white")
                    
                    buf = io.BytesIO()
                    img_qr.save(buf, format="PNG")
                    byte_im = buf.getvalue()
                    
                    st.image(byte_im, caption="QRIS Digital Signature", width=250)
                    st.download_button("Unduh QR Code", byte_im, "signature_qr.png", "image/png")
                    with st.expander("Lihat String Signature"):
                        st.code(signature)
                else:
                    st.error("Gagal membuat signature. Periksa Private Key Anda.")

# --- HALAMAN 3: RECEIVER (VERIFICATION) ---
elif selected == "3. Verifikasi (Receiver)":
    st.markdown("<div class='main-header'>3. Penerima Pesan (Verifikasi)</div>", unsafe_allow_html=True)
    
    col_verify_L, col_verify_R = st.columns(2)
    
    with col_verify_L:
        st.subheader("1. Data yang Diterima")
        verify_type = st.radio("Jenis Data:", ["Pesan Teks", "Upload Dokumen"], horizontal=True, key="v_type")
        data_received = None
        
        if verify_type == "Pesan Teks":
            data_received = st.text_area("Paste Pesan di sini:", placeholder="Harus sama persis dengan pengirim...")
        else:
            uploaded_verify = st.file_uploader("Upload Dokumen Asli", type=['pdf', 'docx', 'txt', 'png', 'jpg'], key="v_doc")
            if uploaded_verify:
                data_received = uploaded_verify.getvalue()

    with col_verify_R:
        st.subheader("2. Validasi Signature")
        
        tab1, tab2 = st.tabs(["Upload QR", "Paste Text"])
        
        signature_to_process = None
        
        # TAB 1: UPLOAD QR (DENGAN PYZBAR)
        with tab1:
            qr_file = st.file_uploader("Upload Gambar QR Code", type=['png', 'jpg', 'jpeg'], key="v_qr")
            if qr_file:
                st.image(qr_file, width=150)
                
                # MEMANGGIL FUNGSI DENGAN NAMA BARU
                decoded_text = arya20221310006_scan_qr_image(qr_file)
                
                if decoded_text:
                    st.success("QR Code Berhasil Dibaca!")
                    st.caption("Signature Hash:")
                    st.code(decoded_text[:50] + "...", language="text") 
                    signature_to_process = decoded_text 
                else:
                    st.error("Gagal membaca QR. Pastikan gambar jelas.")
        
        # TAB 2: MANUAL PASTE
        with tab2:
            manual_text = st.text_input("Paste String Signature di sini:")
            if manual_text:
                signature_to_process = manual_text

        st.markdown("---")
        
        default_pub = st.session_state['rsa_public'] if st.session_state['rsa_public'] else ""
        public_key_input = st.text_area("3. Public Key Pengirim:", value=default_pub, height=100, placeholder="Paste Public Key...")
        
        if st.button("Verifikasi Keaslian", type="primary"):
            if data_received and signature_to_process and public_key_input:
                
                # MEMANGGIL FUNGSI DENGAN NAMA BARU
                is_valid = arya20221310006_verify_data(data_received, signature_to_process, public_key_input)
                
                if is_valid:
                    st.balloons()
                    st.success("VERIFIED! Dokumen/Pesan ASLI dan Tanda Tangan VALID.")
                else:
                    st.error("INVALID! Dokumen telah dimodifikasi atau Signature Palsu.")
            else:
                st.warning("Data belum lengkap. Pastikan Pesan, Signature, dan Public Key terisi.")