import streamlit as st
import sqlite3
import pandas as pd
import datetime
import hashlib
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import calendar

# Page configuration
st.set_page_config(
    page_title="OphtalCAM EMR",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Database setup
@st.cache_resource
def init_db():
    conn = sqlite3.connect('ophtalcam.db', check_same_thread=False)
    c = conn.cursor()
    
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expiry_date TIMESTAMP
        )
    ''')
    
    # Patients table
    c.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            date_of_birth DATE,
            gender TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Appointments table
    c.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            appointment_date TIMESTAMP,
            duration_minutes INTEGER,
            type TEXT,
            status TEXT DEFAULT 'Zakazano',
            notes TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')
    
    # Medical examinations table
    c.execute('''
        CREATE TABLE IF NOT EXISTS medical_examinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            visit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            anamneza TEXT,
            vizus_od_udaljenog_bez_corr_od TEXT,
            vizus_od_udaljenog_bez_corr_os TEXT,
            vizus_od_udaljenog_sa_corr_od TEXT,
            vizus_od_udaljenog_sa_corr_os TEXT,
            vizus_iz_bliza_od TEXT,
            vizus_iz_bliza_os TEXT,
            tonometrija_od TEXT,
            tonometrija_os TEXT,
            biomikroskopija_od TEXT,
            biomikroskopija_os TEXT,
            oftalmoskopija_od TEXT,
            oftalmoskopija_os TEXT,
            dijagnoza TEXT,
            tretman TEXT,
            refrakcija_obavljena BOOLEAN DEFAULT 0,
            kontaktne_lece_prepisane BOOLEAN DEFAULT 0,
            tip_kontaktnih_leca TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')
    
    # Insert default admin user if not exists
    admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
              ("admin", admin_hash, "admin"))
    
    conn.commit()
    return conn

# Initialize database
conn = init_db()

# Utility functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hash):
    return hash_password(password) == hash

def authenticate_user(username, password):
    conn = init_db()
    c = conn.cursor()
    
    c.execute("SELECT username, password_hash, role, expiry_date FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    
    if user and verify_password(password, user[1]):
        if user[3] and datetime.now() > datetime.strptime(user[3], '%Y-%m-%d %H:%M:%S.%f'):
            return None, "User account has expired"
        return user, "Success"
    return None, "Invalid credentials"

def create_user(username, password, role, expiry_days=None):
    conn = init_db()
    c = conn.cursor()
    
    expiry_date = None
    if expiry_days:
        expiry_date = datetime.now() + timedelta(days=expiry_days)
    
    password_hash = hash_password(password)
    
    try:
        c.execute("INSERT INTO users (username, password_hash, role, expiry_date) VALUES (?, ?, ?, ?)",
                  (username, password_hash, role, expiry_date))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

# Custom CSS for styling
def load_css():
    st.markdown("""
    <style>
    .main-header {
        background-color: #ffffff;
        padding: 1rem;
        margin-bottom: 0;
    }
    .login-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem;
    }
    .login-form {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stButton button {
        background-color: #1f77b4;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: 500;
    }
    .protocol-section {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #1f77b4;
    }
    .calendar-day {
        padding: 10px;
        border: 1px solid #e0e0e0;
        height: 120px;
        background-color: white;
    }
    .calendar-day.today {
        background-color: #e3f2fd;
        border: 2px solid #1f77b4;
    }
    .calendar-day.has-appointments {
        background-color: #fff3e0;
    }
    .appointment-badge {
        background-color: #1f77b4;
        color: white;
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 0.8em;
        margin: 1px;
    }
    .metric-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# Login page
def login_page():
    st.markdown("""
    <style>
    .main-header {
        background-color: #ffffff;
        padding: 1rem;
        margin-bottom: 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header with logos
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.image("https://i.postimg.cc/PrRFzQLv/Logo-Transparency-01.png", width=400)
    
    with col2:
        st.image("https://i.postimg.cc/qq656tks/Phantasmed-logo.png", width=250)
    
    st.markdown("---")
    
    # Login form
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h3 style='text-align: center;'>Prijava u sustav</h3>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Korisničko ime")
            password = st.text_input("Lozinka", type="password")
            login_button = st.form_submit_button("PRIJAVA")
            
            if login_button:
                if username and password:
                    user, message = authenticate_user(username, password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.username = user[0]
                        st.session_state.role = user[2]
                        st.success(f"Dobrodošli {user[0]}!")
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Unesite korisničko ime i lozinku")
        
        st.markdown("""
        <div style='text-align: center; margin-top: 2rem;'>
        <p><strong>Demo pristup:</strong></p>
        <p>Korisničko ime: <code>admin</code></p>
        <p>Lozinka: <code>admin123</code></p>
        </div>
        """, unsafe_allow_html=True)

# Calendar component
def show_calendar():
    st.subheader("Kalendar pregleda")
    
    # Initialize session state for calendar if not exists
    if 'current_month' not in st.session_state:
        st.session_state.current_month = datetime.now().month
        st.session_state.current_year = datetime.now().year
    
    # Month navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("◀ Prethodni mjesec"):
            st.session_state.current_month -= 1
            if st.session_state.current_month == 0:
                st.session_state.current_month = 12
                st.session_state.current_year -= 1
            st.rerun()
    
    with col2:
        month_name = ["Siječanj", "Veljača", "Ožujak", "Travanj", "Svibanj", "Lipanj",
                     "Srpanj", "Kolovoz", "Rujan", "Listopad", "Studeni", "Prosinac"][st.session_state.current_month - 1]
        st.markdown(f"<h3 style='text-align: center;'>{month_name} {st.session_state.current_year}</h3>", unsafe_allow_html=True)
    
    with col3:
        if st.button("Sljedeći mjesec ▶"):
            st.session_state.current_month += 1
            if st.session_state.current_month == 13:
                st.session_state.current_month = 1
                st.session_state.current_year += 1
            st.rerun()
    
    # Get appointments for the month
    conn = init_db()
    start_date = datetime(st.session_state.current_year, st.session_state.current_month, 1)
    if st.session_state.current_month == 12:
        end_date = datetime(st.session_state.current_year + 1, 1, 1)
    else:
        end_date = datetime(st.session_state.current_year, st.session_state.current_month + 1, 1)
    
    appointments = pd.read_sql(
        """SELECT a.appointment_date, p.first_name, p.last_name, a.type 
           FROM appointments a 
           JOIN patients p ON a.patient_id = p.id 
           WHERE a.appointment_date >= ? AND a.appointment_date < ? 
           ORDER BY a.appointment_date""", 
        conn, params=(start_date, end_date)
    )
    
    # Create calendar
    cal = calendar.monthcalendar(st.session_state.current_year, st.session_state.current_month)
    
    # Calendar header
    days = ["Pon", "Uto", "Sri", "Čet", "Pet", "Sub", "Ned"]
    cols = st.columns(7)
    for i, day in enumerate(days):
        cols[i].write(f"**{day}**")
    
    # Calendar days
    today = datetime.now().date()
    
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day != 0:
                    current_date = datetime(st.session_state.current_year, st.session_state.current_month, day).date()
                    day_appointments = appointments[
                        pd.to_datetime(appointments['appointment_date']).dt.date == current_date
                    ]
                    
                    # Day styling
                    day_class = "calendar-day"
                    if current_date == today:
                        day_class += " today"
                    if len(day_appointments) > 0:
                        day_class += " has-appointments"
                    
                    st.markdown(f'<div class="{day_class}">', unsafe_allow_html=True)
                    st.write(f"**{day}**")
                    
                    # Show appointments for the day
                    for _, appt in day_appointments.iterrows():
                        appt_time = pd.to_datetime(appt['appointment_date']).strftime('%H:%M')
                        patient_name = f"{appt['first_name']} {appt['last_name'][0]}."
                        st.markdown(f'<div class="appointment-badge" title="{appt["type"]}">{appt_time} {patient_name}</div>', unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="height: 120px;"></div>', unsafe_allow_html=True)
    
    # New appointment form
    st.markdown("---")
    st.subheader("Zakažite novi pregled")
    
    with st.form("appointment_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Patient selection
            patients_df = pd.read_sql("SELECT id, patient_id, first_name, last_name FROM patients", conn)
            if not patients_df.empty:
                patient_options = [f"{row['patient_id']} - {row['first_name']} {row['last_name']}" for _, row in patients_df.iterrows()]
                selected_patient = st.selectbox("Odaberite pacijenta*", [""] + patient_options)
            else:
                st.warning("Nema registriranih pacijenata")
                selected_patient = ""
            
            appointment_date = st.date_input("Datum pregleda*", min_value=datetime.now().date())
            appointment_time = st.time_input("Vrijeme pregleda*", value=datetime.now().time())
        
        with col2:
            duration = st.selectbox("Trajanje pregleda*", [15, 30, 45, 60, 90, 120], index=1)
            appointment_type = st.selectbox("Vrsta pregleda*", [
                "Redovni pregled", "Konsultacija", "Kontrola", "Hitni pregled", 
                "Operacija", "Laserski tretman", "Dijagnostika"
            ])
            notes = st.text_area("Napomene")
        
        submit_button = st.form_submit_button("ZAKAŽI PREGLED")
        
        if submit_button:
            if selected_patient and appointment_date and appointment_time:
                c = conn.cursor()
                
                # Extract patient ID
                patient_id_str = selected_patient.split(" - ")[0]
                
                # Get patient database ID
                c.execute("SELECT id FROM patients WHERE patient_id = ?", (patient_id_str,))
                result = c.fetchone()
                
                if result:
                    patient_db_id = result[0]
                    
                    # Combine date and time
                    appointment_datetime = datetime.combine(appointment_date, appointment_time)
                    
                    try:
                        c.execute('''
                            INSERT INTO appointments 
                            (patient_id, appointment_date, duration_minutes, type, notes)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (patient_db_id, appointment_datetime, duration, appointment_type, notes))
                        
                        conn.commit()
                        st.success("Pregled uspješno zakazan!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Greška pri zakazivanju: {str(e)}")
                else:
                    st.error("Pacijent nije pronađen u bazi podataka")
            else:
                st.error("Molimo popunite sva obavezna polja")

# Analytics dashboard
def show_analytics():
    st.subheader("Analitika pregleda")
    
    conn = init_db()
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Početni datum", datetime.now().replace(day=1))
    with col2:
        end_date = st.date_input("Završni datum", datetime.now())
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_patients = pd.read_sql("SELECT COUNT(*) as count FROM patients", conn).iloc[0]['count']
        st.markdown(f"""
        <div class="metric-card">
            <h3 style='margin: 0; color: #1f77b4;'>{total_patients}</h3>
            <p style='margin: 0;'>Ukupno pacijenata</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        total_examinations = pd.read_sql("SELECT COUNT(*) as count FROM medical_examinations", conn).iloc[0]['count']
        st.markdown(f"""
        <div class="metric-card">
            <h3 style='margin: 0; color: #1f77b4;'>{total_examinations}</h3>
            <p style='margin: 0;'>Ukupno pregleda</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        refrakcije_count = pd.read_sql(
            "SELECT COUNT(*) as count FROM medical_examinations WHERE refrakcija_obavljena = 1", 
            conn
        ).iloc[0]['count']
        st.markdown(f"""
        <div class="metric-card">
            <h3 style='margin: 0; color: #1f77b4;'>{refrakcije_count}</h3>
            <p style='margin: 0;'>Obavljenih refrakcija</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        kontaktne_lece_count = pd.read_sql(
            "SELECT COUNT(*) as count FROM medical_examinations WHERE kontaktne_lece_prepisane = 1", 
            conn
        ).iloc[0]['count']
        st.markdown(f"""
        <div class="metric-card">
            <h3 style='margin: 0; color: #1f77b4;'>{kontaktne_lece_count}</h3>
            <p style='margin: 0;'>Prepisanih kontaktnih leća</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Examinations by type (appointments)
        appointments_by_type = pd.read_sql(
            "SELECT type, COUNT(*) as count FROM appointments GROUP BY type", 
            conn
        )
        if not appointments_by_type.empty:
            fig = px.pie(appointments_by_type, values='count', names='type', 
                        title='Raspored pregleda po vrstama')
            st.plotly_chart(fig)
    
    with col2:
        # Monthly examinations trend
        monthly_exams = pd.read_sql("""
            SELECT DATE(visit_date) as date, COUNT(*) as count 
            FROM medical_examinations 
            GROUP BY DATE(visit_date)
        """, conn)
        if not monthly_exams.empty:
            monthly_exams['date'] = pd.to_datetime(monthly_exams['date'])
            fig = px.line(monthly_exams, x='date', y='count', 
                         title='Dnevni broj pregleda')
            st.plotly_chart(fig)
    
    # Contact lenses types
    contact_lens_types = pd.read_sql("""
        SELECT tip_kontaktnih_leca, COUNT(*) as count 
        FROM medical_examinations 
        WHERE kontaktne_lece_prepisane = 1 AND tip_kontaktnih_leca IS NOT NULL
        GROUP BY tip_kontaktnih_leca
    """, conn)
    
    if not contact_lens_types.empty:
        st.subheader("Tipovi prepisanih kontaktnih leća")
        fig = px.bar(contact_lens_types, x='tip_kontaktnih_leca', y='count',
                    title='Distribucija tipova kontaktnih leća')
        st.plotly_chart(fig)
    
    # Detailed statistics table
    st.subheader("Detaljna statistika")
    
    stats_data = pd.read_sql("""
        SELECT 
            COUNT(DISTINCT p.id) as ukupno_pacijenata,
            COUNT(me.id) as ukupno_pregleda,
            SUM(CASE WHEN me.refrakcija_obavljena = 1 THEN 1 ELSE 0 END) as refrakcije,
            SUM(CASE WHEN me.kontaktne_lece_prepisane = 1 THEN 1 ELSE 0 END) as kontaktne_lece,
            COUNT(DISTINCT a.id) as zakazani_pregledi
        FROM patients p
        LEFT JOIN medical_examinations me ON p.id = me.patient_id
        LEFT JOIN appointments a ON p.id = a.patient_id
    """, conn)
    
    st.dataframe(stats_data)

# Patient registration
def patient_registration():
    st.subheader("Registracija novog pacijenta")
    
    with st.form("patient_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            first_name = st.text_input("Ime*")
            last_name = st.text_input("Prezime*")
            date_of_birth = st.date_input("Datum rođenja*", max_value=datetime.now().date())
            gender = st.selectbox("Spol*", ["", "Muški", "Ženski"])
        
        with col2:
            phone = st.text_input("Telefon")
            email = st.text_input("Email")
            address = st.text_area("Adresa")
        
        submit_button = st.form_submit_button("Registriraj pacijenta")
        
        if submit_button:
            if first_name and last_name and date_of_birth and gender:
                conn = init_db()
                c = conn.cursor()
                
                # Generate patient ID
                patient_id = f"PT{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                try:
                    c.execute('''
                        INSERT INTO patients 
                        (patient_id, first_name, last_name, date_of_birth, gender, phone, email, address)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (patient_id, first_name, last_name, date_of_birth, gender, phone, email, address))
                    
                    conn.commit()
                    st.success(f"Pacijent uspješno registriran! ID pacijenta: {patient_id}")
                except Exception as e:
                    st.error(f"Greška pri registraciji: {str(e)}")
            else:
                st.error("Molimo popunite sva obavezna polja (označena sa *)")

# Medical examination
def medical_examination():
    st.subheader("Protokol oftalmološkog pregleda")
    
    # Odabir pacijenta
    conn = init_db()
    patients = pd.read_sql("SELECT id, patient_id, first_name, last_name FROM patients", conn)
    
    if patients.empty:
        st.warning("Nema registriranih pacijenata. Molimo prvo registrirajte pacijenta.")
        return
    
    patient_options = [f"{row['patient_id']} - {row['first_name']} {row['last_name']}" for _, row in patients.iterrows()]
    selected_patient = st.selectbox("Odaberite pacijenta*", [""] + patient_options)
    
    if not selected_patient:
        st.info("Odaberite pacijenta za nastavak pregleda")
        return
    
    with st.form("examination_form"):
        # 1. ANAMNESA
        st.markdown('<div class="protocol-section">', unsafe_allow_html=True)
        st.subheader("Anamneza")
        anamneza = st.text_area("Opis anamneze", placeholder="Unesite podatke iz anamneze...", height=100)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 2. VIZUS
        st.markdown('<div class="protocol-section">', unsafe_allow_html=True)
        st.subheader("Vizus")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**OD (Desno oko)**")
            vizus_od_udaljenog_bez_corr_od = st.text_input("Udaljeni bez korekcije OD", placeholder="npr. 0.8")
            vizus_od_udaljenog_sa_corr_od = st.text_input("Udaljeni sa korekcijom OD", placeholder="npr. 1.0")
            vizus_iz_bliza_od = st.text_input("Blizu OD", placeholder="npr. 0.8")
            
        with col2:
            st.write("**OS (Lijevo oko)**")
            vizus_od_udaljenog_bez_corr_os = st.text_input("Udaljeni bez korekcije OS", placeholder="npr. 0.6")
            vizus_od_udaljenog_sa_corr_os = st.text_input("Udaljeni sa korekcijom OS", placeholder="npr. 1.0")
            vizus_iz_bliza_os = st.text_input("Blizu OS", placeholder="npr. 0.6")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 3. TONOMETRIJA
        st.markdown('<div class="protocol-section">', unsafe_allow_html=True)
        st.subheader("Tonometrija")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("OphtalCAM Device")
            if st.button("OPHTHALCAM TONOMETRIJA", key="tono_od", use_container_width=True):
                st.info("OphtalCAM uređaj će se aktivirati u budućoj verziji")
            tonometrija_od = st.text_input("Vrijednost OD (mmHg)", placeholder="npr. 16")
            
        with col2:
            st.write("OphtalCAM Device") 
            if st.button("OPHTHALCAM TONOMETRIJA", key="tono_os", use_container_width=True):
                st.info("OphtalCAM uređaj će se aktivirati u budućoj verziji")
            tonometrija_os = st.text_input("Vrijednost OS (mmHg)", placeholder="npr. 17")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 4. BIOMIKROSKOPIJA
        st.markdown('<div class="protocol-section">', unsafe_allow_html=True)
        st.subheader("Biomikroskopija")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("OphtalCAM Device")
            if st.button("OPHTHALCAM BIOMIKROSKOPIJA", key="bio_od", use_container_width=True):
                st.info("OphtalCAM uređaj će se aktivirati u budućoj verziji")
            biomikroskopija_od = st.text_area("Nalaz OD", placeholder="Unesite nalaz biomikroskopije za desno oko...", height=100)
            
        with col2:
            st.write("OphtalCAM Device")
            if st.button("OPHTHALCAM BIOMIKROSKOPIJA", key="bio_os", use_container_width=True):
                st.info("OphtalCAM uređaj će se aktivirati u budućoj verziji")
            biomikroskopija_os = st.text_area("Nalaz OS", placeholder="Unesite nalaz biomikroskopije za lijevo oko...", height=100)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 5. OFTALMOSKOPIJA
        st.markdown('<div class="protocol-section">', unsafe_allow_html=True)
        st.subheader("Oftalmoskopija")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("OphtalCAM Device")
            if st.button("OPHTHALCAM OFTALMOSKOPIJA", key="oft_od", use_container_width=True):
                st.info("OphtalCAM uređaj će se aktivirati u budućoj verziji")
            oftalmoskopija_od = st.text_area("Nalaz OD", placeholder="Unesite nalaz oftalmoskopije za desno oko...", height=100)
            
        with col2:
            st.write("OphtalCAM Device")
            if st.button("OPHTHALCAM OFTALMOSKOPIJA", key="oft_os", use_container_width=True):
                st.info("OphtalCAM uređaj će se aktivirati u budućoj verziji")
            oftalmoskopija_os = st.text_area("Nalaz OS", placeholder="Unesite nalaz oftalmoskopije za lijevo oko...", height=100)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 6. DJIAGNOZA I TRETMAN
        st.markdown('<div class="protocol-section">', unsafe_allow_html=True)
        st.subheader("Dijagnoza i tretman")
        
        dijagnoza = st.text_area("Dijagnoza", placeholder="Unesite dijagnozu...", height=80)
        tretman = st.text_area("Preporučeni tretman", placeholder="Unesite preporučeni tretman...", height=80)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # DODATNA POLJA ZA ANALITIKU
        st.markdown('<div class="protocol-section">', unsafe_allow_html=True)
        st.subheader("Dodatni podaci za statistiku")
        
        col1, col2 = st.columns(2)
        
        with col1:
            refrakcija_obavljena = st.checkbox("Refrakcija obavljena")
        
        with col2:
            kontaktne_lece_prepisane = st.checkbox("Kontaktne leće prepisane")
            tip_kontaktnih_leca = ""
            if kontaktne_lece_prepisane:
                tip_kontaktnih_leca = st.selectbox("Tip kontaktnih leća", [
                    "Mekane dnevne", "Mekane mjesečne", "Mekane godišnje",
                    "Rigidne gas permeable", "Scleralne", "Terapijske",
                    "Kosmetičke", "Kustomizirane"
                ])
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SUBMIT BUTTON
        submit_button = st.form_submit_button("SPREMI PROTOKOL PREGLEDA", use_container_width=True)
        
        if submit_button:
            # Save to database
            patient_id_str = selected_patient.split(" - ")[0]
            c = conn.cursor()
            
            # Get patient database ID
            c.execute("SELECT id FROM patients WHERE patient_id = ?", (patient_id_str,))
            result = c.fetchone()
            
            if result:
                patient_db_id = result[0]
                
                try:
                    c.execute('''
                        INSERT INTO medical_examinations 
                        (patient_id, anamneza, vizus_od_udaljenog_bez_corr_od, vizus_od_udaljenog_bez_corr_os,
                         vizus_od_udaljenog_sa_corr_od, vizus_od_udaljenog_sa_corr_os, vizus_iz_bliza_od, vizus_iz_bliza_os,
                         tonometrija_od, tonometrija_os, biomikroskopija_od, biomikroskopija_os,
                         oftalmoskopija_od, oftalmoskopija_os, dijagnoza, tretman,
                         refrakcija_obavljena, kontaktne_lece_prepisane, tip_kontaktnih_leca)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (patient_db_id, anamneza, vizus_od_udaljenog_bez_corr_od, vizus_od_udaljenog_bez_corr_os,
                          vizus_od_udaljenog_sa_corr_od, vizus_od_udaljenog_sa_corr_os, vizus_iz_bliza_od, vizus_iz_bliza_os,
                          tonometrija_od, tonometrija_os, biomikroskopija_od, biomikroskopija_os,
                          oftalmoskopija_od, oftalmoskopija_os, dijagnoza, tretman,
                          refrakcija_obavljena, kontaktne_lece_prepisane, tip_kontaktnih_leca))
                    
                    conn.commit()
                    st.success("Protokol pregleda uspješno spremljen!")
                except Exception as e:
                    st.error(f"Greška pri spremanju: {str(e)}")
            else:
                st.error("Pacijent nije pronađen u bazi podataka")

# Patient search
def patient_search():
    st.subheader("Pretraga pacijenata i pregled kartona")
    
    conn = init_db()
    
    search_term = st.text_input("Pretraži pacijente (ime, prezime ili ID)")
    
    if search_term:
        patients = pd.read_sql(
            """SELECT * FROM patients 
               WHERE first_name LIKE ? OR last_name LIKE ? OR patient_id LIKE ?""", 
            conn, params=(f"%{search_term}%", f"%{search_term}%", f"%{search_term}%")
        )
        
        if not patients.empty:
            st.dataframe(patients)
            
            # Show medical history for selected patient
            selected_patient_id = st.selectbox("Odaberite pacijenta za detalje", 
                                             patients['patient_id'].tolist())
            
            if selected_patient_id:
                medical_history = pd.read_sql(
                    """SELECT * FROM medical_examinations me
                       JOIN patients p ON me.patient_id = p.id
                       WHERE p.patient_id = ?""", 
                    conn, params=(selected_patient_id,)
                )
                
                if not medical_history.empty:
                    st.subheader("Povijest pregleda")
                    st.dataframe(medical_history)
                else:
                    st.info("Nema zapisa o pregledima za ovog pacijenta")
        else:
            st.info("Nema pronađenih pacijenata")

# Dashboard
def show_dashboard():
    st.subheader("Klinički dashboard")
    
    # Quick stats
    conn = init_db()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        today = datetime.now().date()
        today_appointments = pd.read_sql(
            "SELECT COUNT(*) as count FROM appointments WHERE DATE(appointment_date) = ?", 
            conn, params=(today,)
        ).iloc[0]['count']
        st.metric("Današnji pregledi", today_appointments)
    
    with col2:
        total_patients = pd.read_sql("SELECT COUNT(*) as count FROM patients", conn).iloc[0]['count']
        st.metric("Pacijenati u sustavu", total_patients)
    
    with col3:
        upcoming_appointments = pd.read_sql(
            "SELECT COUNT(*) as count FROM appointments WHERE DATE(appointment_date) >= ?", 
            conn, params=(today,)
        ).iloc[0]['count']
        st.metric("Zakazani pregledi", upcoming_appointments)
    
    with col4:
        monthly_exams = pd.read_sql(
            "SELECT COUNT(*) as count FROM medical_examinations WHERE strftime('%Y-%m', visit_date) = strftime('%Y-%m', 'now')", 
            conn
        ).iloc[0]['count']
        st.metric("Pregledi ovaj mjesec", monthly_exams)
    
    # Quick links
    st.subheader("Brzi pristup")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Novi protokol pregleda", use_container_width=True):
            st.session_state.current_page = "Protokol pregleda"
    
    with col2:
        if st.button("Kalendar pregleda", use_container_width=True):
            st.session_state.current_page = "Kalendar"
    
    with col3:
        if st.button("Analitika", use_container_width=True):
            st.session_state.current_page = "Analitika"

# Main protocol examination page
def examination_protocol():
    st.sidebar.title("OphtalCAM Navigacija")
    menu = st.sidebar.selectbox("Izbornik", [
        "Početna",
        "Novi pacijent", 
        "Protokol pregleda",
        "Kalendar",
        "Pregled kartona",
        "Analitika"
    ])
    
    if menu == "Početna":
        show_dashboard()
    elif menu == "Novi pacijent":
        patient_registration()
    elif menu == "Protokol pregleda":
        medical_examination()
    elif menu == "Kalendar":
        show_calendar()
    elif menu == "Pregled kartona":
        patient_search()
    elif menu == "Analitika":
        show_analytics()

# Main application flow
def main():
    load_css()
    
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'role' not in st.session_state:
        st.session_state.role = None
    
    # Check login status
    if not st.session_state.logged_in:
        login_page()
    else:
        # Header with logos for main app
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.image("https://i.postimg.cc/PrRFzQLv/Logo-Transparency-01.png", width=300)
        
        with col2:
            st.image("https://i.postimg.cc/qq656tks/Phantasmed-logo.png", width=150)
        
        # Logout button
        col1, col2, col3 = st.columns([2, 1, 1])
        with col3:
            if st.button("Odjava"):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.session_state.role = None
                st.rerun()
        
        st.markdown("---")
        
        # Show user info
        st.sidebar.markdown(f"**Prijavljeni ste kao:** {st.session_state.username}")
        st.sidebar.markdown(f"**Uloga:** {st.session_state.role}")
        
        # Show examination protocol
        examination_protocol()

if __name__ == "__main__":
    main()
