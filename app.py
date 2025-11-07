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
import os

# Page configuration
st.set_page_config(
    page_title="OphtalCAM EMR",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Database setup - COMPLETE AND ROBUST
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
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Patients table - COMPLETE
    c.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            date_of_birth DATE NOT NULL,
            gender TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            address TEXT,
            id_number TEXT,
            emergency_contact TEXT,
            insurance_info TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Medical History table - COMPLETE
    c.execute('''
        CREATE TABLE IF NOT EXISTS medical_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            visit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- General Health
            general_health TEXT,
            current_medications TEXT,
            allergies TEXT,
            headaches_history TEXT,
            family_history TEXT,
            
            -- Ocular History
            ocular_history TEXT,
            previous_surgeries TEXT,
            eye_medications TEXT,
            last_eye_exam DATE,
            
            -- Social History
            smoking_status TEXT,
            alcohol_consumption TEXT,
            occupation TEXT,
            hobbies TEXT,
            
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')
    
    # Refraction Examination table - COMPLETE
    c.execute('''
        CREATE TABLE IF NOT EXISTS refraction_exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            exam_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Habitual Correction
            habitual_correction_type TEXT,
            habitual_od_sphere REAL,
            habitual_od_cylinder REAL,
            habitual_od_axis INTEGER,
            habitual_od_add REAL,
            habitual_od_va TEXT,
            habitual_os_sphere REAL,
            habitual_os_cylinder REAL,
            habitual_os_axis INTEGER,
            habitual_os_add REAL,
            habitual_os_va TEXT,
            habitual_binocular_va TEXT,
            
            -- Uncorrected Vision
            uncorrected_od_va TEXT,
            uncorrected_os_va TEXT,
            uncorrected_binocular_va TEXT,
            
            -- Objective Refraction
            objective_refraction_time TEXT,
            autorefractor_od_sphere REAL,
            autorefractor_od_cylinder REAL,
            autorefractor_od_axis INTEGER,
            autorefractor_os_sphere REAL,
            autorefractor_os_cylinder REAL,
            autorefractor_os_axis INTEGER,
            
            -- Subjective Refraction
            subjective_method TEXT,
            cycloplegic_used BOOLEAN,
            cycloplegic_type TEXT,
            cycloplegic_lot TEXT,
            cycloplegic_expiry DATE,
            cycloplegic_drops INTEGER,
            subjective_od_sphere REAL,
            subjective_od_cylinder REAL,
            subjective_od_axis INTEGER,
            subjective_os_sphere REAL,
            subjective_os_cylinder REAL,
            subjective_os_axis INTEGER,
            
            -- Binocular Tests
            binocular_balance TEXT,
            stereopsis TEXT,
            near_point_convergence TEXT,
            near_point_accommodation TEXT,
            
            -- Prescribed Correction
            prescribed_od_sphere REAL,
            prescribed_od_cylinder REAL,
            prescribed_od_axis INTEGER,
            prescribed_od_add REAL,
            prescribed_od_va TEXT,
            prescribed_os_sphere REAL,
            prescribed_os_cylinder REAL,
            prescribed_os_axis INTEGER,
            prescribed_os_add REAL,
            prescribed_os_va TEXT,
            prescribed_binocular_va TEXT,
            prescription_notes TEXT,
            
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')
    
    # Functional Tests table - COMPLETE
    c.execute('''
        CREATE TABLE IF NOT EXISTS functional_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            test_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Motility
            motility_od TEXT,
            motility_os TEXT,
            motility_notes TEXT,
            motility_device_used BOOLEAN DEFAULT 0,
            
            -- Hirschberg Test
            hirschberg_result TEXT,
            hirschberg_device_used BOOLEAN DEFAULT 0,
            
            -- Cover Tests
            cover_test_distance TEXT,
            cover_test_near TEXT,
            alternate_cover_test TEXT,
            
            -- Pupil Examination
            pupil_size_od TEXT,
            pupil_size_os TEXT,
            pupil_shape_od TEXT,
            pupil_shape_os TEXT,
            pupil_reactivity_od TEXT,
            pupil_reactivity_os TEXT,
            pupil_afferent_defect TEXT,
            pupil_device_used BOOLEAN DEFAULT 0,
            
            -- Accommodation
            accommodation_amplitude_od TEXT,
            accommodation_amplitude_os TEXT,
            near_point_accommodation_od TEXT,
            near_point_accommodation_os TEXT,
            accommodation_device_used BOOLEAN DEFAULT 0,
            
            -- Visual Fields
            confrontation_fields TEXT,
            
            -- Additional Tests
            worth_four_dot TEXT,
            bagolini_striated TEXT,
            maddox_rod TEXT,
            
            functional_notes TEXT,
            
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')
    
    # Anterior Segment Examination table - COMPLETE
    c.execute('''
        CREATE TABLE IF NOT EXISTS anterior_segment_exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            exam_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Biomicroscopy
            biomicroscopy_od TEXT,
            biomicroscopy_os TEXT,
            biomicroscopy_notes TEXT,
            biomicroscopy_device_used BOOLEAN DEFAULT 0,
            
            -- Anterior Chamber
            anterior_chamber_depth_od TEXT,
            anterior_chamber_depth_os TEXT,
            anterior_chamber_volume_od TEXT,
            anterior_chamber_volume_os TEXT,
            iridocorneal_angle_od TEXT,
            iridocorneal_angle_os TEXT,
            
            -- Pachymetry
            pachymetry_od REAL,
            pachymetry_os REAL,
            
            -- Tonometry
            tonometry_type TEXT,
            tonometry_time TEXT,
            tonometry_compensation TEXT,
            tonometry_od TEXT,
            tonometry_os TEXT,
            
            -- Additional Tests
            aberometry_notes TEXT,
            corneal_topography_notes TEXT,
            
            anterior_segment_notes TEXT,
            
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')
    
    # Posterior Segment Examination table - COMPLETE
    c.execute('''
        CREATE TABLE IF NOT EXISTS posterior_segment_exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            exam_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Fundus Examination
            fundus_exam_type TEXT,
            fundus_od TEXT,
            fundus_os TEXT,
            fundus_notes TEXT,
            fundus_device_used BOOLEAN DEFAULT 0,
            
            -- Pupillography
            pupillography_results TEXT,
            pupillography_notes TEXT,
            pupillography_device_used BOOLEAN DEFAULT 0,
            
            -- OCT
            oct_macula_od TEXT,
            oct_macula_os TEXT,
            oct_rnfl_od TEXT,
            oct_rnfl_os TEXT,
            oct_notes TEXT,
            
            posterior_segment_notes TEXT,
            
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')
    
    # Contact Lenses table - COMPLETE
    c.execute('''
        CREATE TABLE IF NOT EXISTS contact_lens_prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            prescription_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Lens Type
            lens_type TEXT NOT NULL,
            
            -- Soft Lenses
            soft_brand TEXT,
            soft_base_curve REAL,
            soft_diameter REAL,
            soft_power_od REAL,
            soft_power_os REAL,
            soft_axis_od INTEGER,
            soft_axis_os INTEGER,
            soft_add_od REAL,
            soft_add_os REAL,
            soft_color TEXT,
            soft_replacement_schedule TEXT,
            
            -- RGP Lenses
            rgp_design TEXT,
            rgp_material TEXT,
            rgp_base_curve REAL,
            rgp_secondary_curve REAL,
            rgp_diameter REAL,
            rgp_power_od REAL,
            rgp_power_os REAL,
            rgp_axis_od INTEGER,
            rgp_axis_os INTEGER,
            rgp_add_od REAL,
            rgp_add_os REAL,
            rgp_edge_lift REAL,
            rgp_optical_zone REAL,
            rgp_color TEXT,
            rgp_stabilization TEXT,
            
            -- Scleral Lenses
            scleral_design TEXT,
            scleral_material TEXT,
            scleral_diameter REAL,
            scleral_clearance REAL,
            scleral_power_od REAL,
            scleral_power_os REAL,
            scleral_axis_od INTEGER,
            scleral_axis_os INTEGER,
            scleral_add_od REAL,
            scleral_add_os REAL,
            
            -- Special Lenses
            special_lens_type TEXT,
            special_parameters TEXT,
            
            -- General
            wearing_schedule TEXT,
            care_solution TEXT,
            follow_up_date DATE,
            fitting_notes TEXT,
            
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')
    
    # Patient Groups table
    c.execute('''
        CREATE TABLE IF NOT EXISTS patient_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Patient Group Assignments
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
    
    # Appointments table
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
    
    # Insert default admin user
    try:
        admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                  ("admin", admin_hash, "admin"))
    except:
        pass
    
    # Insert default patient groups
    default_groups = [
        ("Corneal Ectasias", "Keratoconus, Pellucid Marginal Degeneration, Post-LASIK Ectasia"),
        ("Glaucoma", "Primary open-angle glaucoma, Angle-closure glaucoma, Secondary glaucoma"),
        ("Cataracts", "Nuclear, Cortical, Posterior Subcapsular, Congenital cataracts"),
        ("Retinal Diseases", "AMD, Diabetic retinopathy, Retinal detachment, Macular diseases"),
        ("Contact Lens Patients", "All patients using contact lenses"),
        ("Pediatric Ophthalmology", "Children eye conditions, Amblyopia, Strabismus"),
        ("Dry Eye Syndrome", "Aqueous deficient, Evaporative dry eye, MGD"),
        ("Neuro-ophthalmology", "Optic neuritis, Papilledema, Cranial nerve palsies")
    ]
    
    for group_name, description in default_groups:
        try:
            c.execute("INSERT OR IGNORE INTO patient_groups (group_name, description) VALUES (?, ?)", 
                     (group_name, description))
        except:
            pass
    
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
    
    c.execute("SELECT username, password_hash, role FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    
    if user and verify_password(password, user[1]):
        return user, "Success"
    return None, "Invalid credentials"

def get_todays_appointments():
    conn = init_db()
    today = datetime.now().date()
    try:
        appointments = pd.read_sql('''
            SELECT a.*, p.first_name, p.last_name, p.patient_id 
            FROM appointments a 
            JOIN patients p ON a.patient_id = p.id 
            WHERE DATE(a.appointment_date) = ? 
            ORDER BY a.appointment_date
        ''', conn, params=(today,))
        return appointments
    except:
        return pd.DataFrame()

def get_patient_stats():
    conn = init_db()
    try:
        total_patients = pd.read_sql("SELECT COUNT(*) as count FROM patients", conn).iloc[0]['count']
        today = datetime.now().date()
        today_exams = pd.read_sql('''
            SELECT COUNT(*) as count FROM appointments 
            WHERE DATE(appointment_date) = ?
        ''', conn, params=(today,)).iloc[0]['count']
        total_cl = pd.read_sql("SELECT COUNT(*) as count FROM contact_lens_prescriptions", conn).iloc[0]['count']
        return total_patients, today_exams, total_cl
    except:
        return 0, 0, 0

# Custom CSS for professional medical appearance
def load_css():
    st.markdown("""
    <style>
    .main-header {
        font-family: 'Arial', sans-serif;
    }
    .metric-card {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem;
        border: 1px solid #e0e0e0;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        margin: 0.5rem 0;
        font-family: 'Arial', sans-serif;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        font-family: 'Arial', sans-serif;
    }
    .appointment-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #1e3c72;
        font-family: 'Arial', sans-serif;
    }
    .protocol-section {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border: 1px solid #e0e0e0;
        border-left: 4px solid #1e3c72;
        font-family: 'Arial', sans-serif;
    }
    .sub-section {
        background-color: #fafafa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border: 1px solid #e0e0e0;
        font-family: 'Arial', sans-serif;
    }
    .eye-section {
        background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border: 1px solid #e0e0e0;
        font-family: 'Arial', sans-serif;
    }
    .device-button {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 0.2rem;
        font-family: 'Arial', sans-serif;
        font-weight: 500;
    }
    .exam-step {
        background-color: #e3f2fd;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        margin: 0.2rem;
        display: inline-block;
        font-size: 0.9rem;
        font-family: 'Arial', sans-serif;
    }
    .exam-step.active {
        background-color: #1e3c72;
        color: white;
        font-weight: bold;
    }
    .medical-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-left: 4px solid #fdcb6e;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        font-family: 'Arial', sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

# DASHBOARD - Professional medical dashboard
def show_dashboard():
    st.markdown("<h1 style='text-align: center; font-family: Arial, sans-serif;'>OphtalCAM Clinical Dashboard</h1>", unsafe_allow_html=True)
    
    # Date filter
    col_filter = st.columns([2, 1, 1, 1])
    with col_filter[0]:
        view_option = st.selectbox("Time View", ["Today", "This Week", "This Month"], key="view_filter")
    with col_filter[3]:
        if st.button("+ New Appointment", use_container_width=True):
            st.session_state.menu = "Schedule Appointment"
            st.rerun()
    
    # Statistics cards
    total_patients, today_exams, total_cl = get_patient_stats()
    
    col_metrics = st.columns(3)
    with col_metrics[0]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_patients}</div>
            <div class="metric-label">Registered Patients</div>
        </div>
        """, unsafe_allow_html=True)
    with col_metrics[1]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{today_exams}</div>
            <div class="metric-label">Scheduled Examinations</div>
        </div>
        """, unsafe_allow_html=True)
    with col_metrics[2]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_cl}</div>
            <div class="metric-label">Contact Lens Patients</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Main content area
    col_main = st.columns([2, 1])
    
    with col_main[0]:
        st.subheader("Today's Clinical Schedule")
        appointments = get_todays_appointments()
        
        if not appointments.empty:
            for _, apt in appointments.iterrows():
                apt_time = pd.to_datetime(apt['appointment_date']).strftime('%H:%M')
                with st.container():
                    st.markdown(f"""
                    <div class="appointment-card">
                        <strong>{apt_time}</strong> - {apt['first_name']} {apt['last_name']} ({apt['patient_id']})<br>
                        <small>Type: {apt['appointment_type']} | Status: {apt['status']}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col_btn = st.columns(2)
                    with col_btn[0]:
                        if st.button("Begin Examination", key=f"start_{apt['id']}", use_container_width=True):
                            st.session_state.selected_patient = apt['patient_id']
                            st.session_state.menu = "Examination Protocol"
                            st.session_state.exam_step = "medical_history"
                            st.rerun()
                    with col_btn[1]:
                        if st.button("Patient Details", key=f"details_{apt['id']}", use_container_width=True):
                            st.session_state.selected_patient = apt['patient_id']
                            st.session_state.menu = "Patient Records"
                            st.rerun()
        else:
            st.info("No appointments scheduled for today.")
    
    with col_main[1]:
        st.subheader("Clinical Calendar")
        
        # Professional mini calendar
        today = datetime.now()
        cal = calendar.monthcalendar(today.year, today.month)
        
        st.write(f"**{today.strftime('%B %Y')}**")
        
        # Calendar header
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        cols = st.columns(7)
        for i, day in enumerate(days):
            cols[i].write(f"**{day}**")
        
        # Calendar days
        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day == 0:
                    cols[i].write("")
                else:
                    day_str = str(day)
                    if day == today.day:
                        cols[i].markdown(f"<div style='background-color: #1e3c72; color: white; padding: 5px; border-radius: 50%; text-align: center;'><strong>{day_str}</strong></div>", unsafe_allow_html=True)
                    else:
                        cols[i].write(day_str)
        
        st.markdown("---")
        st.subheader("Clinical Actions")
        
        if st.button("🆕 New Patient Registration", use_container_width=True):
            st.session_state.menu = "Patient Registration"
            st.rerun()
        
        if st.button("🔍 Patient Search & Records", use_container_width=True):
            st.session_state.menu = "Patient Search"
            st.rerun()
        
        if st.button("📊 Clinical Analytics", use_container_width=True):
            st.session_state.menu = "Analytics"
            st.rerun()

# MEDICAL HISTORY - Comprehensive medical history
def medical_history():
    st.subheader("📋 Comprehensive Medical History & Anamnesis")
    
    if 'selected_patient' not in st.session_state:
        st.error("❌ No patient selected. Please select a patient from the Dashboard.")
        return
    
    patient_id = st.session_state.selected_patient
    
    # Get patient info
    try:
        patient_info = pd.read_sql("SELECT * FROM patients WHERE patient_id = ?", conn, params=(patient_id,)).iloc[0]
        st.markdown(f"### Patient: {patient_info['first_name']} {patient_info['last_name']} (ID: {patient_info['patient_id']})")
    except:
        st.error("❌ Patient not found in database.")
        return
    
    with st.form("medical_history_form"):
        st.markdown("#### General Health History")
        
        col1, col2 = st.columns(2)
        
        with col1:
            general_health = st.text_area("General Health Status*", 
                                        placeholder="Chronic conditions, systemic diseases, hospitalizations...", 
                                        height=100)
            current_medications = st.text_area("Current Medications*", 
                                            placeholder="List all current medications with dosages...", 
                                            height=100)
            allergies = st.text_area("Allergies & Reactions*", 
                                   placeholder="Drug allergies, environmental allergies, reactions...", 
                                   height=80)
        
        with col2:
            headaches_history = st.text_area("Headaches & Migraines", 
                                           placeholder="Frequency, type, duration, triggers, treatment...", 
                                           height=80)
            family_history = st.text_area("Family Medical History*", 
                                        placeholder="Ocular and systemic conditions in family members...", 
                                        height=100)
        
        st.markdown("#### Ocular History")
        
        col_ocular1, col_ocular2 = st.columns(2)
        
        with col_ocular1:
            ocular_history = st.text_area("Ocular History & Conditions*", 
                                        placeholder="Previous eye diseases, conditions, treatments...", 
                                        height=100)
            previous_surgeries = st.text_area("Previous Ocular Surgeries", 
                                            placeholder="Cataract surgery, LASIK, retinal procedures...", 
                                            height=80)
        
        with col_ocular2:
            eye_medications = st.text_area("Ocular Medications", 
                                         placeholder="Current eye drops, ointments, treatments...", 
                                         height=80)
            last_eye_exam = st.date_input("Last Comprehensive Eye Examination")
        
        st.markdown("#### Social & Lifestyle History")
        
        col_social1, col_social2 = st.columns(2)
        
        with col_social1:
            smoking_status = st.selectbox("Smoking Status", 
                                        ["Non-smoker", "Former smoker", "Current smoker", "Unknown"])
            alcohol_consumption = st.selectbox("Alcohol Consumption", 
                                            ["None", "Occasional", "Moderate", "Heavy"])
        
        with col_social2:
            occupation = st.text_input("Occupation", placeholder="Current occupation...")
            hobbies = st.text_area("Hobbies & Activities", 
                                 placeholder="Sports, reading, computer use, other activities...", 
                                 height=60)
        
        st.markdown("#### Previous Medical Documents")
        previous_reports = st.file_uploader("Upload Previous Medical Reports", 
                                          type=['pdf', 'jpg', 'png', 'docx'], 
                                          accept_multiple_files=True,
                                          help="Upload previous examination reports, lab results, imaging studies...")
        
        if previous_reports:
            st.info(f"📎 {len(previous_reports)} file(s) ready for upload")
        
        st.markdown("---")
        submit_history = st.form_submit_button("💾 Save Medical History & Continue to Refraction Examination", 
                                             use_container_width=True)
        
        if submit_history:
            if not general_health or not current_medications or not allergies or not family_history or not ocular_history:
                st.error("❌ Please complete all required fields (marked with *)")
            else:
                try:
                    c = conn.cursor()
                    
                    # Save medical history
                    c.execute('''
                        INSERT INTO medical_history 
                        (patient_id, general_health, current_medications, allergies, headaches_history, 
                         family_history, ocular_history, previous_surgeries, eye_medications, last_eye_exam,
                         smoking_status, alcohol_consumption, occupation, hobbies)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (patient_info['id'], general_health, current_medications, allergies, headaches_history,
                         family_history, ocular_history, previous_surgeries, eye_medications, last_eye_exam,
                         smoking_status, alcohol_consumption, occupation, hobbies))
                    
                    conn.commit()
                    st.success("✅ Comprehensive medical history saved successfully!")
                    
                    # Auto-navigate to refraction
                    st.session_state.exam_step = "refraction"
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Database error: {str(e)}")

# REFRACTION EXAMINATION - Complete professional refraction
def refraction_examination():
    st.subheader("🔍 Comprehensive Refraction Examination")
    
    if 'selected_patient' not in st.session_state:
        st.error("❌ Please complete medical history first.")
        return
    
    patient_id = st.session_state.selected_patient
    
    with st.form("refraction_form"):
        st.markdown("#### 1. Habitual Correction Analysis")
        
        col_habit1, col_habit2 = st.columns(2)
        
        with col_habit1:
            habitual_type = st.selectbox("Type of Current Correction*", 
                                       ["None", "Spectacles", "Soft Contact Lenses", "RGP Contact Lenses", 
                                        "Scleral Lenses", "Ortho-K", "Other"])
            
            st.markdown("**Right Eye (OD)**")
            habitual_od_sph = st.number_input("Sphere OD", value=0.0, step=0.25, format="%.2f")
            habitual_od_cyl = st.number_input("Cylinder OD", value=0.0, step=0.25, format="%.2f")
            habitual_od_axis = st.number_input("Axis OD", min_value=0, max_value=180, value=0)
            habitual_od_add = st.number_input("Add OD", value=0.0, step=0.25, format="%.2f")
            habitual_od_va = st.text_input("Visual Acuity OD*", placeholder="e.g., 20/20, 6/6, 0.0")
        
        with col_habit2:
            st.markdown("**Left Eye (OS)**")
            habitual_os_sph = st.number_input("Sphere OS", value=0.0, step=0.25, format="%.2f")
            habitual_os_cyl = st.number_input("Cylinder OS", value=0.0, step=0.25, format="%.2f")
            habitual_os_axis = st.number_input("Axis OS", min_value=0, max_value=180, value=0)
            habitual_os_add = st.number_input("Add OS", value=0.0, step=0.25, format="%.2f")
            habitual_os_va = st.text_input("Visual Acuity OS*", placeholder="e.g., 20/20, 6/6, 0.0")
            habitual_bin_va = st.text_input("Binocular Visual Acuity*", placeholder="e.g., 20/20, 6/6, 0.0")
        
        st.markdown("#### 2. Uncorrected Visual Acuity")
        
        col_uncorr = st.columns(3)
        with col_uncorr[0]:
            uncorrected_od_va = st.text_input("Uncorrected VA OD*", placeholder="20/20")
        with col_uncorr[1]:
            uncorrected_os_va = st.text_input("Uncorrected VA OS*", placeholder="20/20")
        with col_uncorr[2]:
            uncorrected_bin_va = st.text_input("Uncorrected Binocular VA*", placeholder="20/20")
        
        st.markdown("#### 3. Objective Refraction (Autorefractor)")
        
        col_obj = st.columns(2)
        with col_obj[0]:
            objective_time = st.text_input("Time of Measurement*", placeholder="HH:MM (24h format)")
            st.markdown("**Right Eye (OD)**")
            autorefractor_od_sph = st.number_input("Autorefractor Sphere OD", value=0.0, step=0.25, format="%.2f")
            autorefractor_od_cyl = st.number_input("Autorefractor Cylinder OD", value=0.0, step=0.25, format="%.2f")
            autorefractor_od_axis = st.number_input("Autorefractor Axis OD", min_value=0, max_value=180, value=0)
        
        with col_obj[1]:
            st.markdown("**Left Eye (OS)**")
            autorefractor_os_sph = st.number_input("Autorefractor Sphere OS", value=0.0, step=0.25, format="%.2f")
            autorefractor_os_cyl = st.number_input("Autorefractor Cylinder OS", value=0.0, step=0.25, format="%.2f")
            autorefractor_os_axis = st.number_input("Autorefractor Axis OS", min_value=0, max_value=180, value=0)
        
        st.markdown("#### 4. Subjective Refraction")
        
        col_subj = st.columns(2)
        with col_subj[0]:
            subjective_method = st.selectbox("Refraction Method*", ["Fogging Technique", "With Cycloplegic"])
            
            if subjective_method == "With Cycloplegic":
                cycloplegic_used = True
                cycloplegic_type = st.text_input("Cycloplegic Agent*", placeholder="e.g., Cyclopentolate 1%")
                cycloplegic_lot = st.text_input("Lot Number")
                cycloplegic_expiry = st.date_input("Expiry Date")
                cycloplegic_drops = st.number_input("Number of Drops", min_value=1, max_value=4, value=1)
            else:
                cycloplegic_used = False
                cycloplegic_type = None
                cycloplegic_lot = None
                cycloplegic_expiry = None
                cycloplegic_drops = None
            
            st.markdown("**Right Eye (OD)**")
            subjective_od_sph = st.number_input("Subjective Sphere OD*", value=0.0, step=0.25, format="%.2f")
            subjective_od_cyl = st.number_input("Subjective Cylinder OD", value=0.0, step=0.25, format="%.2f")
            subjective_od_axis = st.number_input("Subjective Axis OD", min_value=0, max_value=180, value=0)
        
        with col_subj[1]:
            st.markdown("**Left Eye (OS)**")
            subjective_os_sph = st.number_input("Subjective Sphere OS*", value=0.0, step=0.25, format="%.2f")
            subjective_os_cyl = st.number_input("Subjective Cylinder OS", value=0.0, step=0.25, format="%.2f")
            subjective_os_axis = st.number_input("Subjective Axis OS", min_value=0, max_value=180, value=0)
        
        st.markdown("#### 5. Binocular Vision Assessment")
        
        binocular_balance = st.selectbox("Binocular Balance*", 
                                       ["Balanced", "OD dominant", "OS dominant", "Unbalanced"])
        stereopsis = st.text_input("Stereoacuity", placeholder="e.g., 40 arc seconds")
        near_point_convergence = st.text_input("Near Point of Convergence", placeholder="e.g., 6 cm")
        near_point_accommodation = st.text_input("Near Point of Accommodation", placeholder="e.g., 8 cm")
        
        st.markdown("#### 6. Final Prescription")
        
        col_pres = st.columns(2)
        with col_pres[0]:
            st.markdown("**Right Eye (OD)**")
            prescribed_od_sph = st.number_input("Final Sphere OD*", value=0.0, step=0.25, format="%.2f")
            prescribed_od_cyl = st.number_input("Final Cylinder OD", value=0.0, step=0.25, format="%.2f")
            prescribed_od_axis = st.number_input("Final Axis OD", min_value=0, max_value=180, value=0)
            prescribed_od_add = st.number_input("Final Add OD", value=0.0, step=0.25, format="%.2f")
            prescribed_od_va = st.text_input("Final VA OD*", placeholder="20/20")
        
        with col_pres[1]:
            st.markdown("**Left Eye (OS)**")
            prescribed_os_sph = st.number_input("Final Sphere OS*", value=0.0, step=0.25, format="%.2f")
            prescribed_os_cyl = st.number_input("Final Cylinder OS", value=0.0, step=0.25, format="%.2f")
            prescribed_os_axis = st.number_input("Final Axis OS", min_value=0, max_value=180, value=0)
            prescribed_os_add = st.number_input("Final Add OS", value=0.0, step=0.25, format="%.2f")
            prescribed_os_va = st.text_input("Final VA OS*", placeholder="20/20")
        
        prescribed_bin_va = st.text_input("Final Binocular VA*", placeholder="20/20")
        prescription_notes = st.text_area("Prescription Notes & Rationale", 
                                        placeholder="Clinical reasoning, special considerations, anisometropia management...",
                                        height=80)
        
        st.markdown("---")
        submit_refraction = st.form_submit_button("💾 Save Refraction & Continue to Functional Tests", 
                                                use_container_width=True)
        
        if submit_refraction:
            # Validate required fields
            required_fields = [
                habitual_od_va, habitual_os_va, habitual_bin_va,
                uncorrected_od_va, uncorrected_os_va, uncorrected_bin_va,
                objective_time, prescribed_od_va, prescribed_os_va, prescribed_bin_va
            ]
            
            if any(not field for field in required_fields):
                st.error("❌ Please complete all required fields (marked with *)")
            else:
                try:
                    patient_info = pd.read_sql("SELECT id FROM patients WHERE patient_id = ?", conn, params=(patient_id,)).iloc[0]
                    
                    c = conn.cursor()
                    c.execute('''
                        INSERT INTO refraction_exams 
                        (patient_id, habitual_correction_type, habitual_od_sphere, habitual_od_cylinder, habitual_od_axis,
                         habitual_od_add, habitual_od_va, habitual_os_sphere, habitual_os_cylinder, habitual_os_axis,
                         habitual_os_add, habitual_os_va, habitual_binocular_va, uncorrected_od_va, uncorrected_os_va,
                         uncorrected_binocular_va, objective_refraction_time, autorefractor_od_sphere, autorefractor_od_cylinder,
                         autorefractor_od_axis, autorefractor_os_sphere, autorefractor_os_cylinder, autorefractor_os_axis,
                         subjective_method, cycloplegic_used, cycloplegic_type, cycloplegic_lot, cycloplegic_expiry,
                         cycloplegic_drops, subjective_od_sphere, subjective_od_cylinder, subjective_od_axis,
                         subjective_os_sphere, subjective_os_cylinder, subjective_os_axis, binocular_balance,
                         stereopsis, near_point_convergence, near_point_accommodation, prescribed_od_sphere,
                         prescribed_od_cylinder, prescribed_od_axis, prescribed_od_add, prescribed_od_va,
                         prescribed_os_sphere, prescribed_os_cylinder, prescribed_os_axis, prescribed_os_add,
                         prescribed_os_va, prescribed_binocular_va, prescription_notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (patient_info['id'], habitual_type, habitual_od_sph, habitual_od_cyl, habitual_od_axis,
                         habitual_od_add, habitual_od_va, habitual_os_sph, habitual_os_cyl, habitual_os_axis,
                         habitual_os_add, habitual_os_va, habitual_bin_va, uncorrected_od_va, uncorrected_os_va,
                         uncorrected_bin_va, objective_time, autorefractor_od_sph, autorefractor_od_cyl,
                         autorefractor_od_axis, autorefractor_os_sph, autorefractor_os_cyl, autorefractor_os_axis,
                         subjective_method, cycloplegic_used, cycloplegic_type, cycloplegic_lot, cycloplegic_expiry,
                         cycloplegic_drops, subjective_od_sph, subjective_od_cyl, subjective_od_axis,
                         subjective_os_sph, subjective_os_cyl, subjective_os_axis, binocular_balance,
                         stereopsis, near_point_convergence, near_point_accommodation, prescribed_od_sph,
                         prescribed_od_cyl, prescribed_od_axis, prescribed_od_add, prescribed_od_va,
                         prescribed_os_sph, prescribed_os_cyl, prescribed_os_axis, prescribed_os_add,
                         prescribed_os_va, prescribed_bin_va, prescription_notes))
                    
                    conn.commit()
                    st.success("✅ Comprehensive refraction examination saved successfully!")
                    
                    # Auto-navigate to functional tests
                    st.session_state.exam_step = "functional_tests"
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Database error: {str(e)}")

# [OSTALE FUNKCIJE - functional_tests(), anterior_segment_examination(), posterior_segment_examination(), contact_lenses(), itd.]

# Placeholder for other complete functions
def functional_tests():
    st.subheader("🧪 Functional Vision Tests")
    st.info("Complete functional tests module implementation...")
    
    if st.button("Continue to Anterior Segment Examination", use_container_width=True):
        st.session_state.exam_step = "anterior_segment"
        st.rerun()

def anterior_segment_examination():
    st.subheader("🔬 Anterior Segment Examination")
    st.info("Complete anterior segment examination module implementation...")
    
    if st.button("Continue to Posterior Segment Examination", use_container_width=True):
        st.session_state.exam_step = "posterior_segment"
        st.rerun()

def posterior_segment_examination():
    st.subheader("👁️ Posterior Segment Examination")
    st.info("Complete posterior segment examination module implementation...")
    
    if st.button("Continue to Contact Lens Fitting", use_container_width=True):
        st.session_state.exam_step = "contact_lenses"
        st.rerun()

def contact_lenses():
    st.subheader("👓 Contact Lens Fitting & Prescription")
    st.info("Complete contact lens fitting module implementation...")
    
    if st.button("Complete Examination & Generate Report", use_container_width=True):
        st.session_state.exam_step = "generate_report"
        st.rerun()

def generate_report():
    st.subheader("📄 Generate Clinical Report")
    st.info("Complete report generation module implementation...")
    
    if st.button("Return to Dashboard", use_container_width=True):
        st.session_state.exam_step = None
        st.session_state.selected_patient = None
        st.session_state.menu = "Dashboard"
        st.success("✅ Examination completed successfully!")
        st.rerun()

# PATIENT REGISTRATION - Complete professional registration
def patient_registration():
    st.subheader("👤 New Patient Registration")
    
    with st.form("patient_registration_form"):
        st.markdown("#### Personal Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            patient_id = st.text_input("Patient ID*", placeholder="Unique identifier (e.g., PAT2024001)")
            first_name = st.text_input("First Name*", placeholder="Legal first name")
            last_name = st.text_input("Last Name*", placeholder="Legal last name")
            date_of_birth = st.date_input("Date of Birth*", 
                                        value=datetime.now() - timedelta(days=365*30),
                                        max_value=datetime.now())
            gender = st.selectbox("Gender*", ["Male", "Female", "Other", "Prefer not to say"])
        
        with col2:
            phone = st.text_input("Phone Number*", placeholder="+1234567890")
            email = st.text_input("Email Address", placeholder="patient@example.com")
            address = st.text_area("Home Address", placeholder="Full residential address", height=60)
            id_number = st.text_input("ID Number", placeholder="National ID or passport number")
        
        st.markdown("#### Emergency & Insurance Information")
        
        col_emergency = st.columns(2)
        with col_emergency[0]:
            emergency_contact = st.text_input("Emergency Contact", placeholder="Name and relationship")
        with col_emergency[1]:
            insurance_info = st.text_input("Insurance Information", placeholder="Insurance provider and number")
        
        submit_button = st.form_submit_button("Register New Patient", use_container_width=True)
        
        if submit_button:
            if not all([patient_id, first_name, last_name, phone]):
                st.error("❌ Please complete all required fields (marked with *)")
            else:
                try:
                    c = conn.cursor()
                    c.execute('''
                        INSERT INTO patients 
                        (patient_id, first_name, last_name, date_of_birth, gender, phone, email, address, id_number, emergency_contact, insurance_info)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (patient_id, first_name, last_name, date_of_birth, gender, phone, email, address, id_number, emergency_contact, insurance_info))
                    
                    conn.commit()
                    st.success(f"✅ Patient {first_name} {last_name} registered successfully!")
                    
                except sqlite3.IntegrityError:
                    st.error("❌ Patient ID already exists. Please use a unique identifier.")
                except Exception as e:
                    st.error(f"❌ Database error: {str(e)}")

# PATIENT SEARCH - Professional patient search
def patient_search():
    st.subheader("🔍 Patient Search & Medical Records")
    
    col_search = st.columns([2, 1])
    with col_search[0]:
        search_term = st.text_input("Search Patients", 
                                  placeholder="Patient ID, name, phone number, or ID number...")
    with col_search[1]:
        search_type = st.selectbox("Search By", ["All Fields", "Patient ID", "Name", "Phone"])
    
    if search_term:
        try:
            if search_type == "All Fields":
                patients = pd.read_sql('''
                    SELECT * FROM patients 
                    WHERE patient_id LIKE ? OR first_name LIKE ? OR last_name LIKE ? OR phone LIKE ? OR id_number LIKE ?
                    ORDER BY last_name, first_name
                ''', conn, params=(f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
            elif search_type == "Patient ID":
                patients = pd.read_sql('''
                    SELECT * FROM patients WHERE patient_id LIKE ? ORDER BY patient_id
                ''', conn, params=(f'%{search_term}%',))
            elif search_type == "Name":
                patients = pd.read_sql('''
                    SELECT * FROM patients 
                    WHERE first_name LIKE ? OR last_name LIKE ? 
                    ORDER BY last_name, first_name
                ''', conn, params=(f'%{search_term}%', f'%{search_term}%'))
            else:  # Phone
                patients = pd.read_sql('''
                    SELECT * FROM patients WHERE phone LIKE ? ORDER BY last_name, first_name
                ''', conn, params=(f'%{search_term}%',))
            
            if not patients.empty:
                st.success(f"🔍 Found {len(patients)} patient(s)")
                
                for _, patient in patients.iterrows():
                    with st.expander(f"📁 {patient['patient_id']} - {patient['first_name']} {patient['last_name']}"):
                        col_info1, col_info2 = st.columns(2)
                        
                        with col_info1:
                            st.write(f"**Date of Birth:** {patient['date_of_birth']}")
                            st.write(f"**Gender:** {patient['gender']}")
                            st.write(f"**Phone:** {patient['phone']}")
                            if patient['email']:
                                st.write(f"**Email:** {patient['email']}")
                        
                        with col_info2:
                            if patient['address']:
                                st.write(f"**Address:** {patient['address']}")
                            if patient['id_number']:
                                st.write(f"**ID Number:** {patient['id_number']}")
                            if patient['emergency_contact']:
                                st.write(f"**Emergency Contact:** {patient['emergency_contact']}")
                        
                        st.markdown("---")
                        col_actions = st.columns(4)
                        
                        with col_actions[0]:
                            if st.button("Begin Examination", key=f"exam_{patient['id']}", use_container_width=True):
                                st.session_state.selected_patient = patient['patient_id']
                                st.session_state.menu = "Examination Protocol"
                                st.session_state.exam_step = "medical_history"
                                st.rerun()
                        
                        with col_actions[1]:
                            if st.button("View History", key=f"history_{patient['id']}", use_container_width=True):
                                st.session_state.selected_patient = patient['patient_id']
                                st.session_state.menu = "Patient History"
                                st.rerun()
                        
                        with col_actions[2]:
                            if st.button("Contact Lenses", key=f"cl_{patient['id']}", use_container_width=True):
                                st.session_state.selected_patient = patient['patient_id']
                                st.session_state.menu = "Contact Lenses"
                                st.rerun()
                        
                        with col_actions[3]:
                            if st.button("Schedule", key=f"schedule_{patient['id']}", use_container_width=True):
                                st.session_state.selected_patient = patient['patient_id']
                                st.session_state.menu = "Schedule Appointment"
                                st.rerun()
            else:
                st.info("No patients found matching your search criteria.")
                
        except Exception as e:
            st.error(f"❌ Search error: {str(e)}")

# MAIN NAVIGATION - Professional navigation
def main_navigation():
    st.sidebar.title("👁️ OphtalCAM EMR")
    st.sidebar.markdown("---")
    
    if 'menu' not in st.session_state:
        st.session_state.menu = "Dashboard"
    if 'exam_step' not in st.session_state:
        st.session_state.exam_step = None
    
    # Main clinical menu
    menu_options = [
        "Dashboard",
        "Patient Registration", 
        "Patient Search",
        "Examination Protocol",
        "Contact Lenses",
        "Schedule Appointment",
        "Clinical Analytics",
        "Patient Groups",
        "System Settings"
    ]
    
    menu = st.sidebar.selectbox("Clinical Navigation", menu_options, 
                              index=menu_options.index(st.session_state.menu))
    
    st.session_state.menu = menu
    
    # Examination workflow
    if st.session_state.exam_step:
        st.sidebar.markdown("---")
        st.sidebar.subheader("Examination Protocol")
        
        exam_steps = [
            ("medical_history", "1. Medical History"),
            ("refraction", "2. Refraction"), 
            ("functional_tests", "3. Functional Tests"),
            ("anterior_segment", "4. Anterior Segment"),
            ("posterior_segment", "5. Posterior Segment"),
            ("contact_lenses", "6. Contact Lenses"),
            ("generate_report", "7. Clinical Report")
        ]
        
        for step, label in exam_steps:
            if step == st.session_state.exam_step:
                st.sidebar.markdown(f"<div class='exam-step active'>{label}</div>", unsafe_allow_html=True)
            else:
                st.sidebar.markdown(f"<div class='exam-step'>{label}</div>", unsafe_allow_html=True)
    
    # User info
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Clinician:** {st.session_state.username}")
    st.sidebar.markdown(f"**Role:** {st.session_state.role}")
    
    # Render current page
    if st.session_state.exam_step:
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
        if menu == "Dashboard":
            show_dashboard()
        elif menu == "Patient Registration":
            patient_registration()
        elif menu == "Patient Search":
            patient_search()
        elif menu == "Examination Protocol":
            st.info("👆 Select a patient from Dashboard or Patient Search to begin comprehensive examination.")
        elif menu == "Contact Lenses":
            st.info("👆 Begin an examination or select a patient to access contact lens fitting.")
        elif menu == "Schedule Appointment":
            st.info("Appointment scheduling module - Implementation in progress")
        elif menu == "Clinical Analytics":
            st.info("Clinical analytics module - Implementation in progress")
        elif menu == "Patient Groups":
            st.info("Patient groups management - Implementation in progress")
        elif menu == "System Settings":
            st.info("System settings module - Implementation in progress")

# LOGIN PAGE - Professional login
def login_page():
    st.markdown("""
    <style>
    .login-container {
        max-width: 500px;
        margin: 0 auto;
        padding: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Professional header
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.image("https://i.postimg.cc/PrRFzQLv/Logo-Transparency-01.png", width=400)
        st.markdown("<h3 style='text-align: center;'>Ophthalmology Electronic Medical Records</h3>", unsafe_allow_html=True)
    
    with col2:
        st.image("https://i.postimg.cc/qq656tks/Phantasmed-logo.png", width=250)
    
    st.markdown("---")
    
    # Secure login form
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h4 style='text-align: center;'>Secure Clinical Access</h4>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Enter your username")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
            login_button = st.form_submit_button("🚀 Access Clinical System", use_container_width=True)
            
            if login_button:
                if username and password:
                    user, message = authenticate_user(username, password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.username = user[0]
                        st.session_state.role = user[2]
                        st.success(f"🔓 Access granted. Welcome Dr. {user[0]}!")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("❌ Please enter both username and password")
        
        # Security notice
        st.markdown("""
        <div style='text-align: center; margin-top: 2rem; padding: 1rem; background-color: #f8f9fa; border-radius: 5px;'>
        <small>🔐 <strong>Security Notice:</strong> This system contains protected health information.<br>
        Unauthorized access is prohibited.</small>
        </div>
        """, unsafe_allow_html=True)
        
        # Demo access
        st.markdown("""
        <div style='text-align: center; margin-top: 1rem;'>
        <small><strong>Demo Access:</strong><br>
        Username: <code>admin</code><br>
        Password: <code>admin123</code></small>
        </div>
        """, unsafe_allow_html=True)

# MAIN FUNCTION
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
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.image("https://i.postimg.cc/PrRFzQLv/Logo-Transparency-01.png", width=300)
        
        with col2:
            st.write("")  # Spacer
        
        with col3:
            st.write(f"**Clinician:** {st.session_state.username}")
            st.write(f"**Role:** {st.session_state.role}")
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.session_state.role = None
                st.session_state.selected_patient = None
                st.session_state.menu = "Dashboard"
                st.session_state.exam_step = None
                st.rerun()
        
        st.markdown("---")
        
        main_navigation()

if __name__ == "__main__":
    main()
