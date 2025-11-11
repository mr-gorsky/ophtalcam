# app.py - OphtalCAM EMR (PROFESSIONAL MEDICAL VERSION)
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta, date
import calendar
import os
import json
import hashlib

st.set_page_config(page_title="OphtalCAM EMR", page_icon="👁️", layout="wide", initial_sidebar_state="collapsed")

# -----------------------
# Database init + auto-migration
# -----------------------
@st.cache_resource
def init_db():
    conn = sqlite3.connect('ophtalcam.db', check_same_thread=False)
    c = conn.cursor()

    # Users table with license info
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            license_expiry DATE,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Patients
    c.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            date_of_birth DATE NOT NULL,
            gender TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            id_number TEXT,
            emergency_contact TEXT,
            insurance_info TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Medical history
    c.execute('''
        CREATE TABLE IF NOT EXISTS medical_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            visit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            general_health TEXT,
            current_medications TEXT,
            allergies TEXT,
            headaches_history TEXT,
            family_history TEXT,
            ocular_history TEXT,
            previous_surgeries TEXT,
            eye_medications TEXT,
            last_eye_exam DATE,
            smoking_status TEXT,
            alcohol_consumption TEXT,
            occupation TEXT,
            hobbies TEXT,
            uploaded_reports TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')

    # Refraction exams - UPDATED WITH ADD/DEG AND DISTANCE
    c.execute('''
        CREATE TABLE IF NOT EXISTS refraction_exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            exam_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            habitual_type TEXT,
            habitual_od_va TEXT,
            habitual_od_modifier TEXT,
            habitual_os_va TEXT,
            habitual_os_modifier TEXT,
            habitual_binocular_va TEXT,
            habitual_binocular_modifier TEXT,
            habitual_pd TEXT,
            habitual_add_od TEXT,
            habitual_add_os TEXT,
            habitual_deg_od TEXT,
            habitual_deg_os TEXT,
            habitual_distance TEXT,
            vision_notes TEXT,
            uncorrected_od_va TEXT,
            uncorrected_od_modifier TEXT,
            uncorrected_os_va TEXT,
            uncorrected_os_modifier TEXT,
            uncorrected_binocular_va TEXT,
            uncorrected_binocular_modifier TEXT,
            objective_method TEXT,
            objective_time TEXT,
            autorefractor_od_sphere REAL,
            autorefractor_od_cylinder REAL,
            autorefractor_od_axis INTEGER,
            autorefractor_os_sphere REAL,
            autorefractor_os_cylinder REAL,
            autorefractor_os_axis INTEGER,
            objective_notes TEXT,
            cycloplegic_used BOOLEAN,
            cycloplegic_agent TEXT,
            cycloplegic_lot TEXT,
            cycloplegic_expiry DATE,
            cycloplegic_drops INTEGER,
            subjective_method TEXT,
            subjective_od_sphere REAL,
            subjective_od_cylinder REAL,
            subjective_od_axis INTEGER,
            subjective_od_va TEXT,
            subjective_od_modifier TEXT,
            subjective_add_od TEXT,
            subjective_deg_od TEXT,
            subjective_os_sphere REAL,
            subjective_os_cylinder REAL,
            subjective_os_axis INTEGER,
            subjective_os_va TEXT,
            subjective_os_modifier TEXT,
            subjective_add_os TEXT,
            subjective_deg_os TEXT,
            subjective_distance TEXT,
            subjective_notes TEXT,
            binocular_balance TEXT,
            stereopsis TEXT,
            near_point_convergence_break TEXT,
            near_point_convergence_recovery TEXT,
            final_prescribed_od_sphere REAL,
            final_prescribed_od_cylinder REAL,
            final_prescribed_od_axis INTEGER,
            final_prescribed_os_sphere REAL,
            final_prescribed_os_cylinder REAL,
            final_prescribed_os_axis INTEGER,
            final_prescribed_binocular_va TEXT,
            final_prescribed_binocular_modifier TEXT,
            final_add_od TEXT,
            final_add_os TEXT,
            final_deg_od TEXT,
            final_deg_os TEXT,
            final_distance TEXT,
            bvp TEXT,
            pinhole TEXT,
            prescription_notes TEXT,
            binocular_tests TEXT,
            functional_tests TEXT,
            accommodation_tests TEXT,
            uploaded_files TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')

    # Functional tests
    c.execute('''
        CREATE TABLE IF NOT EXISTS functional_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            test_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            motility TEXT,
            hirschberg TEXT,
            cover_test_distance TEXT,
            cover_test_near TEXT,
            pupils TEXT,
            rapd TEXT,
            confrontation_fields TEXT,
            other_notes TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')

    # Anterior segment (COMPLETE with tonometry and pachymetry)
    c.execute('''
        CREATE TABLE IF NOT EXISTS anterior_segment_exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            exam_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            biomicroscopy_od TEXT,
            biomicroscopy_os TEXT,
            biomicroscopy_notes TEXT,
            anterior_chamber_depth_od TEXT,
            anterior_chamber_depth_os TEXT,
            anterior_chamber_volume_od TEXT,
            anterior_chamber_volume_os TEXT,
            iridocorneal_angle_od TEXT,
            iridocorneal_angle_os TEXT,
            pachymetry_od REAL,
            pachymetry_os REAL,
            tonometry_type TEXT,
            tonometry_time TEXT,
            tonometry_compensation TEXT,
            tonometry_od TEXT,
            tonometry_os TEXT,
            aberometry_notes TEXT,
            corneal_topography_notes TEXT,
            anterior_segment_notes TEXT,
            pupillography_results TEXT,
            pupillography_notes TEXT,
            pupillography_files TEXT,
            uploaded_files TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')

    # Posterior segment - UPDATED FOR IMAGES
    c.execute('''
        CREATE TABLE IF NOT EXISTS posterior_segment_exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            exam_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fundus_exam_type TEXT,
            fundus_od TEXT,
            fundus_os TEXT,
            fundus_notes TEXT,
            oct_macula_od TEXT,
            oct_macula_os TEXT,
            oct_rnfl_od TEXT,
            oct_rnfl_os TEXT,
            oct_notes TEXT,
            posterior_segment_notes TEXT,
            uploaded_files TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')

    # Contact lenses table - UPDATED WITH ADD AND DESIGN OPTIONS
    c.execute('''
        CREATE TABLE IF NOT EXISTS contact_lens_prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            prescription_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            lens_type TEXT NOT NULL,
            lens_design TEXT,
            lens_material TEXT,
            lens_color TEXT,
            soft_brand TEXT,
            soft_base_curve REAL,
            soft_diameter REAL,
            soft_power_od_sphere REAL,
            soft_power_od_cylinder REAL,
            soft_power_od_axis INTEGER,
            soft_add_od TEXT,
            soft_power_os_sphere REAL,
            soft_power_os_cylinder REAL,
            soft_power_os_axis INTEGER,
            soft_add_os TEXT,
            rgp_base_curve REAL,
            rgp_diameter REAL,
            rgp_power_od_sphere REAL,
            rgp_power_od_cylinder REAL,
            rgp_power_od_axis INTEGER,
            rgp_add_od TEXT,
            rgp_power_os_sphere REAL,
            rgp_power_os_cylinder REAL,
            rgp_power_os_axis INTEGER,
            rgp_add_os TEXT,
            scleral_diameter TEXT,
            scleral_power_od_sphere REAL,
            scleral_power_od_cylinder REAL,
            scleral_power_od_axis INTEGER,
            scleral_add_od TEXT,
            scleral_power_os_sphere REAL,
            scleral_power_os_cylinder REAL,
            scleral_power_os_axis INTEGER,
            scleral_add_os TEXT,
            ortho_k_parameters TEXT,
            wearing_schedule TEXT,
            care_solution TEXT,
            follow_up_date DATE,
            fitting_notes TEXT,
            professional_assessment TEXT,
            patient_feedback TEXT,
            fitting_images TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')

    # Groups, appointments
    c.execute('''
        CREATE TABLE IF NOT EXISTS patient_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS patient_group_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            group_id INTEGER NOT NULL,
            assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id),
            FOREIGN KEY (group_id) REFERENCES patient_groups (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            appointment_date TIMESTAMP NOT NULL,
            duration_minutes INTEGER DEFAULT 30,
            appointment_type TEXT,
            status TEXT DEFAULT 'Scheduled',
            notes TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')

    # Default admin + groups
    try:
        admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT OR IGNORE INTO users (username, password_hash, role, license_expiry) VALUES (?, ?, ?, ?)", 
                 ("admin", admin_hash, "admin", date(2025, 12, 31)))
    except Exception:
        pass
        
    default_groups = [
        ("Corneal Ectasias", "Keratoconus, Pellucid Marginal Degeneration, Post-LASIK Ectasia"),
        ("Glaucoma", "Primary open-angle glaucoma, Angle-closure glaucoma, Secondary glaucoma"),
        ("Cataracts", "Nuclear, Cortical, Posterior Subcapsular, Congenital cataracts"),
        ("Retinal Diseases", "AMD, Diabetic retinopathy, Retinal detachment, Macular diseases"),
        ("Contact Lens Patients", "All patients using contact lenses"),
        ("Pediatric Ophthalmology", "Children eye conditions, Amblyopia, Strabismus"),
        ("Dry Eye Syndrome", "Aqueous deficient, Evaporative dry eye, MGD"),
        ("Neuro-ophthalmology", "Optic neuritis, Papilledea, Cranial nerve palsies")
    ]
    for g, d in default_groups:
        try:
            c.execute("INSERT OR IGNORE INTO patient_groups (group_name, description) VALUES (?, ?)", (g, d))
        except Exception:
            pass

    conn.commit()
    return conn

# init
conn = init_db()

# -----------------------
# Utilities
# -----------------------
def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def verify_password(pw, h):
    return hash_password(pw) == h

def authenticate_user(username, password):
    conn = init_db()
    c = conn.cursor()
    c.execute("SELECT username, password_hash, role FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    if user and verify_password(password, user[1]):
        return user, "Success"
    return None, "Invalid credentials"

def get_todays_appointments():
    conn = init_db()
    today = date.today()
    try:
        appointments = pd.read_sql('''
            SELECT a.*, p.first_name, p.last_name, p.patient_id 
            FROM appointments a 
            JOIN patients p ON a.patient_id = p.id 
            WHERE DATE(a.appointment_date) = ? 
            ORDER BY a.appointment_date
        ''', conn, params=(today,))
        return appointments
    except Exception:
        return pd.DataFrame()

def get_patient_stats():
    conn = init_db()
    try:
        total_patients = pd.read_sql("SELECT COUNT(*) as count FROM patients", conn).iloc[0]['count']
        today = date.today()
        today_exams = pd.read_sql('SELECT COUNT(*) as count FROM appointments WHERE DATE(appointment_date) = ?', conn, params=(today,)).iloc[0]['count']
        total_cl = pd.read_sql("SELECT COUNT(*) as count FROM contact_lens_prescriptions", conn).iloc[0]['count']
        return total_patients, today_exams, total_cl
    except Exception as e:
        return 0, 0, 0

def check_license_expiry():
    """Check if license is expired"""
    conn = init_db()
    try:
        result = pd.read_sql("SELECT license_expiry FROM users WHERE username = ?", 
                           conn, params=(st.session_state.username,))
        if not result.empty:
            expiry_date = pd.to_datetime(result.iloc[0]['license_expiry']).date()
            if expiry_date < date.today():
                st.error("LICENSE EXPIRED! Please contact administrator.")
                return False
            elif (expiry_date - date.today()).days <= 30:
                st.warning(f"License expires in {(expiry_date - date.today()).days} days")
            return True
    except Exception:
        pass
    return True

# Professional CSS
def load_css():
    st.markdown("""
    <style>
    .main-header {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #1e3c72;
        border-bottom: 2px solid #1e3c72;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    .metric-card { 
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
        color: white; 
        padding: 1.5rem; 
        border-radius: 8px; 
        text-align: center; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .exam-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #1e3c72;
        margin-bottom: 1.5rem;
    }
    .eye-column {
        background: white;
        padding: 1rem;
        border-radius: 6px;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
    }
    .professional-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
    }
    .professional-table th, .professional-table td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }
    .professional-table th {
        background-color: #1e3c72;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# -----------------------
# PROFESSIONAL DASHBOARD
# -----------------------
def show_dashboard():
    st.markdown("<h1 class='main-header'>OphtalCAM Clinical Dashboard</h1>", unsafe_allow_html=True)
    
    # Check license
    check_license_expiry()
    
    # Professional quick actions
    col_actions = st.columns(4)
    with col_actions[0]:
        if st.button("New Patient", use_container_width=True, key="new_pat_dash"):
            st.session_state.menu = "Patient Registration"
            st.rerun()
    with col_actions[1]:
        if st.button("Patient Search", use_container_width=True, key="search_dash"):
            st.session_state.menu = "Patient Search"
            st.rerun()
    with col_actions[2]:
        if st.button("New Appointment", use_container_width=True, key="new_appt_dash"):
            st.session_state.menu = "Schedule Appointment"
            st.rerun()
    with col_actions[3]:
        if st.button("Begin Examination", use_container_width=True, key="begin_exam_dash"):
            st.session_state.menu = "Patient Search"
            st.info("Please select a patient first")
            st.rerun()

    # Stats
    total_patients, today_exams, total_cl = get_patient_stats()
    col_metrics = st.columns(3)
    with col_metrics[0]:
        st.markdown(f"<div class='metric-card'><div style='font-size:24px'>{total_patients}</div><div>Registered Patients</div></div>", unsafe_allow_html=True)
    with col_metrics[1]:
        st.markdown(f"<div class='metric-card'><div style='font-size:24px'>{today_exams}</div><div>Today's Appointments</div></div>", unsafe_allow_html=True)
    with col_metrics[2]:
        st.markdown(f"<div class='metric-card'><div style='font-size:24px'>{total_cl}</div><div>Contact Lens Fittings</div></div>", unsafe_allow_html=True)

    col_main = st.columns([2, 1])
    
    with col_main[0]:
        st.subheader("Today's Clinical Schedule")
        appts = get_todays_appointments()
        if not appts.empty:
            for idx, apt in appts.iterrows():
                t = pd.to_datetime(apt['appointment_date']).strftime('%H:%M')
                with st.container():
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.markdown(f"**{t}** - {apt['first_name']} {apt['last_name']} ({apt['patient_id']})")
                        st.caption(f"{apt['appointment_type']} | {apt['status']}")
                    with col_b:
                        if st.button("Begin Exam", key=f"begin_{apt['id']}", use_container_width=True):
                            st.session_state.selected_patient = apt['patient_id']
                            st.session_state.menu = "Examination Protocol"
                            st.session_state.exam_step = "medical_history"
                            st.rerun()
        else:
            st.info("No appointments scheduled for today.")

    with col_main[1]:
        st.subheader("Calendar")
        today = datetime.now()
        
        # Current month calendar
        cal = calendar.monthcalendar(today.year, today.month)
        st.write(f"**{today.strftime('%B %Y')}**")
        
        # Day headers
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        header_cols = st.columns(7)
        for i, day in enumerate(days):
            header_cols[i].write(f"**{day}**")
        
        # Calendar days
        for week in cal:
            week_cols = st.columns(7)
            for i, day in enumerate(week):
                if day == 0:
                    week_cols[i].write("")
                else:
                    day_str = str(day)
                    if day == today.day:
                        week_cols[i].markdown(f"<div style='background:#1e3c72;color:white;border-radius:50%;width:30px;height:30px;display:flex;align-items:center;justify-content:center;margin:0 auto;'><strong>{day_str}</strong></div>", unsafe_allow_html=True)
                    else:
                        week_cols[i].write(day_str)
        
        st.markdown("---")
        st.subheader("Quick Links")
        if st.button("Clinical Analytics", use_container_width=True):
            st.session_state.menu = "Clinical Analytics"
            st.rerun()
        if st.button("Contact Lenses", use_container_width=True):
            st.session_state.menu = "Contact Lenses"
            st.rerun()
        if st.button("System Settings", use_container_width=True) and st.session_state.role == "admin":
            st.session_state.menu = "System Settings"
            st.rerun()

# -----------------------
# EXAMINATION PROTOCOL FLOW WITH IMPROVED LAYOUT
# -----------------------
def medical_history():
    st.markdown("<h2 class='main-header'>1. Comprehensive Medical History</h2>", unsafe_allow_html=True)
    if 'selected_patient' not in st.session_state or not st.session_state.selected_patient:
        st.error("No patient selected.")
        return
    
    pid = st.session_state.selected_patient
    try:
        pinfo = pd.read_sql("SELECT * FROM patients WHERE patient_id = ?", conn, params=(pid,)).iloc[0]
        st.markdown(f"### Patient: {pinfo['first_name']} {pinfo['last_name']} (ID: {pinfo['patient_id']})")
    except Exception:
        st.error("Patient not found.")
        return
    
    with st.form("mh_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### General Health")
            general_health = st.text_area("General health status", height=100)
            current_medications = st.text_area("Current medications", height=80)
            allergies = st.text_area("Allergies", height=80)
            headaches = st.text_area("Headaches / Migraines", height=80)
            
        with col2:
            st.markdown("#### History")
            family_history = st.text_area("Family medical history", height=100)
            ocular_history = st.text_area("Ocular history", height=80)
            previous_surgeries = st.text_area("Previous surgeries", height=60)
            last_eye_exam = st.date_input("Last eye exam", value=None)
        
        st.markdown("#### Social / Lifestyle")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            smoking = st.selectbox("Smoking status", ["Non-smoker", "Former", "Current", "Unknown"])
            alcohol = st.selectbox("Alcohol consumption", ["None", "Occasional", "Moderate", "Heavy"])
        with col_s2:
            occupation = st.text_input("Occupation")
            hobbies = st.text_area("Hobbies/Activities", height=60)
        
        uploaded = st.file_uploader("Upload medical reports (PDF/JPG/PNG)", 
                                  type=['pdf', 'jpg', 'png'], 
                                  accept_multiple_files=True)
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.form_submit_button("Back to Dashboard", use_container_width=True):
                st.session_state.menu = "Dashboard"
                st.session_state.exam_step = None
                st.rerun()
        with col_btn2:
            submit = st.form_submit_button("Save & Continue → Refraction", use_container_width=True)
        
        if submit:
            try:
                files = []
                if uploaded:
                    os.makedirs("uploads", exist_ok=True)
                    for f in uploaded:
                        safe_name = "".join(c for c in f.name if c.isalnum() or c in "._- ")
                        path = os.path.join("uploads", f"{datetime.now().timestamp()}_{safe_name}")
                        with open(path, "wb") as fp:
                            fp.write(f.getbuffer())
                        files.append(path)
                
                c = conn.cursor()
                c.execute('''
                    INSERT INTO medical_history
                    (patient_id, general_health, current_medications, allergies, headaches_history, family_history,
                     ocular_history, previous_surgeries, last_eye_exam, smoking_status, alcohol_consumption, occupation, hobbies, uploaded_reports)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (pinfo['id'], general_health, current_medications, allergies, headaches, family_history, 
                     ocular_history, previous_surgeries, last_eye_exam, smoking, alcohol, occupation, hobbies, json.dumps(files)))
                conn.commit()
                st.success("Medical history saved successfully!")
                st.session_state.exam_step = "refraction"
                st.rerun()
            except Exception as e:
                st.error(f"Database error: {str(e)}")

def refraction_examination():
    st.markdown("<h2 class='main-header'>2. Comprehensive Refraction & Vision Examination</h2>", unsafe_allow_html=True)
    if 'selected_patient' not in st.session_state or not st.session_state.selected_patient:
        st.error("No patient selected.")
        return
    
    pid_code = st.session_state.selected_patient
    try:
        pinfo = pd.read_sql("SELECT * FROM patients WHERE patient_id = ?", conn, params=(pid_code,)).iloc[0]
        st.markdown(f"### Patient: {pinfo['first_name']} {pinfo['last_name']} (ID: {pinfo['patient_id']})")
    except Exception:
        st.error("Patient not found.")
        return

    if 'refraction' not in st.session_state:
        st.session_state.refraction = {}

    # Navigation
    col_nav = st.columns(3)
    with col_nav[0]:
        if st.button("Back to Medical History", use_container_width=True):
            st.session_state.exam_step = "medical_history"
            st.rerun()
    with col_nav[2]:
        if st.button("Skip to Functional Tests", use_container_width=True):
            st.session_state.exam_step = "functional_tests"
            st.rerun()

    # 1) Vision Examination WITH ADD/DEG
    st.markdown("<div class='exam-section'><h4>Vision Examination</h4></div>", unsafe_allow_html=True)
    with st.form("vision_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Habitual Correction**")
            habitual_type = st.selectbox("Type of Correction", 
                                       ["None", "Spectacles", "Soft Contact Lenses", "RGP", "Scleral", "Ortho-K", "Other"])
            
            st.markdown("**Right Eye (OD)**")
            h_od_va = st.text_input("Habitual VA OD", placeholder="e.g., 1.0 or 20/20")
            h_od_mod = st.text_input("Modifier OD", placeholder="-2")
            h_od_add = st.text_input("ADD OD", placeholder="e.g., +1.50")
            h_od_deg = st.text_input("DEG OD", placeholder="e.g., 2.00")
            
            st.markdown("**Left Eye (OS)**")
            h_os_va = st.text_input("Habitual VA OS", placeholder="e.g., 1.0 or 20/20")
            h_os_mod = st.text_input("Modifier OS", placeholder="-2")
            h_os_add = st.text_input("ADD OS", placeholder="e.g., +1.50")
            h_os_deg = st.text_input("DEG OS", placeholder="e.g., 2.00")
            
        with col2:
            st.markdown("**Uncorrected Vision**")
            uc_od_va = st.text_input("Uncorrected VA OD", placeholder="e.g., 1.0 or 20/200")
            uc_od_mod = st.text_input("Modifier OD", placeholder="-2")
            uc_os_va = st.text_input("Uncorrected VA OS", placeholder="e.g., 1.0 or 20/200")
            uc_os_mod = st.text_input("Modifier OS", placeholder="-2")
            
            st.markdown("**Binocular Vision**")
            h_bin_va = st.text_input("Habitual Binocular VA", placeholder="1.0 or 20/20")
            h_pd = st.text_input("PD (mm)", placeholder="e.g., 62")
            habitual_distance = st.text_input("Distance", placeholder="e.g., 6m")
            vision_notes = st.text_area("Vision Notes", height=100)
        
        if st.form_submit_button("Save Vision Data", use_container_width=True):
            st.session_state.refraction.update({
                'habitual_type': habitual_type,
                'habitual_od_va': h_od_va, 'habitual_od_modifier': h_od_mod,
                'habitual_os_va': h_os_va, 'habitual_os_modifier': h_os_mod,
                'habitual_binocular_va': h_bin_va, 'habitual_pd': h_pd,
                'habitual_add_od': h_od_add, 'habitual_add_os': h_os_add,
                'habitual_deg_od': h_od_deg, 'habitual_deg_os': h_os_deg,
                'habitual_distance': habitual_distance,
                'uncorrected_od_va': uc_od_va, 'uncorrected_od_modifier': uc_od_mod,
                'uncorrected_os_va': uc_os_va, 'uncorrected_os_modifier': uc_os_mod,
                'vision_notes': vision_notes
            })
            st.success("Vision data saved!")

    # 2) Objective Refraction
    st.markdown("<div class='exam-section'><h4>Objective Refraction</h4></div>", unsafe_allow_html=True)
    with st.form("objective_form"):
        col_obj1, col_obj2 = st.columns(2)
        
        with col_obj1:
            objective_method = st.selectbox("Method", ["Autorefractor", "Retinoscopy", "Other"])
            objective_time = st.time_input("Time of measurement", value=datetime.now().time())
            
            st.markdown("**Right Eye (OD)**")
            obj_od_sph = st.number_input("Sphere OD", value=0.0, step=0.25, format="%.2f")
            obj_od_cyl = st.number_input("Cylinder OD", value=0.0, step=0.25, format="%.2f")
            obj_od_axis = st.number_input("Axis OD", min_value=0, max_value=180, value=0)
            
        with col_obj2:
            st.markdown("**Left Eye (OS)**")
            obj_os_sph = st.number_input("Sphere OS", value=0.0, step=0.25, format="%.2f")
            obj_os_cyl = st.number_input("Cylinder OS", value=0.0, step=0.25, format="%.2f")
            obj_os_axis = st.number_input("Axis OS", min_value=0, max_value=180, value=0)
            
            objective_notes = st.text_area("Objective Notes", height=100)
        
        if st.form_submit_button("Save Objective Data", use_container_width=True):
            st.session_state.refraction.update({
                'objective_method': objective_method,
                'objective_time': objective_time.strftime("%H:%M"),
                'autorefractor_od_sphere': obj_od_sph, 'autorefractor_od_cylinder': obj_od_cyl, 'autorefractor_od_axis': obj_od_axis,
                'autorefractor_os_sphere': obj_os_sph, 'autorefractor_os_cylinder': obj_os_cyl, 'autorefractor_os_axis': obj_os_axis,
                'objective_notes': objective_notes
            })
            st.success("Objective data saved!")

    # 3) Subjective Refraction WITH ADD/DEG
    st.markdown("<div class='exam-section'><h4>Subjective Refraction</h4></div>", unsafe_allow_html=True)
    with st.form("subjective_form"):
        subj_method = st.selectbox("Subjective Method", ["Fogging", "With Cycloplegic", "Other"])
        
        col_subj1, col_subj2 = st.columns(2)
        
        with col_subj1:
            st.markdown("**Right Eye (OD)**")
            subj_od_sph = st.number_input("Sphere OD", value=0.0, step=0.25, format="%.2f", key="subj_od_sph")
            subj_od_cyl = st.number_input("Cylinder OD", value=0.0, step=0.25, format="%.2f", key="subj_od_cyl")
            subj_od_axis = st.number_input("Axis OD", min_value=0, max_value=180, value=0, key="subj_od_axis")
            subj_od_va = st.text_input("Subjective VA OD", placeholder="e.g., 1.0 or 20/20")
            subj_od_add = st.text_input("ADD OD", placeholder="e.g., +1.50")
            subj_od_deg = st.text_input("DEG OD", placeholder="e.g., 2.00")
            
        with col_subj2:
            st.markdown("**Left Eye (OS)**")
            subj_os_sph = st.number_input("Sphere OS", value=0.0, step=0.25, format="%.2f", key="subj_os_sph")
            subj_os_cyl = st.number_input("Cylinder OS", value=0.0, step=0.25, format="%.2f", key="subj_os_cyl")
            subj_os_axis = st.number_input("Axis OS", min_value=0, max_value=180, value=0, key="subj_os_axis")
            subj_os_va = st.text_input("Subjective VA OS", placeholder="e.g., 1.0 or 20/20")
            subj_os_add = st.text_input("ADD OS", placeholder="e.g., +1.50")
            subj_os_deg = st.text_input("DEG OS", placeholder="e.g., 2.00")
        
        subjective_distance = st.text_input("Distance", placeholder="e.g., 6m")
        subjective_notes = st.text_area("Subjective Notes", height=80)
        
        if st.form_submit_button("Save Subjective Data", use_container_width=True):
            st.session_state.refraction.update({
                'subjective_method': subj_method,
                'subjective_od_sphere': subj_od_sph, 'subjective_od_cylinder': subj_od_cyl, 'subjective_od_axis': subj_od_axis,
                'subjective_od_va': subj_od_va, 'subjective_add_od': subj_od_add, 'subjective_deg_od': subj_od_deg,
                'subjective_os_sphere': subj_os_sph, 'subjective_os_cylinder': subj_os_cyl, 'subjective_os_axis': subj_os_axis,
                'subjective_os_va': subj_os_va, 'subjective_add_os': subj_os_add, 'subjective_deg_os': subj_os_deg,
                'subjective_distance': subjective_distance,
                'subjective_notes': subjective_notes
            })
            st.success("Subjective data saved!")

    # 4) Final Prescription WITH ADD/DEG
    st.markdown("<div class='exam-section'><h4>Final Prescription</h4></div>", unsafe_allow_html=True)
    with st.form("final_form"):
        col_final1, col_final2 = st.columns(2)
        
        with col_final1:
            st.markdown("**Right Eye (OD) - Final**")
            final_od_sph = st.number_input("Final Sphere OD", value=0.0, step=0.25, format="%.2f")
            final_od_cyl = st.number_input("Final Cylinder OD", value=0.0, step=0.25, format="%.2f")
            final_od_axis = st.number_input("Final Axis OD", min_value=0, max_value=180, value=0)
            final_add_od = st.text_input("Final ADD OD", placeholder="e.g., +1.50")
            final_deg_od = st.text_input("Final DEG OD", placeholder="e.g., 2.00")
            
        with col_final2:
            st.markdown("**Left Eye (OS) - Final**")
            final_os_sph = st.number_input("Final Sphere OS", value=0.0, step=0.25, format="%.2f")
            final_os_cyl = st.number_input("Final Cylinder OS", value=0.0, step=0.25, format="%.2f")
            final_os_axis = st.number_input("Final Axis OS", min_value=0, max_value=180, value=0)
            final_add_os = st.text_input("Final ADD OS", placeholder="e.g., +1.50")
            final_deg_os = st.text_input("Final DEG OS", placeholder="e.g., 2.00")
        
        col_bin1, col_bin2 = st.columns(2)
        with col_bin1:
            binocular_balance = st.selectbox("Binocular Balance", ["Balanced", "OD dominant", "OS dominant", "Unbalanced"])
            stereopsis = st.text_input("Stereoacuity", placeholder="e.g., 40 arcsec")
            final_bin_va = st.text_input("Final Binocular VA", placeholder="e.g., 1.0 or 20/20")
            final_distance = st.text_input("Final Distance", placeholder="e.g., 6m")
            
        with col_bin2:
            npc_break = st.text_input("NPC Break", placeholder="e.g., 5 cm")
            npc_recovery = st.text_input("NPC Recovery", placeholder="e.g., 7 cm")
            prescription_notes = st.text_area("Prescription Notes", height=100)
        
        col_save1, col_save2 = st.columns(2)
        with col_save1:
            if st.form_submit_button("Save Refraction & Continue", use_container_width=True):
                try:
                    p = pd.read_sql("SELECT id FROM patients WHERE patient_id = ?", conn, params=(pid_code,)).iloc[0]
                    pid = p['id']
                    
                    c = conn.cursor()
                    c.execute('''
                        INSERT INTO refraction_exams (
                            patient_id, habitual_type, habitual_od_va, habitual_od_modifier, habitual_os_va, habitual_os_modifier,
                            habitual_binocular_va, habitual_pd, habitual_add_od, habitual_add_os, habitual_deg_od, habitual_deg_os, habitual_distance,
                            vision_notes, uncorrected_od_va, uncorrected_od_modifier, uncorrected_os_va, uncorrected_os_modifier, uncorrected_binocular_va,
                            objective_method, objective_time, autorefractor_od_sphere, autorefractor_od_cylinder, autorefractor_od_axis,
                            autorefractor_os_sphere, autorefractor_os_cylinder, autorefractor_os_axis, objective_notes,
                            subjective_method, subjective_od_sphere, subjective_od_cylinder, subjective_od_axis, subjective_od_va, subjective_add_od, subjective_deg_od,
                            subjective_os_sphere, subjective_os_cylinder, subjective_os_axis, subjective_os_va, subjective_add_os, subjective_deg_os, subjective_distance, subjective_notes,
                            binocular_balance, stereopsis, near_point_convergence_break, near_point_convergence_recovery,
                            final_prescribed_od_sphere, final_prescribed_od_cylinder, final_prescribed_od_axis, final_add_od, final_deg_od,
                            final_prescribed_os_sphere, final_prescribed_os_cylinder, final_prescribed_os_axis, final_add_os, final_deg_os,
                            final_prescribed_binocular_va, final_distance, prescription_notes
                        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ''', (
                        pid, st.session_state.refraction.get('habitual_type'),
                        st.session_state.refraction.get('habitual_od_va'), st.session_state.refraction.get('habitual_od_modifier'),
                        st.session_state.refraction.get('habitual_os_va'), st.session_state.refraction.get('habitual_os_modifier'),
                        st.session_state.refraction.get('habitual_binocular_va'), st.session_state.refraction.get('habitual_pd'),
                        st.session_state.refraction.get('habitual_add_od'), st.session_state.refraction.get('habitual_add_os'),
                        st.session_state.refraction.get('habitual_deg_od'), st.session_state.refraction.get('habitual_deg_os'),
                        st.session_state.refraction.get('habitual_distance'), st.session_state.refraction.get('vision_notes'),
                        st.session_state.refraction.get('uncorrected_od_va'), st.session_state.refraction.get('uncorrected_od_modifier'),
                        st.session_state.refraction.get('uncorrected_os_va'), st.session_state.refraction.get('uncorrected_os_modifier'),
                        st.session_state.refraction.get('uncorrected_binocular_va'),
                        st.session_state.refraction.get('objective_method'), st.session_state.refraction.get('objective_time'),
                        st.session_state.refraction.get('autorefractor_od_sphere'), st.session_state.refraction.get('autorefractor_od_cylinder'), st.session_state.refraction.get('autorefractor_od_axis'),
                        st.session_state.refraction.get('autorefractor_os_sphere'), st.session_state.refraction.get('autorefractor_os_cylinder'), st.session_state.refraction.get('autorefractor_os_axis'),
                        st.session_state.refraction.get('objective_notes'),
                        st.session_state.refraction.get('subjective_method'),
                        st.session_state.refraction.get('subjective_od_sphere'), st.session_state.refraction.get('subjective_od_cylinder'), st.session_state.refraction.get('subjective_od_axis'), 
                        st.session_state.refraction.get('subjective_od_va'), st.session_state.refraction.get('subjective_add_od'), st.session_state.refraction.get('subjective_deg_od'),
                        st.session_state.refraction.get('subjective_os_sphere'), st.session_state.refraction.get('subjective_os_cylinder'), st.session_state.refraction.get('subjective_os_axis'), 
                        st.session_state.refraction.get('subjective_os_va'), st.session_state.refraction.get('subjective_add_os'), st.session_state.refraction.get('subjective_deg_os'),
                        st.session_state.refraction.get('subjective_distance'), st.session_state.refraction.get('subjective_notes'),
                        binocular_balance, stereopsis, npc_break, npc_recovery,
                        final_od_sph, final_od_cyl, final_od_axis, final_add_od, final_deg_od,
                        final_os_sph, final_os_cyl, final_os_axis, final_add_os, final_deg_os,
                        final_bin_va, final_distance, prescription_notes
                    ))
                    conn.commit()
                    st.success("Refraction examination saved successfully!")
                    st.session_state.refraction = {}
                    st.session_state.exam_step = "functional_tests"
                    st.rerun()
                except Exception as e:
                    st.error(f"Database error: {str(e)}")

def functional_tests():
    st.markdown("<h2 class='main-header'>3. Functional Vision Tests</h2>", unsafe_allow_html=True)
    if 'selected_patient' not in st.session_state or not st.session_state.selected_patient:
        st.error("No patient selected.")
        return
    
    pid = st.session_state.selected_patient
    
    # Navigation
    col_nav = st.columns(3)
    with col_nav[0]:
        if st.button("Back to Refraction", use_container_width=True):
            st.session_state.exam_step = "refraction"
            st.rerun()
    with col_nav[2]:
        if st.button("Continue to Anterior Segment", use_container_width=True):
            st.session_state.exam_step = "anterior_segment"
            st.rerun()

    with st.form("functional_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Ocular Motility & Alignment")
            motility = st.text_area("Ocular motility", placeholder="Ductions, versions", height=80)
            hirschberg = st.text_input("Hirschberg test", placeholder="e.g., Central, 15° temporal")
            cover_distance = st.text_input("Cover test - Distance", placeholder="e.g., Ortho, 4△ XP")
            cover_near = st.text_input("Cover test - Near", placeholder="e.g., Ortho, 6△ XP")
            
        with col2:
            st.markdown("#### Pupils & Visual Fields")
            pupils = st.text_input("Pupils", placeholder="e.g., 4mm, round, reactive")
            rapd = st.selectbox("RAPD", ["None", "Present OD", "Present OS", "Unsure"])
            confrontation = st.text_area("Confrontation fields", placeholder="Visual field assessment", height=80)
            other_notes = st.text_area("Other functional notes", height=60)
        
        col_save1, col_save2 = st.columns(2)
        with col_save1:
            if st.form_submit_button("Save Functional Tests", use_container_width=True):
                try:
                    p = pd.read_sql("SELECT id FROM patients WHERE patient_id = ?", conn, params=(pid,)).iloc[0]
                    c = conn.cursor()
                    c.execute('''
                        INSERT INTO functional_tests 
                        (patient_id, motility, hirschberg, cover_test_distance, cover_test_near, pupils, rapd, confrontation_fields, other_notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (p['id'], motility, hirschberg, cover_distance, cover_near, pupils, rapd, confrontation, other_notes))
                    conn.commit()
                    st.success("Functional tests saved successfully!")
                    st.session_state.exam_step = "anterior_segment"
                    st.rerun()
                except Exception as e:
                    st.error(f"Database error: {str(e)}")

def anterior_segment_examination():
    st.markdown("<h2 class='main-header'>4. Anterior Segment Examination</h2>", unsafe_allow_html=True)
    if 'selected_patient' not in st.session_state or not st.session_state.selected_patient:
        st.error("No patient selected.")
        return
    
    pid = st.session_state.selected_patient
    
    # Navigation
    col_nav = st.columns(3)
    with col_nav[0]:
        if st.button("Back to Functional Tests", use_container_width=True):
            st.session_state.exam_step = "functional_tests"
            st.rerun()
    with col_nav[2]:
        if st.button("Continue to Posterior Segment", use_container_width=True):
            st.session_state.exam_step = "posterior_segment"
            st.rerun()

    with st.form("anterior_form"):
        st.markdown("#### Biomicroscopy")
        col_bio1, col_bio2 = st.columns(2)
        with col_bio1:
            st.markdown("<div class='eye-column'><strong>Right Eye (OD)</strong></div>", unsafe_allow_html=True)
            biomicroscopy_od = st.text_area("Biomicroscopy OD", 
                                          placeholder="Cornea, conjunctiva, anterior chamber, iris, lens", 
                                          height=120)
        with col_bio2:
            st.markdown("<div class='eye-column'><strong>Left Eye (OS)</strong></div>", unsafe_allow_html=True)
            biomicroscopy_os = st.text_area("Biomicroscopy OS", 
                                          placeholder="Cornea, conjunctiva, anterior chamber, iris, lens", 
                                          height=120)
        biomicroscopy_notes = st.text_area("Biomicroscopy notes", height=60)

        st.markdown("#### Anterior Chamber & Angle")
        col_ac1, col_ac2 = st.columns(2)
        with col_ac1:
            st.markdown("<div class='eye-column'><strong>Right Eye (OD)</strong></div>", unsafe_allow_html=True)
            ac_depth_od = st.selectbox("AC Depth OD", ["Deep", "Medium", "Shallow", "Flat"])
            ac_volume_od = st.text_input("AC Volume OD", placeholder="e.g., Normal")
            angle_od = st.selectbox("Iridocorneal Angle OD", ["Open", "Narrow", "Closed", "Grade 0-4"])
        with col_ac2:
            st.markdown("<div class='eye-column'><strong>Left Eye (OS)</strong></div>", unsafe_allow_html=True)
            ac_depth_os = st.selectbox("AC Depth OS", ["Deep", "Medium", "Shallow", "Flat"])
            ac_volume_os = st.text_input("AC Volume OS", placeholder="e.g., Normal")
            angle_os = st.selectbox("Iridocorneal Angle OS", ["Open", "Narrow", "Closed", "Grade 0-4"])

        st.markdown("#### Tonometry & Pachymetry")
        col_tono1, col_tono2 = st.columns(2)
        with col_tono1:
            st.markdown("<div class='eye-column'><strong>Right Eye (OD)</strong></div>", unsafe_allow_html=True)
            pachymetry_od = st.number_input("CCT OD (μm)", min_value=400, max_value=700, value=540, step=5)
            iop_od = st.text_input("IOP OD (mmHg)", placeholder="e.g., 16")
        with col_tono2:
            st.markdown("<div class='eye-column'><strong>Left Eye (OS)</strong></div>", unsafe_allow_html=True)
            pachymetry_os = st.number_input("CCT OS (μm)", min_value=400, max_value=700, value=540, step=5)
            iop_os = st.text_input("IOP OS (mmHg)", placeholder="e.g., 15")
        
        col_tono3, col_tono4 = st.columns(2)
        with col_tono3:
            tonometry_type = st.selectbox("Tonometry Type", 
                                        ["Goldmann", "Non-contact", "iCare", "Perkins", "Other"])
            tonometry_time = st.time_input("Tonometry Time", value=datetime.now().time())
        with col_tono4:
            tonometry_compensation = st.selectbox("Compensation", 
                                               ["None", "CCT adjusted", "DCT", "Other"])

        st.markdown("#### Pupillography")
        pupillography_results = st.text_area("Pupillography results", 
                                           placeholder="Pupil size, reactivity, shape", 
                                           height=80)
        pupillography_notes = st.text_area("Pupillography notes", height=60)
        
        uploaded_files = st.file_uploader("Upload anterior segment images", 
                                        type=['pdf', 'png', 'jpg', 'jpeg'], 
                                        accept_multiple_files=True)

        col_save1, col_save2 = st.columns(2)
        with col_save1:
            if st.form_submit_button("Save Anterior Segment", use_container_width=True):
                try:
                    p = pd.read_sql("SELECT id FROM patients WHERE patient_id = ?", conn, params=(pid,)).iloc[0]
                    
                    file_paths = []
                    if uploaded_files:
                        os.makedirs("uploads", exist_ok=True)
                        for f in uploaded_files:
                            safe_name = "".join(c for c in f.name if c.isalnum() or c in "._- ")
                            path = os.path.join("uploads", f"{datetime.now().timestamp()}_{safe_name}")
                            with open(path, "wb") as fp:
                                fp.write(f.getbuffer())
                            file_paths.append(path)
                    
                    c = conn.cursor()
                    c.execute('''
                        INSERT INTO anterior_segment_exams 
                        (patient_id, biomicroscopy_od, biomicroscopy_os, biomicroscopy_notes,
                         anterior_chamber_depth_od, anterior_chamber_depth_os, anterior_chamber_volume_od, anterior_chamber_volume_os,
                         iridocorneal_angle_od, iridocorneal_angle_os, pachymetry_od, pachymetry_os,
                         tonometry_type, tonometry_time, tonometry_compensation, tonometry_od, tonometry_os,
                         pupillography_results, pupillography_notes, uploaded_files)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (p['id'], biomicroscopy_od, biomicroscopy_os, biomicroscopy_notes,
                         ac_depth_od, ac_depth_os, ac_volume_od, ac_volume_os, angle_od, angle_os,
                         pachymetry_od, pachymetry_os, tonometry_type, tonometry_time.strftime("%H:%M"),
                         tonometry_compensation, iop_od, iop_os, pupillography_results, pupillography_notes,
                         json.dumps(file_paths)))
                    conn.commit()
                    st.success("Anterior segment examination saved successfully!")
                    st.session_state.exam_step = "posterior_segment"
                    st.rerun()
                except Exception as e:
                    st.error(f"Database error: {str(e)}")

def posterior_segment_examination():
    st.markdown("<h2 class='main-header'>5. Posterior Segment Examination</h2>", unsafe_allow_html=True)
    if 'selected_patient' not in st.session_state or not st.session_state.selected_patient:
        st.error("No patient selected.")
        return
    
    pid = st.session_state.selected_patient
    
    # Navigation
    col_nav = st.columns(3)
    with col_nav[0]:
        if st.button("Back to Anterior Segment", use_container_width=True):
            st.session_state.exam_step = "anterior_segment"
            st.rerun()
    with col_nav[2]:
        if st.button("Continue to Contact Lenses", use_container_width=True):
            st.session_state.exam_step = "contact_lenses"
            st.rerun()

    with st.form("posterior_form"):
        st.markdown("#### Fundus Examination")
        fundus_type = st.selectbox("Fundus Exam Type", 
                                 ["Indirect ophthalmoscopy", "Fundus camera", "Widefield", "Slit lamp", "Other"])
        
        col_fundus1, col_fundus2 = st.columns(2)
        with col_fundus1:
            st.markdown("<div class='eye-column'><strong>Right Eye (OD)</strong></div>", unsafe_allow_html=True)
            fundus_od = st.text_area("Fundus OD", 
                                   placeholder="Optic disc, macula, vessels, periphery", 
                                   height=120)
        with col_fundus2:
            st.markdown("<div class='eye-column'><strong>Left Eye (OS)</strong></div>", unsafe_allow_html=True)
            fundus_os = st.text_area("Fundus OS", 
                                   placeholder="Optic disc, macula, vessels, periphery", 
                                   height=120)
        fundus_notes = st.text_area("Fundus examination notes", height=80)

        st.markdown("#### OCT Imaging")
        col_oct1, col_oct2 = st.columns(2)
        with col_oct1:
            st.markdown("<div class='eye-column'><strong>Right Eye (OD)</strong></div>", unsafe_allow_html=True)
            oct_macula_od = st.text_area("OCT Macula OD", placeholder="Macular thickness, morphology", height=80)
            oct_rnfl_od = st.text_area("OCT RNFL OD", placeholder="RNFL thickness, symmetry", height=80)
        with col_oct2:
            st.markdown("<div class='eye-column'><strong>Left Eye (OS)</strong></div>", unsafe_allow_html=True)
            oct_macula_os = st.text_area("OCT Macula OS", placeholder="Macular thickness, morphology", height=80)
            oct_rnfl_os = st.text_area("OCT RNFL OS", placeholder="RNFL thickness, symmetry", height=80)
        oct_notes = st.text_area("OCT notes", height=60)

        # Enhanced image upload for posterior segment
        st.markdown("#### Fundus & OCT Images")
        uploaded_files = st.file_uploader("Upload posterior segment images (OCT, fundus photos, angiography)", 
                                        type=['pdf', 'png', 'jpg', 'jpeg', 'tiff'], 
                                        accept_multiple_files=True,
                                        help="Upload high-quality fundus photos, OCT scans, angiography images")
        
        if uploaded_files:
            st.info(f"{len(uploaded_files)} file(s) selected for upload")
            # Display image previews if needed

        col_save1, col_save2 = st.columns(2)
        with col_save1:
            if st.form_submit_button("Save Posterior Segment", use_container_width=True):
                try:
                    p = pd.read_sql("SELECT id FROM patients WHERE patient_id = ?", conn, params=(pid,)).iloc[0]
                    
                    file_paths = []
                    if uploaded_files:
                        os.makedirs("uploads", exist_ok=True)
                        for f in uploaded_files:
                            safe_name = "".join(c for c in f.name if c.isalnum() or c in "._- ")
                            path = os.path.join("uploads", f"{datetime.now().timestamp()}_{safe_name}")
                            with open(path, "wb") as fp:
                                fp.write(f.getbuffer())
                            file_paths.append(path)
                    
                    c = conn.cursor()
                    c.execute('''
                        INSERT INTO posterior_segment_exams 
                        (patient_id, fundus_exam_type, fundus_od, fundus_os, fundus_notes,
                         oct_macula_od, oct_macula_os, oct_rnfl_od, oct_rnfl_os, oct_notes, uploaded_files)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (p['id'], fundus_type, fundus_od, fundus_os, fundus_notes,
                         oct_macula_od, oct_macula_os, oct_rnfl_od, oct_rnfl_os, oct_notes, json.dumps(file_paths)))
                    conn.commit()
                    st.success("Posterior segment examination saved successfully!")
                    st.session_state.exam_step = "contact_lenses"
                    st.rerun()
                except Exception as e:
                    st.error(f"Database error: {str(e)}")

# -----------------------
# PROFESSIONAL CONTACT LENSES WITH ADD AND FLEXIBLE DESIGN OPTIONS
# -----------------------
def contact_lenses():
    st.markdown("<h2 class='main-header'>6. Contact Lens Fitting & Prescription</h2>", unsafe_allow_html=True)
    
    if 'selected_patient' not in st.session_state or not st.session_state.selected_patient:
        st.info("Please select a patient first from Patient Search or Dashboard.")
        return
    
    pid = st.session_state.selected_patient
    
    try:
        pinfo = pd.read_sql("SELECT * FROM patients WHERE patient_id = ?", conn, params=(pid,)).iloc[0]
        st.markdown(f"### Patient: {pinfo['first_name']} {pinfo['last_name']} (ID: {pinfo['patient_id']})")
    except Exception:
        st.error("Patient not found.")
        return

    # Navigation
    col_nav = st.columns(3)
    with col_nav[0]:
        if st.button("Back to Posterior Segment", use_container_width=True):
            st.session_state.exam_step = "posterior_segment"
            st.rerun()
    with col_nav[2]:
        if st.button("Continue to Clinical Report", use_container_width=True):
            st.session_state.exam_step = "generate_report"
            st.rerun()

    with st.form("cl_form"):
        lens_type = st.selectbox("Lens Type", 
                               ["Soft", "RGP", "Scleral", "Custom", "Ortho-K", "Hybrid", "Other"])
        
        # General lens parameters
        st.markdown("#### General Lens Parameters")
        col_gen1, col_gen2 = st.columns(2)
        with col_gen1:
            lens_design = st.text_input("Lens Design", placeholder="e.g., Spherical, Aspheric, Toric, Multifocal, Back Toric, Bitoric, Rose K2, etc.")
            lens_material = st.text_input("Lens Material", placeholder="e.g., Boston XO, Senofilcon A, etc.")
        with col_gen2:
            lens_color = st.text_input("Lens Color/Visibility", placeholder="e.g., Clear, Blue, Handling tint")
            brand = st.text_input("Brand/Manufacturer", placeholder="e.g., Acuvue, Biofinity, etc.")
        
        # Power parameters with ADD for both eyes
        st.markdown("#### Lens Power Parameters")
        col_power1, col_power2 = st.columns(2)
        
        with col_power1:
            st.markdown("<div class='eye-column'><strong>Right Eye (OD)</strong></div>", unsafe_allow_html=True)
            od_sphere = st.number_input("Sphere OD", value=0.0, step=0.25, format="%.2f")
            od_cylinder = st.number_input("Cylinder OD", value=0.0, step=0.25, format="%.2f")
            od_axis = st.number_input("Axis OD", min_value=0, max_value=180, value=0)
            od_add = st.text_input("ADD OD", placeholder="e.g., +1.50 for multifocal")
            
        with col_power2:
            st.markdown("<div class='eye-column'><strong>Left Eye (OS)</strong></div>", unsafe_allow_html=True)
            os_sphere = st.number_input("Sphere OS", value=0.0, step=0.25, format="%.2f")
            os_cylinder = st.number_input("Cylinder OS", value=0.0, step=0.25, format="%.2f")
            os_axis = st.number_input("Axis OS", min_value=0, max_value=180, value=0)
            os_add = st.text_input("ADD OS", placeholder="e.g., +1.50 for multifocal")
        
        # Lens-specific parameters
        if lens_type == "Soft":
            st.markdown("#### Soft Lens Parameters")
            col_soft1, col_soft2 = st.columns(2)
            with col_soft1:
                soft_base_curve = st.number_input("Base Curve (mm)", min_value=7.0, max_value=10.0, value=8.6, step=0.1)
            with col_soft2:
                soft_diameter = st.number_input("Diameter (mm)", min_value=13.0, max_value=16.0, value=14.2, step=0.1)
                
        elif lens_type == "RGP":
            st.markdown("#### RGP Lens Parameters")
            col_rgp1, col_rgp2 = st.columns(2)
            with col_rgp1:
                rgp_base_curve = st.number_input("Base Curve (mm)", min_value=6.0, max_value=9.0, value=7.8, step=0.1)
            with col_rgp2:
                rgp_diameter = st.number_input("Diameter (mm)", min_value=8.0, max_value=11.0, value=9.2, step=0.1)
                
        elif lens_type == "Scleral":
            st.markdown("#### Scleral Lens Parameters")
            col_scl1, col_scl2 = st.columns(2)
            with col_scl1:
                scleral_diameter = st.text_input("Diameter", placeholder="e.g., 16.5mm, 18.0mm")
            with col_scl2:
                scleral_design = st.text_input("Specific Design", placeholder="e.g., PROSE, Zenlens, etc.")
                
        elif lens_type == "Ortho-K":
            st.markdown("#### Ortho-K Parameters")
            ortho_k_parameters = st.text_area("Ortho-K Treatment Parameters", 
                                            placeholder="Treatment zone, reverse curve, alignment curve details",
                                            height=100)
        
        # Fitting details
        st.markdown("#### Fitting Details & Assessment")
        col_fit1, col_fit2 = st.columns(2)
        with col_fit1:
            wearing_schedule = st.selectbox("Wearing Schedule", 
                                          ["Daily", "Weekly", "Monthly", "Extended", "Flexible", "Other"])
            care_solution = st.text_input("Care Solution", placeholder="e.g., Boston Advance, PeroxiClear")
        with col_fit2:
            follow_up_date = st.date_input("Follow-up Date", value=date.today() + timedelta(days=30))
        
        # Professional assessment
        professional_assessment = st.text_area("Professional Assessment", 
                                            placeholder="Lens fit evaluation, centration, movement, corneal coverage",
                                            height=100)
        patient_feedback = st.text_area("Patient Feedback & Comfort", 
                                      placeholder="Patient subjective experience, comfort, vision quality",
                                      height=80)
        fitting_notes = st.text_area("Additional Fitting Notes", height=80)
        
        # Enhanced file upload for fitting documentation
        st.markdown("#### Fitting Documentation")
        fitting_images = st.file_uploader("Upload fitting images/videos (slit lamp, topography, fit assessment)", 
                                        type=['png', 'jpg', 'jpeg', 'mp4', 'mov'],
                                        accept_multiple_files=True,
                                        help="Document lens fit with slit lamp images, topography maps, etc.")
        
        # OphtalCAM device integration
        st.markdown("#### OphtalCAM Device Integration")
        if st.button("Start OphtalCAM Device", use_container_width=True):
            st.info("OphtalCAM device integration would be implemented here")
            # This would integrate with actual OphtalCAM hardware
        
        col_save1, col_save2 = st.columns(2)
        with col_save1:
            if st.form_submit_button("Save Contact Lens Prescription", use_container_width=True):
                try:
                    p = pd.read_sql("SELECT id FROM patients WHERE patient_id = ?", conn, params=(pid,)).iloc[0]
                    
                    file_paths = []
                    if fitting_images:
                        os.makedirs("uploads", exist_ok=True)
                        for f in fitting_images:
                            safe_name = "".join(c for c in f.name if c.isalnum() or c in "._- ")
                            path = os.path.join("uploads", f"{datetime.now().timestamp()}_{safe_name}")
                            with open(path, "wb") as fp:
                                fp.write(f.getbuffer())
                            file_paths.append(path)
                    
                    c = conn.cursor()
                    
                    # Unified insert for all lens types
                    c.execute('''
                        INSERT INTO contact_lens_prescriptions 
                        (patient_id, lens_type, lens_design, lens_material, lens_color,
                         soft_brand, soft_base_curve, soft_diameter,
                         soft_power_od_sphere, soft_power_od_cylinder, soft_power_od_axis, soft_add_od,
                         soft_power_os_sphere, soft_power_os_cylinder, soft_power_os_axis, soft_add_os,
                         rgp_base_curve, rgp_diameter,
                         rgp_power_od_sphere, rgp_power_od_cylinder, rgp_power_od_axis, rgp_add_od,
                         rgp_power_os_sphere, rgp_power_os_cylinder, rgp_power_os_axis, rgp_add_os,
                         scleral_diameter,
                         scleral_power_od_sphere, scleral_power_od_cylinder, scleral_power_od_axis, scleral_add_od,
                         scleral_power_os_sphere, scleral_power_os_cylinder, scleral_power_os_axis, scleral_add_os,
                         ortho_k_parameters,
                         wearing_schedule, care_solution, follow_up_date, fitting_notes,
                         professional_assessment, patient_feedback, fitting_images)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (p['id'], lens_type, lens_design, lens_material, lens_color,
                         brand if lens_type == "Soft" else None,
                         soft_base_curve if lens_type == "Soft" else None,
                         soft_diameter if lens_type == "Soft" else None,
                         od_sphere, od_cylinder, od_axis, od_add,
                         os_sphere, os_cylinder, os_axis, os_add,
                         rgp_base_curve if lens_type == "RGP" else None,
                         rgp_diameter if lens_type == "RGP" else None,
                         od_sphere, od_cylinder, od_axis, od_add,
                         os_sphere, os_cylinder, os_axis, os_add,
                         scleral_diameter if lens_type == "Scleral" else None,
                         od_sphere, od_cylinder, od_axis, od_add,
                         os_sphere, os_cylinder, os_axis, os_add,
                         ortho_k_parameters if lens_type == "Ortho-K" else None,
                         wearing_schedule, care_solution, follow_up_date, fitting_notes,
                         professional_assessment, patient_feedback, json.dumps(file_paths)))
                    
                    conn.commit()
                    st.success("Contact lens prescription saved successfully!")
                    st.session_state.exam_step = "generate_report"
                    st.rerun()
                except Exception as e:
                    st.error(f"Database error: {str(e)}")

# -----------------------
# PROFESSIONAL CLINICAL REPORT GENERATION
# -----------------------
def generate_report():
    st.markdown("<h2 class='main-header'>7. Clinical Report Generation</h2>", unsafe_allow_html=True)
    
    if 'selected_patient' not in st.session_state or not st.session_state.selected_patient:
        st.error("No patient selected.")
        return
    
    pid_code = st.session_state.selected_patient
    
    try:
        # Get patient info
        p = pd.read_sql("SELECT * FROM patients WHERE patient_id = ?", conn, params=(pid_code,)).iloc[0]
        st.markdown(f"### Clinical Report for {p['first_name']} {p['last_name']}")
        st.markdown(f"**Patient ID:** {p['patient_id']} | **DOB:** {p['date_of_birth']} | **Gender:** {p['gender']}")
        
        # Navigation
        col_nav = st.columns(3)
        with col_nav[0]:
            if st.button("Back to Contact Lenses", use_container_width=True):
                st.session_state.exam_step = "contact_lenses"
                st.rerun()
        with col_nav[2]:
            if st.button("Back to Dashboard", use_container_width=True):
                st.session_state.menu = "Dashboard"
                st.session_state.exam_step = None
                st.session_state.selected_patient = None
                st.rerun()

        # Collect data from all exam tables
        st.markdown("#### Examination Summary")
        
        # Refraction
        refraction_data = pd.read_sql('''
            SELECT * FROM refraction_exams 
            WHERE patient_id = (SELECT id FROM patients WHERE patient_id = ?) 
            ORDER BY exam_date DESC LIMIT 1
        ''', conn, params=(pid_code,))
        
        if not refraction_data.empty:
            ref = refraction_data.iloc[0]
            st.markdown("**Refraction:**")
            col_ref1, col_ref2 = st.columns(2)
            with col_ref1:
                st.write(f"**OD:** {ref.get('final_prescribed_od_sphere', '')} {ref.get('final_prescribed_od_cylinder', '')} x {ref.get('final_prescribed_od_axis', '')}")
                st.write(f"**ADD OD:** {ref.get('final_add_od', '')} | **DEG OD:** {ref.get('final_deg_od', '')}")
            with col_ref2:
                st.write(f"**OS:** {ref.get('final_prescribed_os_sphere', '')} {ref.get('final_prescribed_os_cylinder', '')} x {ref.get('final_prescribed_os_axis', '')}")
                st.write(f"**ADD OS:** {ref.get('final_add_os', '')} | **DEG OS:** {ref.get('final_deg_os', '')}")
            st.write(f"**Distance:** {ref.get('final_distance', '')} | **Binocular VA:** {ref.get('final_prescribed_binocular_va', '')}")

        # Anterior Segment
        anterior_data = pd.read_sql('''
            SELECT * FROM anterior_segment_exams 
            WHERE patient_id = (SELECT id FROM patients WHERE patient_id = ?) 
            ORDER BY exam_date DESC LIMIT 1
        ''', conn, params=(pid_code,))
        
        if not anterior_data.empty:
            ant = anterior_data.iloc[0]
            st.markdown("**Anterior Segment:**")
            col_ant1, col_ant2 = st.columns(2)
            with col_ant1:
                st.write(f"**IOP OD:** {ant.get('tonometry_od', '')} mmHg")
                st.write(f"**IOP OS:** {ant.get('tonometry_os', '')} mmHg")
                st.write(f"**CCT OD:** {ant.get('pachymetry_od', '')} μm")
                st.write(f"**CCT OS:** {ant.get('pachymetry_os', '')} μm")
            with col_ant2:
                st.write(f"**AC Depth:** OD {ant.get('anterior_chamber_depth_od', '')}, OS {ant.get('anterior_chamber_depth_os', '')}")
                st.write(f"**Angle:** OD {ant.get('iridocorneal_angle_od', '')}, OS {ant.get('iridocorneal_angle_os', '')}")

        # Contact Lenses
        cl_data = pd.read_sql('''
            SELECT * FROM contact_lens_prescriptions 
            WHERE patient_id = (SELECT id FROM patients WHERE patient_id = ?) 
            ORDER BY prescription_date DESC LIMIT 1
        ''', conn, params=(pid_code,))
        
        if not cl_data.empty:
            cl = cl_data.iloc[0]
            st.markdown("**Contact Lenses:**")
            st.write(f"**Type:** {cl.get('lens_type', '')} | **Design:** {cl.get('lens_design', '')} | **Follow-up:** {cl.get('follow_up_date', '')}")

        # Custom Report Notes
        st.markdown("#### Clinical Assessment & Recommendations")
        assessment = st.text_area("Clinical Assessment", height=150, 
                                placeholder="Summarize findings, diagnosis, and treatment plan...")
        
        recommendations = st.text_area("Recommendations & Follow-up", height=120,
                                     placeholder="Next steps, medications, follow-up schedule...")

        # Generate Professional Report
        st.markdown("#### Generate Final Report")
        if st.button("Generate Printable Report", use_container_width=True):
            # Create comprehensive professional report
            report_content = f"""
PHANTASMED MEDICAL SYSTEMS - CLINICAL REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

CLINICIAN INFORMATION:
Clinician: {st.session_state.username}
Role: {st.session_state.role}
Report Date: {date.today().strftime('%d.%m.%Y')}

PATIENT INFORMATION:
Name: {p['first_name']} {p['last_name']}
Patient ID: {p['patient_id']}
Date of Birth: {p['date_of_birth']}
Gender: {p['gender']}
Contact: {p['phone']} | {p['email']}

EXAMINATION SUMMARY:
{assessment if assessment else "Comprehensive ophthalmological examination performed."}

CLINICAL FINDINGS:
- Refraction: {f"OD: {ref.get('final_prescribed_od_sphere', '')} {ref.get('final_prescribed_od_cylinder', '')} x {ref.get('final_prescribed_od_axis', '')}" if not refraction_data.empty else "Not recorded"}
- Anterior Segment: Normal examination findings
- Posterior Segment: Within normal limits
- Contact Lenses: {f"{cl.get('lens_type', '')} lenses prescribed" if not cl_data.empty else "Not prescribed"}

RECOMMENDATIONS:
{recommendations if recommendations else "Routine follow-up recommended."}

ADDITIONAL NOTES:
This report was generated using OphtalCAM EMR system.
All findings should be interpreted in clinical context.

Clinician Signature: 
_________________________
{st.session_state.username}
{date.today().strftime('%d %B %Y')}
            """
            
            st.download_button(
                label="Download Report as TXT",
                data=report_content,
                file_name=f"clinical_report_{p['patient_id']}_{date.today().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True
            )
            
            st.success("Professional report generated successfully! Click download to save.")

    except Exception as e:
        st.error(f"Error generating report: {str(e)}")

# -----------------------
# OTHER MODULES (Patient Registration, Search, etc.)
# -----------------------
def patient_registration():
    st.markdown("<h2 class='main-header'>New Patient Registration</h2>", unsafe_allow_html=True)
    with st.form("reg_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            patient_id = st.text_input("Patient ID (optional)", 
                                     placeholder="Leave blank for auto-generation")
            first_name = st.text_input("First Name*", placeholder="Given name")
            last_name = st.text_input("Last Name*", placeholder="Family name")
            date_of_birth = st.date_input("Date of Birth*", 
                                        value=date(1990, 1, 1),
                                        min_value=date(1900, 1, 1),
                                        max_value=date.today(),
                                        format="DD.MM.YYYY")
            gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"])
            
        with col2:
            phone = st.text_input("Phone", placeholder="+1234567890")
            email = st.text_input("Email", placeholder="patient@example.com")
            address = st.text_area("Address", height=60, placeholder="Full address")
            id_number = st.text_input("ID / Passport Number", placeholder="National ID or passport")
        
        with st.expander("Emergency Contact & Insurance"):
            emergency_contact = st.text_input("Emergency Contact", 
                                           placeholder="Name and phone number")
            insurance_info = st.text_input("Insurance Information", 
                                         placeholder="Insurance provider and number")
        
        if st.form_submit_button("Register New Patient", use_container_width=True):
            if not all([first_name, last_name, date_of_birth]):
                st.error("Please fill in all required fields (First Name, Last Name, Date of Birth)")
            else:
                try:
                    if not patient_id:
                        # Auto-generate patient ID
                        patient_id = f"PAT{int(datetime.now().timestamp())}"
                    
                    c = conn.cursor()
                    c.execute('''
                        INSERT INTO patients 
                        (patient_id, first_name, last_name, date_of_birth, gender, phone, email, address, id_number, emergency_contact, insurance_info)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (patient_id, first_name, last_name, date_of_birth, gender, phone, email, address, id_number, emergency_contact, insurance_info))
                    conn.commit()
                    st.success(f"Patient registered successfully! Patient ID: **{patient_id}**")
                except sqlite3.IntegrityError:
                    st.error("Patient ID already exists. Please choose a different ID.")
                except Exception as e:
                    st.error(f"Database error: {str(e)}")

def patient_search():
    st.markdown("<h2 class='main-header'>Patient Search & Records</h2>", unsafe_allow_html=True)
    
    col_search1, col_search2 = st.columns([3, 1])
    with col_search1:
        search_query = st.text_input("Search patients", 
                                   placeholder="Enter patient ID, name, phone, or ID number...")
    with col_search2:
        search_type = st.selectbox("Search by", 
                                 ["All Fields", "Patient ID", "Name", "Phone", "ID Number"])
    
    if search_query:
        try:
            if search_type == "All Fields":
                df = pd.read_sql('''
                    SELECT * FROM patients 
                    WHERE patient_id LIKE ? OR first_name LIKE ? OR last_name LIKE ? OR phone LIKE ? OR id_number LIKE ?
                    ORDER BY last_name, first_name
                ''', conn, params=(f'%{search_query}%', f'%{search_query}%', f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'))
            elif search_type == "Patient ID":
                df = pd.read_sql('SELECT * FROM patients WHERE patient_id LIKE ? ORDER BY patient_id', 
                               conn, params=(f'%{search_query}%',))
            elif search_type == "Name":
                df = pd.read_sql('SELECT * FROM patients WHERE first_name LIKE ? OR last_name LIKE ? ORDER BY last_name, first_name', 
                               conn, params=(f'%{search_query}%', f'%{search_query}%'))
            elif search_type == "Phone":
                df = pd.read_sql('SELECT * FROM patients WHERE phone LIKE ? ORDER BY last_name, first_name', 
                               conn, params=(f'%{search_query}%',))
            else:  # ID Number
                df = pd.read_sql('SELECT * FROM patients WHERE id_number LIKE ? ORDER BY last_name, first_name', 
                               conn, params=(f'%{search_query}%',))
            
            if df.empty:
                st.info("No patients found matching your search criteria.")
            else:
                st.success(f"Found {len(df)} patient(s)")
                
                for idx, row in df.iterrows():
                    with st.expander(f"{row['patient_id']} - {row['first_name']} {row['last_name']}"):
                        col_info1, col_info2 = st.columns(2)
                        
                        with col_info1:
                            st.write(f"**Date of Birth:** {row['date_of_birth']}")
                            st.write(f"**Gender:** {row['gender']}")
                            st.write(f"**Phone:** {row['phone']}")
                            
                        with col_info2:
                            st.write(f"**Email:** {row['email']}")
                            st.write(f"**ID Number:** {row['id_number']}")
                            st.write(f"**Registered:** {row['created_date'][:10]}")
                        
                        # Action buttons
                        col_act1, col_act2, col_act3, col_act4 = st.columns(4)
                        
                        with col_act1:
                            if st.button("Begin Exam", key=f"exam_{row['id']}", use_container_width=True):
                                st.session_state.selected_patient = row['patient_id']
                                st.session_state.menu = "Examination Protocol"
                                st.session_state.exam_step = "medical_history"
                                st.rerun()
                                
                        with col_act2:
                            if st.button("View History", key=f"history_{row['id']}", use_container_width=True):
                                st.session_state.selected_patient = row['patient_id']
                                st.info(f"Showing history for {row['first_name']} {row['last_name']}")
                                
                        with col_act3:
                            if st.button("Contact Lenses", key=f"cl_{row['id']}", use_container_width=True):
                                st.session_state.selected_patient = row['patient_id']
                                st.session_state.menu = "Contact Lenses"
                                st.rerun()
                                
                        with col_act4:
                            if st.button("Schedule", key=f"schedule_{row['id']}", use_container_width=True):
                                st.session_state.selected_patient = row['patient_id']
                                st.session_state.menu = "Schedule Appointment"
                                st.rerun()
                                
        except Exception as e:
            st.error(f"Search error: {str(e)}")

def user_management():
    """Admin function to manage users and licenses"""
    if st.session_state.role != "admin":
        st.error("Access denied. Admin privileges required.")
        return
        
    st.markdown("<h2 class='main-header'>User Management & License Control</h2>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["User Management", "License Settings"])
    
    with tab1:
        st.markdown("#### Add New User")
        with st.form("add_user_form"):
            col_user1, col_user2 = st.columns(2)
            with col_user1:
                new_username = st.text_input("Username")
                new_password = st.text_input("Password", type="password")
            with col_user2:
                new_role = st.selectbox("Role", ["admin", "clinician", "assistant"])
                license_expiry = st.date_input("License Expiry", value=date.today() + timedelta(days=365))
            
            if st.form_submit_button("Add User", use_container_width=True):
                if new_username and new_password:
                    try:
                        c = conn.cursor()
                        password_hash = hash_password(new_password)
                        c.execute('''
                            INSERT INTO users (username, password_hash, role, license_expiry)
                            VALUES (?, ?, ?, ?)
                        ''', (new_username, password_hash, new_role, license_expiry))
                        conn.commit()
                        st.success(f"User {new_username} added successfully!")
                    except sqlite3.IntegrityError:
                        st.error("Username already exists.")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                else:
                    st.error("Please enter both username and password.")
        
        st.markdown("#### Existing Users")
        try:
            users_df = pd.read_sql("SELECT id, username, role, license_expiry FROM users ORDER BY username", conn)
            if not users_df.empty:
                for _, user in users_df.iterrows():
                    col_user, col_role, col_license, col_action = st.columns([2, 1, 1, 1])
                    with col_user:
                        st.write(user['username'])
                    with col_role:
                        st.write(user['role'])
                    with col_license:
                        expiry_color = "🟢" if pd.to_datetime(user['license_expiry']).date() > date.today() else "🔴"
                        st.write(f"{expiry_color} {user['license_expiry']}")
                    with col_action:
                        if user['username'] != st.session_state.username:
                            if st.button("Delete", key=f"del_{user['id']}"):
                                c = conn.cursor()
                                c.execute("DELETE FROM users WHERE id = ?", (user['id'],))
                                conn.commit()
                                st.success(f"User {user['username']} deleted.")
                                st.rerun()
            else:
                st.info("No users found.")
        except Exception as e:
            st.error(f"Error loading users: {str(e)}")

# -----------------------
# MODERN TOP NAVIGATION
# -----------------------
def main_navigation():
    # Top navigation bar
    col_nav1, col_nav2, col_nav3, col_nav4, col_nav5, col_nav6, col_nav7 = st.columns(7)
    
    nav_options = {
        "Dashboard": col_nav1,
        "Patient Registration": col_nav2, 
        "Patient Search": col_nav3,
        "Examination Protocol": col_nav4,
        "Contact Lenses": col_nav5,
        "Clinical Analytics": col_nav6,
        "System Settings": col_nav7
    }
    
    for option, col in nav_options.items():
        with col:
            if st.button(option, use_container_width=True, key=f"nav_{option}"):
                st.session_state.menu = option
                if option == "Examination Protocol" and not st.session_state.selected_patient:
                    st.info("Please select a patient first from Patient Search")
                else:
                    st.rerun()
    
    st.markdown("---")
    
    # Examination progress bar (when in exam flow)
    if st.session_state.exam_step:
        st.markdown("#### Examination Progress")
        steps = [
            ("medical_history", "1. Medical History"),
            ("refraction", "2. Refraction"),
            ("functional_tests", "3. Functional Tests"), 
            ("anterior_segment", "4. Anterior Segment"),
            ("posterior_segment", "5. Posterior Segment"),
            ("contact_lenses", "6. Contact Lenses"),
            ("generate_report", "7. Clinical Report")
        ]
        
        progress_cols = st.columns(len(steps))
        for i, (step, label) in enumerate(steps):
            with progress_cols[i]:
                if step == st.session_state.exam_step:
                    st.markdown(f"**{label}**")
                else:
                    st.markdown(f"{label}")
        
        st.markdown("---")

    # Render selected page
    if st.session_state.exam_step:
        # Examination flow
        if st.session_state.exam_step == "medical_history":
            medical_history()
        elif st.session_state.exam_step == "refraction":
            refraction_examination()
        elif st.session_state.exam_step == "functional_tests":
            functional_tests()
        elif st.session_state.exam_step == "anterior_segment":
            anterior_segment_examination()
        elif st.session_state.exam_step == "posterior_segment":
            posterior_segment_examination()
        elif st.session_state.exam_step == "contact_lenses":
            contact_lenses()
        elif st.session_state.exam_step == "generate_report":
            generate_report()
    else:
        # Main menu
        if st.session_state.menu == "Dashboard":
            show_dashboard()
        elif st.session_state.menu == "Patient Registration":
            patient_registration()
        elif st.session_state.menu == "Patient Search":
            patient_search()
        elif st.session_state.menu == "Examination Protocol":
            st.info("Please select a patient from Patient Search to begin examination.")
        elif st.session_state.menu == "Contact Lenses":
            contact_lenses()
        elif st.session_state.menu == "System Settings" and st.session_state.role == "admin":
            user_management()
        else:
            st.info("This module is under development.")

def login_page():
    st.markdown("<h2 style='text-align:center;'>OphtalCAM Clinical Management System</h2>", unsafe_allow_html=True)
    
    # Professional login interface
    col_logo, col_form = st.columns([1, 2])
    
    with col_logo:
        st.image("https://i.postimg.cc/qq656tks/Phantasmed-logo.png", width=200)
        st.markdown("<div style='text-align:center;'><h3>PHANTASMED</h3><p>Medical Systems</p></div>", unsafe_allow_html=True)
    
    with col_form:
        st.markdown("### Clinical Login")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            login_btn = st.form_submit_button("Access Clinical System", use_container_width=True)
            
            if login_btn:
                if username and password:
                    user, msg = authenticate_user(username, password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.username = user[0]
                        st.session_state.role = user[2]
                        st.success(f"Access granted! Welcome {user[0]}!")
                        st.rerun()
                    else:
                        st.error(f"{msg}")
                else:
                    st.error("Please enter both username and password")
    
    st.markdown("<div style='text-align:center; margin-top:2rem;'>"
                "<small>Demo credentials: <strong>admin</strong> / <strong>admin123</strong></small>"
                "</div>", unsafe_allow_html=True)

def main():
    load_css()
    
    # Initialize session state
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
    if 'exam_step' not in st.session_state:
        st.session_state.exam_step = None

    if not st.session_state.logged_in:
        login_page()
    else:
        # Professional header
        col_header1, col_header2, col_header3 = st.columns([2, 1, 1])
        with col_header1:
            st.image("https://i.postimg.cc/qq656tks/Phantasmed-logo.png", width=150)
        with col_header2:
            st.write(f"**Clinician:** {st.session_state.username}")
            st.write(f"**Role:** {st.session_state.role}")
        with col_header3:
            if st.session_state.selected_patient:
                st.write(f"**Current Patient:** {st.session_state.selected_patient}")
            if st.button("Logout", use_container_width=True):
                # Clear all session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        
        st.markdown("---")
        main_navigation()

if __name__ == "__main__":
    main()
