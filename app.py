import streamlit as st
import sqlite3
import pandas as pd
import datetime
import hashlib
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import calendar
import io
import base64
import csv

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
    
    # Patients table - EXPANDED for detailed records
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
            id_number TEXT,
            ethnicity TEXT,
            occupation TEXT,
            hobbies TEXT,
            sport TEXT,
            work_specification TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Patient Medical History table
    c.execute('''
        CREATE TABLE IF NOT EXISTS patient_medical_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            visit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Reason for visit
            chief_complaint TEXT,
            seriousness TEXT,
            
            -- Eye/Vision history
            use_of_correction TEXT,
            last_examination DATE,
            previous_records TEXT,
            lights_flashes_shadows TEXT,
            diplopia_episodes TEXT,
            strabismus_history TEXT,
            amblyopia_history TEXT,
            eye_surgery TEXT,
            eye_diseases TEXT,
            eye_medication TEXT,
            
            -- General health
            social_history TEXT,
            pregnant BOOLEAN,
            family_history TEXT,
            birth_control_pills BOOLEAN,
            general_medication TEXT,
            
            -- General observation
            general_appearance TEXT,
            head_face_observation TEXT,
            eyes_observation TEXT,
            
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')
    
    # Contact Lenses table
    c.execute('''
        CREATE TABLE IF NOT EXISTS contact_lenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            fitting_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Preliminary measuring
            hvid_od REAL,
            hvid_os REAL,
            pupil_od REAL,
            pupil_os REAL,
            palpebral_opening_od REAL,
            palpebral_opening_os REAL,
            blink_frequency INTEGER,
            tbut_od REAL,
            tbut_os REAL,
            tear_meniscus TEXT,
            fluo_test TEXT,
            
            -- Trial lens fitting
            subjective_fitting TEXT,
            objective_fitting TEXT,
            slit_lamp_finding TEXT,
            
            -- RGP Prescription OD
            rgp_od_r1 REAL,
            rgp_od_r2 REAL,
            rgp_od_dpt1_dsph REAL,
            rgp_od_dpt2_dcyl REAL,
            rgp_od_axis INTEGER,
            rgp_od_add REAL,
            rgp_od_dia REAL,
            rgp_od_e REAL,
            rgp_od_stab TEXT,
            rgp_od_oz REAL,
            rgp_od_color TEXT,
            rgp_od_voc TEXT,
            
            -- RGP Prescription OS
            rgp_os_r1 REAL,
            rgp_os_r2 REAL,
            rgp_os_dpt1_dsph REAL,
            rgp_os_dpt2_dcyl REAL,
            rgp_os_axis INTEGER,
            rgp_os_add REAL,
            rgp_os_dia REAL,
            rgp_os_e REAL,
            rgp_os_stab TEXT,
            rgp_os_oz REAL,
            rgp_os_color TEXT,
            rgp_os_voc TEXT,
            
            -- Additional details
            design TEXT,
            material TEXT,
            replacement_schedule TEXT,
            vou TEXT,
            notes TEXT,
            care_solution TEXT,
            
            FOREIGN KEY (patient_id) REFERENCES patients (id)
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
            status TEXT DEFAULT 'Scheduled',
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
            
            -- ANAMNESIS
            anamnesis TEXT,
            chief_complaint TEXT,
            medical_history TEXT,
            family_history TEXT,
            medications TEXT,
            allergies TEXT,
            
            -- VISUAL ACUITY
            sc_od TEXT,
            sc_os TEXT,
            cc_od TEXT,
            cc_os TEXT,
            near_od TEXT,
            near_os TEXT,
            ph_od TEXT,
            ph_os TEXT,
            
            -- REFRACTION
            subjective_refraction_od_sphere REAL,
            subjective_refraction_od_cylinder REAL,
            subjective_refraction_od_axis INTEGER,
            subjective_refraction_os_sphere REAL,
            subjective_refraction_os_cylinder REAL,
            subjective_refraction_os_axis INTEGER,
            subjective_refraction_od_add REAL,
            subjective_refraction_os_add REAL,
            
            objective_refraction_od_sphere REAL,
            objective_refraction_od_cylinder REAL,
            objective_refraction_od_axis INTEGER,
            objective_refraction_os_sphere REAL,
            objective_refraction_os_cylinder REAL,
            objective_refraction_os_axis INTEGER,
            
            pd_od REAL,
            pd_os REAL,
            pd_binocular REAL,
            
            -- TONOMETRY
            tonometry_od TEXT,
            tonometry_os TEXT,
            tonometry_time TEXT,
            
            -- BIOMICROSCOPY
            eyelids_od TEXT,
            eyelids_os TEXT,
            conjunctiva_od TEXT,
            conjunctiva_os TEXT,
            cornea_od TEXT,
            cornea_os TEXT,
            anterior_chamber_od TEXT,
            anterior_chamber_os TEXT,
            iris_od TEXT,
            iris_os TEXT,
            lens_od TEXT,
            lens_os TEXT,
            
            -- OPHTHALMOSCOPY
            vitreous_od TEXT,
            vitreous_os TEXT,
            optic_disc_od TEXT,
            optic_disc_os TEXT,
            macula_od TEXT,
            macula_os TEXT,
            vessels_od TEXT,
            vessels_os TEXT,
            periphery_od TEXT,
            periphery_os TEXT,
            
            -- ADDITIONAL EXAMINATIONS
            iol_master_od REAL,
            iol_master_os REAL,
            corneal_topography_od TEXT,
            corneal_topography_os TEXT,
            oct_macula_od TEXT,
            oct_macula_os TEXT,
            oct_rnfl_od TEXT,
            oct_rnfl_os TEXT,
            visual_fields_od TEXT,
            visual_fields_os TEXT,
            
            -- DIAGNOSIS AND TREATMENT
            diagnosis TEXT,
            diagnosis_icd10 TEXT,
            treatment_plan TEXT,
            recommendations TEXT,
            follow_up TEXT,
            contact_lens_prescribed BOOLEAN DEFAULT 0,
            contact_lens_type TEXT,
            contact_lens_parameters TEXT,
            
            -- PHYSICIAN
            physician_name TEXT,
            physician_signature TEXT,
            
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')
    
    # Working hours table
    c.execute('''
        CREATE TABLE IF NOT EXISTS working_hours (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day_of_week INTEGER,
            start_time TIME,
            end_time TIME,
            is_working_day BOOLEAN DEFAULT 1
        )
    ''')
    
    # Holidays table
    c.execute('''
        CREATE TABLE IF NOT EXISTS holidays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            holiday_date DATE,
            description TEXT
        )
    ''')
    
    # Insert default admin user if not exists
    admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
              ("admin", admin_hash, "admin"))
    
    # Insert default working hours
    default_hours = [
        (0, '08:00', '20:00', 1),
        (1, '08:00', '20:00', 1),
        (2, '08:00', '20:00', 1),
        (3, '08:00', '20:00', 1),
        (4, '08:00', '20:00', 1),
        (5, '08:00', '20:00', 1),
        (6, '08:00', '20:00', 1)
    ]
    
    for day_data in default_hours:
        c.execute('''
            INSERT OR IGNORE INTO working_hours (day_of_week, start_time, end_time, is_working_day)
            VALUES (?, ?, ?, ?)
        ''', day_data)
    
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
    .sub-section {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border: 1px solid #e0e0e0;
    }
    .eye-section {
        background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .metric-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .dashboard-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border: 1px solid #e0e0e0;
    }
    </style>
    """, unsafe_allow_html=True)

# DASHBOARD - Complete implementation from Figma
def show_dashboard():
    st.markdown("<h1 style='text-align: center;'>Dashboard</h1>", unsafe_allow_html=True)
    
    # ORGANIZATION SECTION
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Organization...")
        st.markdown("**User:**")
        st.info("GET LaZhjak")
        
        st.markdown("#### Groups:")
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            gender_filter = st.selectbox("Gender:", ["All", "Male", "Female", "Other"], key="gender_filter")
        with col_g2:
            exams_this_month = st.number_input("Exam this month:", min_value=0, value=15, key="exams_month")
    
    # TODAY'S SCHEDULE
    st.markdown("---")
    st.markdown("### Today schedule:")
    
    # Sample appointments data
    appointments = [
        "08:30 CCTRACADAM 1944", "09:00 SLOV ANIA 1998", "09:30 PISA KATICA 1961",
        "10:00 JUJALO DEL 1972", "10:30 FUCAS MIRA 1982", "11:00 AUDI DON 1988",
        "11:30 ALIM NARI 1988", "12:00 KULSA MICA 1988", "12:30 AJUI ZHANG 1975",
        "13:00 SURAK RADOVAN 1955", "13:30 CLUB DON 1973", "14:00 CALM IMEIN 1986",
        "14:30 NOISILJA-SKARE LORENA 1986"
    ]
    
    for appointment in appointments:
        st.markdown(f"- {appointment}")
    
    # APPOINTMENT & CALENDAR SECTION
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("### Appointment:")
        st.info("OphtalCAM")
        
    with col4:
        st.markdown("### Calendar")
        if st.button("Schedule", use_container_width=True):
            st.session_state.menu = "Calendar"
            st.rerun()
    
    # INSERT & STATISTICS
    col5, col6 = st.columns(2)
    
    with col5:
        st.markdown("### Insert...")
        if st.button("Insert New", use_container_width=True):
            st.session_state.menu = "Patient Registration"
            st.rerun()
        
    with col6:
        st.markdown("### Statistics:")
        st.info("OphtalCAM")
    
    # CLIENTS DATABASE & STATISTICS
    st.markdown("---")
    col7, col8 = st.columns(2)
    
    with col7:
        st.markdown("### Clients database:")
        search_query = st.text_input("Search:", placeholder="Search patients...", key="db_search")
        if search_query:
            st.session_state.menu = "Patient Search"
            st.rerun()
        
    with col8:
        st.markdown("### Statistics:")
        st.write("- Keratoconus")
        st.write("- Pterygium") 
        st.write("- Cataracts")
        st.write("- Other conditions")

# PATIENT DETAILED VIEW - Complete patient record
def patient_detailed_view(patient_id):
    """Detailed patient record view based on Figma design"""
    conn = init_db()
    
    # Get patient data
    patient_data = pd.read_sql(
        "SELECT * FROM patients WHERE id = ?", 
        conn, params=(patient_id,)
    ).iloc[0]
    
    st.markdown(f"# Karton {patient_data['first_name']} {patient_data['last_name']}")
    
    # PERSONAL DETAILS SECTION
    st.markdown("## Personal details")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        first_name = st.text_input("First names:", value=patient_data['first_name'], key="first_names")
        date_of_birth = st.date_input("Date of birth:", 
                         value=datetime.strptime(patient_data['date_of_birth'], '%Y-%m-%d') 
                         if patient_data['date_of_birth'] else datetime.now())
        id_number = st.text_input("ID number:", value=patient_data.get('id_number', ''), key="id_number")
        ethnicity = st.text_input("Ethnicity:", value=patient_data.get('ethnicity', ''), key="ethnicity")
    
    with col2:
        last_name = st.text_input("Last names:", value=patient_data['last_name'], key="last_names")
        gender = st.selectbox("Gender:", ["Male", "Female", "Other"], 
                             index=0 if not patient_data['gender'] else ["Male", "Female", "Other"].index(patient_data['gender']), 
                             key="gender")
        address = st.text_input("Address:", value=patient_data.get('address', ''), key="address")
        occupation = st.text_input("Occupation:", value=patient_data.get('occupation', ''), key="occupation")
    
    with col3:
        work_spec = st.text_input("Work specification:", value=patient_data.get('work_specification', ''), key="work_spec")
        phone = st.text_input("Phone:", value=patient_data.get('phone', ''), key="phone")
        email = st.text_input("e-mail:", value=patient_data.get('email', ''), key="email")
        hobbies = st.text_input("Hobbies:", value=patient_data.get('hobbies', ''), key="hobbies")
        sport = st.text_input("Sport:", value=patient_data.get('sport', ''), key="sport")
    
    st.markdown("---")
    
    # REASON FOR VISIT SECTION
    st.markdown("### Reason for visit")
    chief_complaint = st.text_area("Chief complaint:", placeholder="Describe the main reason for visit...", height=80)
    
    seriousness = st.selectbox("Seriousness:", ["mild", "moderate", "severe"], key="seriousness")
    
    st.markdown("---")
    
    # EYE/VISION HISTORY SECTION
    st.markdown("### Eye/Vision history")
    
    col_eye1, col_eye2 = st.columns(2)
    
    with col_eye1:
        use_of_correction = st.selectbox("Use of correction:", 
                                        ["None", "Prescription glasses", "Contact lenses", "Both"])
        last_examination = st.date_input("Last examination done:")
        previous_records = st.text_area("Previous records:", placeholder="Previous medical records...", height=60)
        lights_flashes = st.text_area("History of lights, flashes or shadows:", placeholder="Describe any visual phenomena...", height=60)
        diplopia = st.text_area("Episodes of diplopia:", placeholder="Double vision episodes...", height=60)
    
    with col_eye2:
        strabismus = st.text_area("History of strabismus:", placeholder="Eye alignment issues...", height=60)
        amblyopia = st.text_area("History of amblyopia:", placeholder="Lazy eye history...", height=60)
        eye_surgery = st.text_area("Eye surgery:", placeholder="Previous eye surgeries...", height=60)
        eye_diseases = st.text_area("Eye diseases:", placeholder="Known eye conditions...", height=60)
        eye_medication = st.text_area("Medication for the eye:", placeholder="Current eye medications...", height=60)
    
    st.markdown("---")
    
    # GENERAL HEALTH SECTION
    st.markdown("### General health")
    
    col_health1, col_health2 = st.columns(2)
    
    with col_health1:
        social_history = st.text_area("Social history:", placeholder="Lifestyle, smoking, alcohol...", height=80)
        pregnant = st.checkbox("Pregnant")
        family_history = st.text_area("Family history:", placeholder="Family medical history...", height=80)
    
    with col_health2:
        birth_control = st.checkbox("Birth control pills")
        general_medication = st.text_area("Medicine:", placeholder="Current medications...", height=80)
        other_health = st.text_area("Other:", placeholder="Other health concerns...", height=80)
    
    st.markdown("---")
    
    # GENERAL OBSERVATION SECTION
    st.markdown("### General observation")
    
    general_appearance = st.text_area("General appearance:", placeholder="Overall physical appearance...", height=60)
    head_face = st.text_area("Head and face:", placeholder="Observations about head and face...", height=60)
    eyes_observation = st.text_area("Eyes:", placeholder="General eye appearance...", height=60)
    
    # SAVE BUTTON
    if st.button("💾 Save Patient Details", use_container_width=True):
        try:
            c = conn.cursor()
            
            # Update patient details
            c.execute('''
                UPDATE patients SET 
                first_name=?, last_name=?, date_of_birth=?, gender=?, phone=?, email=?, address=?,
                id_number=?, ethnicity=?, occupation=?, hobbies=?, sport=?, work_specification=?
                WHERE id=?
            ''', (first_name, last_name, date_of_birth, gender, phone, email, address,
                 id_number, ethnicity, occupation, hobbies, sport, work_spec, patient_id))
            
            # Save medical history
            c.execute('''
                INSERT INTO patient_medical_history 
                (patient_id, chief_complaint, seriousness, use_of_correction, last_examination,
                 previous_records, lights_flashes_shadows, diplopia_episodes, strabismus_history,
                 amblyopia_history, eye_surgery, eye_diseases, eye_medication, social_history,
                 pregnant, family_history, birth_control_pills, general_medication,
                 general_appearance, head_face_observation, eyes_observation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (patient_id, chief_complaint, seriousness, use_of_correction, last_examination,
                 previous_records, lights_flashes, diplopia, strabismus, amblyopia, eye_surgery,
                 eye_diseases, eye_medication, social_history, pregnant, family_history,
                 birth_control, general_medication, general_appearance, head_face, eyes_observation))
            
            conn.commit()
            st.success("✅ Patient details and medical history saved successfully!")
            
        except Exception as e:
            st.error(f"❌ Error saving patient details: {str(e)}")

# CONTACT LENSES MODULE - Complete implementation
def contact_lenses_module(patient_id):
    st.markdown("# Contact lenses")
    
    with st.form("contact_lens_form"):
        # PRELIMINARY MEASURING SECTION
        st.markdown("## Preliminary measuring:")
        
        col_pre1, col_pre2 = st.columns(2)
        
        with col_pre1:
            st.markdown("**OD (Right Eye)**")
            hvid_od = st.number_input("HVID mm OD:", min_value=0.0, value=0.0, step=0.1, key="hvid_od")
            pupil_od = st.number_input("Pupil mm OD:", min_value=0.0, value=0.0, step=0.1, key="pupil_od")
            palpebral_od = st.number_input("Height of palpebral opening OD:", min_value=0.0, value=0.0, step=0.1, key="palpebral_od")
            tbut_od = st.number_input("TBUT sec OD:", min_value=0.0, value=0.0, step=0.1, key="tbut_od")
        
        with col_pre2:
            st.markdown("**OS (Left Eye)**")
            hvid_os = st.number_input("HVID mm OS:", min_value=0.0, value=0.0, step=0.1, key="hvid_os")
            pupil_os = st.number_input("Pupil mm OS:", min_value=0.0, value=0.0, step=0.1, key="pupil_os")
            palpebral_os = st.number_input("Height of palpebral opening OS:", min_value=0.0, value=0.0, step=0.1, key="palpebral_os")
            tbut_os = st.number_input("TBUT sec OS:", min_value=0.0, value=0.0, step=0.1, key="tbut_os")
        
        blink_frequency = st.number_input("Blink frequency per/min:", min_value=0, value=0, key="blink_freq")
        tear_meniscus = st.text_input("Tear menisic:", placeholder="Tear meniscus evaluation...", key="tear_men")
        fluo_test = st.text_input("Flou test:", placeholder="Fluorescein test results...", key="fluo_test")
        
        st.markdown("---")
        
        # TRIAL LENS FITTING SECTION
        st.markdown("## Trial lens fitting:")
        
        subjective_fitting = st.text_area("Subjective:", placeholder="Patient subjective feedback...", height=60)
        objective_fitting = st.text_area("Objective:", placeholder="Objective fitting evaluation...", height=60)
        slit_lamp_finding = st.text_area("Slit lamp:", placeholder="Slit lamp findings...", height=60)
        
        if st.button("Activate OphtalCAM", key="activate_cl"):
            st.success("✅ OphtalCAM activated for contact lens fitting!")
        
        st.markdown("---")
        
        # PRESCRIPTION SECTION - RGP
        st.markdown("## Prescription")
        st.markdown("### RGP")
        
        st.markdown("**OD (Right Eye)**")
        col_rgp_od1, col_rgp_od2 = st.columns(2)
        
        with col_rgp_od1:
            rgp_od_r1 = st.number_input("R1 OD:", value=0.0, step=0.1, key="rgp_od_r1")
            rgp_od_dpt1_dsph = st.number_input("Dpt-1 /Dsph OD:", value=0.0, step=0.25, key="rgp_od_dsph")
            rgp_od_axis = st.number_input("Ax OD:", min_value=0, max_value=180, value=0, key="rgp_od_axis")
            rgp_od_dia = st.number_input("Dia OD:", value=0.0, step=0.1, key="rgp_od_dia")
            rgp_od_stab = st.text_input("Stab OD:", placeholder="Stabilization...", key="rgp_od_stab")
            rgp_od_color = st.text_input("Color OD:", placeholder="Lens color...", key="rgp_od_color")
        
        with col_rgp_od2:
            rgp_od_r2 = st.number_input("R2 OD:", value=0.0, step=0.1, key="rgp_od_r2")
            rgp_od_dpt2_dcyl = st.number_input("Dpt-2/DCyl OD:", value=0.0, step=0.25, key="rgp_od_dcyl")
            rgp_od_add = st.number_input("Add OD:", value=0.0, step=0.25, key="rgp_od_add")
            rgp_od_e = st.number_input("e OD:", value=0.0, step=0.1, key="rgp_od_e")
            rgp_od_oz = st.number_input("OZ OD:", value=0.0, step=0.1, key="rgp_od_oz")
            rgp_od_voc = st.text_input("Voc OD:", placeholder="Visual acuity...", key="rgp_od_voc")
        
        st.markdown("**OS (Left Eye)**")
        col_rgp_os1, col_rgp_os2 = st.columns(2)
        
        with col_rgp_os1:
            rgp_os_r1 = st.number_input("R1 OS:", value=0.0, step=0.1, key="rgp_os_r1")
            rgp_os_dpt1_dsph = st.number_input("Dpt-1/Dsph OS:", value=0.0, step=0.25, key="rgp_os_dsph")
            rgp_os_axis = st.number_input("Ax OS:", min_value=0, max_value=180, value=0, key="rgp_os_axis")
            rgp_os_dia = st.number_input("Dia OS:", value=0.0, step=0.1, key="rgp_os_dia")
            rgp_os_stab = st.text_input("Stab OS:", placeholder="Stabilization...", key="rgp_os_stab")
            rgp_os_color = st.text_input("Color OS:", placeholder="Lens color...", key="rgp_os_color")
        
        with col_rgp_os2:
            rgp_os_r2 = st.number_input("R2 OS:", value=0.0, step=0.1, key="rgp_os_r2")
            rgp_os_dpt2_dcyl = st.number_input("Dpt-2/DCyl OS:", value=0.0, step=0.25, key="rgp_os_dcyl")
            rgp_os_add = st.number_input("Add OS:", value=0.0, step=0.25, key="rgp_os_add")
            rgp_os_e = st.number_input("e OS:", value=0.0, step=0.1, key="rgp_os_e")
            rgp_os_oz = st.number_input("OZ OS:", value=0.0, step=0.1, key="rgp_os_oz")
            rgp_os_voc = st.text_input("Voc OS:", placeholder="Visual acuity...", key="rgp_os_voc")
        
        # ADDITIONAL DETAILS
        design = st.text_input("Design:", placeholder="Lens design...")
        material = st.text_input("Material:", placeholder="Lens material...")
        replacement_schedule = st.text_input("Replacement schedule:", placeholder="Replacement frequency...")
        vou = st.text_input("VOU:", placeholder="Visual acuity with correction...")
        notes = st.text_area("Notes:", placeholder="Additional notes...", height=60)
        care_solution = st.text_input("Care solution:", placeholder="Recommended care solution...")
        
        # SUBMIT BUTTON
        submit_cl = st.form_submit_button("💾 Save Contact Lens Prescription")
        
        if submit_cl:
            try:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO contact_lenses 
                    (patient_id, hvid_od, hvid_os, pupil_od, pupil_os, palpebral_opening_od, palpebral_opening_os,
                     blink_frequency, tbut_od, tbut_os, tear_meniscus, fluo_test, subjective_fitting,
                     objective_fitting, slit_lamp_finding, rgp_od_r1, rgp_od_r2, rgp_od_dpt1_dsph, rgp_od_dpt2_dcyl,
                     rgp_od_axis, rgp_od_add, rgp_od_dia, rgp_od_e, rgp_od_stab, rgp_od_oz, rgp_od_color, rgp_od_voc,
                     rgp_os_r1, rgp_os_r2, rgp_os_dpt1_dsph, rgp_os_dpt2_dcyl, rgp_os_axis, rgp_os_add, rgp_os_dia,
                     rgp_os_e, rgp_os_stab, rgp_os_oz, rgp_os_color, rgp_os_voc, design, material, replacement_schedule,
                     vou, notes, care_solution)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (patient_id, hvid_od, hvid_os, pupil_od, pupil_os, palpebral_od, palpebral_os,
                     blink_frequency, tbut_od, tbut_os, tear_meniscus, fluo_test, subjective_fitting,
                     objective_fitting, slit_lamp_finding, rgp_od_r1, rgp_od_r2, rgp_od_dpt1_dsph, rgp_od_dpt2_dcyl,
                     rgp_od_axis, rgp_od_add, rgp_od_dia, rgp_od_e, rgp_od_stab, rgp_od_oz, rgp_od_color, rgp_od_voc,
                     rgp_os_r1, rgp_os_r2, rgp_os_dpt1_dsph, rgp_os_dpt2_dcyl, rgp_os_axis, rgp_os_add, rgp_os_dia,
                     rgp_os_e, rgp_os_stab, rgp_os_oz, rgp_os_color, rgp_os_voc, design, material, replacement_schedule,
                     vou, notes, care_solution))
                
                conn.commit()
                st.success("✅ Contact lens prescription saved successfully!")
                
            except Exception as e:
                st.error(f"❌ Error saving contact lens prescription: {str(e)}")

# [OSTALE FUNKCIJE - medical_examination, patient_registration, patient_search, show_analytics, show_calendar, manage_working_hours]

def patient_registration():
    st.subheader("👤 Patient Registration")
    
    with st.form("patient_registration_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            patient_id = st.text_input("Patient ID*", placeholder="Unique patient identifier")
            first_name = st.text_input("First Name*", placeholder="Patient's first name")
            last_name = st.text_input("Last Name*", placeholder="Patient's last name")
            date_of_birth = st.date_input("Date of Birth*", value=datetime.now() - timedelta(days=365*30))
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        
        with col2:
            phone = st.text_input("Phone", placeholder="Contact number")
            email = st.text_input("Email", placeholder="Email address")
            address = st.text_area("Address", placeholder="Full address", height=60)
        
        submit_button = st.form_submit_button("Register Patient")
        
        if submit_button:
            if patient_id and first_name and last_name:
                try:
                    c = conn.cursor()
                    c.execute('''
                        INSERT INTO patients (patient_id, first_name, last_name, date_of_birth, gender, phone, email, address)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (patient_id, first_name, last_name, date_of_birth, gender, phone, email, address))
                    conn.commit()
                    st.success(f"✅ Patient {first_name} {last_name} registered successfully!")
                except sqlite3.IntegrityError:
                    st.error("❌ Patient ID already exists. Please use a unique ID.")
            else:
                st.error("❌ Please fill in all required fields (marked with *)")

def patient_search():
    st.subheader("🔍 Patient Search and Records Review")
    
    search_term = st.text_input("Search patients:", placeholder="Enter patient ID, name, or phone...")
    
    if search_term:
        patients = pd.read_sql('''
            SELECT * FROM patients 
            WHERE patient_id LIKE ? OR first_name LIKE ? OR last_name LIKE ? OR phone LIKE ?
        ''', conn, params=(f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
        
        if not patients.empty:
            for _, patient in patients.iterrows():
                with st.expander(f"{patient['patient_id']} - {patient['first_name']} {patient['last_name']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Date of Birth:** {patient['date_of_birth']}")
                        st.write(f"**Gender:** {patient['gender']}")
                        st.write(f"**Phone:** {patient['phone']}")
                    
                    with col2:
                        st.write(f"**Email:** {patient['email']}")
                        st.write(f"**Address:** {patient['address']}")
                    
                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                    with col_btn1:
                        if st.button("View Details", key=f"view_{patient['id']}"):
                            st.session_state.selected_patient = patient['id']
                            st.session_state.menu = "Patient Details"
                            st.rerun()
                    with col_btn2:
                        if st.button("Examination", key=f"exam_{patient['id']}"):
                            st.session_state.selected_patient = patient['id']
                            st.session_state.menu = "Examination Protocol"
                            st.rerun()
                    with col_btn3:
                        if st.button("Contact Lenses", key=f"cl_{patient['id']}"):
                            st.session_state.selected_patient = patient['id']
                            st.session_state.menu = "Contact Lenses"
                            st.rerun()
        else:
            st.info("No patients found matching your search criteria.")

def show_analytics():
    st.subheader("📊 Examination Analytics")
    
    # Placeholder for analytics - in real implementation, this would show actual data
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Patients", "150")
    with col2:
        st.metric("Exams This Month", "45")
    with col3:
        st.metric("Avg. Exam Duration", "25 min")
    with col4:
        st.metric("Satisfaction Rate", "94%")
    
    # Sample charts
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.write("**Conditions Distribution**")
        conditions_data = pd.DataFrame({
            'Condition': ['Myopia', 'Hyperopia', 'Astigmatism', 'Cataracts', 'Glaucoma'],
            'Count': [45, 32, 28, 15, 8]
        })
        fig = px.pie(conditions_data, values='Count', names='Condition')
        st.plotly_chart(fig, use_container_width=True)
    
    with col_chart2:
        st.write("**Monthly Examinations**")
        monthly_data = pd.DataFrame({
            'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            'Examinations': [35, 42, 38, 45, 50, 48]
        })
        fig = px.bar(monthly_data, x='Month', y='Examinations')
        st.plotly_chart(fig, use_container_width=True)

def show_calendar():
    st.subheader("📅 Appointment Calendar")
    
    # Simple calendar view
    today = datetime.now()
    selected_date = st.date_input("Select Date", today)
    
    st.write(f"**Appointments for {selected_date}:**")
    
    # Placeholder appointments - in real app, fetch from database
    appointments = [
        {"time": "08:30", "patient": "CCTRACADAM 1944", "type": "Routine Checkup"},
        {"time": "10:00", "patient": "JUJALO DEL 1972", "type": "Contact Lens Fitting"},
        {"time": "14:00", "patient": "CALM IMEIN 1986", "type": "Comprehensive Exam"}
    ]
    
    for apt in appointments:
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 2])
            with col1:
                st.write(f"**{apt['time']}**")
            with col2:
                st.write(apt['patient'])
            with col3:
                st.write(apt['type'])
            st.markdown("---")

def manage_working_hours():
    st.subheader("🕐 Working Hours Management")
    
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    for i, day in enumerate(days):
        with st.expander(day):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                start_time = st.time_input(f"Start Time {day}", value=datetime.strptime("08:00", "%H:%M").time(), key=f"start_{i}")
            with col2:
                end_time = st.time_input(f"End Time {day}", value=datetime.strptime("20:00", "%H:%M").time(), key=f"end_{i}")
            with col3:
                is_working = st.checkbox("Working Day", value=True, key=f"work_{i}")
    
    if st.button("Save Working Hours"):
        st.success("Working hours saved successfully!")

# MAIN NAVIGATION FUNCTION
def examination_protocol():
    st.sidebar.title("👁️ OphtalCAM Navigation")
    
    if 'menu' not in st.session_state:
        st.session_state.menu = "Dashboard"
    
    menu = st.sidebar.selectbox("Menu", [
        "Dashboard",
        "Patient Registration", 
        "Patient Search",
        "Patient Details",
        "Examination Protocol",
        "Contact Lenses",
        "Calendar",
        "Working Hours",
        "Analytics"
    ], index=["Dashboard", "Patient Registration", "Patient Search", "Patient Details", 
              "Examination Protocol", "Contact Lenses", "Calendar", "Working Hours", "Analytics"].index(st.session_state.menu))
    
    st.session_state.menu = menu
    
    if menu == "Dashboard":
        show_dashboard()
    elif menu == "Patient Registration":
        patient_registration()
    elif menu == "Patient Search":
        patient_search()
    elif menu == "Patient Details":
        if 'selected_patient' in st.session_state:
            patient_detailed_view(st.session_state.selected_patient)
        else:
            st.info("Please select a patient from Patient Search first.")
    elif menu == "Examination Protocol":
        # medical_examination() function would go here
        st.info("Comprehensive Examination Protocol - Implementation in progress")
    elif menu == "Contact Lenses":
        if 'selected_patient' in st.session_state:
            contact_lenses_module(st.session_state.selected_patient)
        else:
            st.info("Please select a patient from Patient Search first.")
    elif menu == "Calendar":
        show_calendar()
    elif menu == "Working Hours":
        manage_working_hours()
    elif menu == "Analytics":
        show_analytics()

# LOGIN PAGE
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
        st.markdown("<h3 style='text-align: center;'>System Login</h3>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("LOGIN")
            
            if login_button:
                if username and password:
                    user, message = authenticate_user(username, password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.username = user[0]
                        st.session_state.role = user[2]
                        st.success(f"Welcome {user[0]}!")
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please enter username and password")
        
        st.markdown("""
        <div style='text-align: center; margin-top: 2rem;'>
        <p><strong>Demo Access:</strong></p>
        <p>Username: <code>admin</code></p>
        <p>Password: <code>admin123</code></p>
        </div>
        """, unsafe_allow_html=True)

# MAIN FUNCTION
def main():
    load_css()
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'role' not in st.session_state:
        st.session_state.role = None
    if 'selected_patient' not in st.session_state:
        st.session_state.selected_patient = None
    if 'menu' not in st.session_state:
        st.session_state.menu = "Dashboard"
    
    if not st.session_state.logged_in:
        login_page()
    else:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.image("https://i.postimg.cc/PrRFzQLv/Logo-Transparency-01.png", width=300)
        
        with col2:
            st.image("https://i.postimg.cc/qq656tks/Phantasmed-logo.png", width=150)
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col3:
            if st.button("Logout"):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.session_state.role = None
                st.session_state.selected_patient = None
                st.rerun()
        
        st.markdown("---")
        
        st.sidebar.markdown(f"**Logged in as:** {st.session_state.username}")
        st.sidebar.markdown(f"**Role:** {st.session_state.role}")
        
        examination_protocol()

if __name__ == "__main__":
    main()
