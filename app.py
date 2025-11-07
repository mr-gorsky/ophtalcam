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
    
    # Patient Medical History table
    c.execute('''
        CREATE TABLE IF NOT EXISTS patient_medical_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            visit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- General Health
            general_health TEXT,
            medications TEXT,
            allergies TEXT,
            headaches TEXT,
            family_history TEXT,
            eye_history TEXT,
            
            -- Uploaded documents
            previous_reports_path TEXT,
            
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')
    
    # Refraction Examination table
    c.execute('''
        CREATE TABLE IF NOT EXISTS refraction_examinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            examination_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Habitual Correction
            habitual_correction_type TEXT,
            habitual_od_sphere REAL,
            habitual_od_cylinder REAL,
            habitual_od_axis INTEGER,
            habitual_os_sphere REAL,
            habitual_os_cylinder REAL,
            habitual_os_axis INTEGER,
            habitual_od_add REAL,
            habitual_os_add REAL,
            habitual_od_va TEXT,
            habitual_os_va TEXT,
            habitual_binocular_va TEXT,
            
            -- Vision without correction
            uncorrected_od_va TEXT,
            uncorrected_os_va TEXT,
            uncorrected_binocular_va TEXT,
            
            -- Objective Refraction
            objective_time TEXT,
            objective_od_sphere REAL,
            objective_od_cylinder REAL,
            objective_od_axis INTEGER,
            objective_os_sphere REAL,
            objective_os_cylinder REAL,
            objective_os_axis INTEGER,
            
            -- Subjective Monocular Refraction
            subjective_method TEXT,
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
            
            -- Binocular Correction
            binocular_correction_va TEXT,
            binocular_balance TEXT,
            
            -- Prescribed Correction
            prescribed_od_sphere REAL,
            prescribed_od_cylinder REAL,
            prescribed_od_axis INTEGER,
            prescribed_os_sphere REAL,
            prescribed_os_cylinder REAL,
            prescribed_os_axis INTEGER,
            prescribed_od_add REAL,
            prescribed_os_add REAL,
            prescribed_od_va TEXT,
            prescribed_os_va TEXT,
            prescribed_binocular_va TEXT,
            prescription_notes TEXT,
            
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')
    
    # Functional Tests table
    c.execute('''
        CREATE TABLE IF NOT EXISTS functional_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            test_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Motility
            motility_notes TEXT,
            motility_device_used BOOLEAN DEFAULT 0,
            
            -- Hirschberg Test
            hirschberg_result TEXT,
            hirschberg_device_used BOOLEAN DEFAULT 0,
            
            -- Near Point of Convergence
            npc_break REAL,
            npc_recovery REAL,
            npc_device_used BOOLEAN DEFAULT 0,
            
            -- Visual Field
            confrontation_field TEXT,
            
            -- Cover/Uncover Test
            cover_uncover_result TEXT,
            
            -- Pupil Test
            pupil_test_result TEXT,
            pupil_device_used BOOLEAN DEFAULT 0,
            
            -- Accommodation
            accommodation_method TEXT,
            npa_result TEXT,
            accommodation_device_used BOOLEAN DEFAULT 0,
            accommodation_notes TEXT,
            
            -- Binocular Tests
            binocular_tests_notes TEXT,
            
            -- General Notes
            functional_notes TEXT,
            
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')
    
    # Biomicroscopy and Anterior Segment table
    c.execute('''
        CREATE TABLE IF NOT EXISTS anterior_segment_exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            exam_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Biomicroscopy
            biomicroscopy_notes TEXT,
            biomicroscopy_device_used BOOLEAN DEFAULT 0,
            biomicroscopy_upload_path TEXT,
            
            -- Anterior Chamber Analysis
            ac_depth_od TEXT,
            ac_depth_os TEXT,
            ac_volume_od TEXT,
            ac_volume_os TEXT,
            iridocorneal_angle_od TEXT,
            iridocorneal_angle_os TEXT,
            anterior_chamber_notes TEXT,
            
            -- Pachymetry
            pachymetry_od REAL,
            pachymetry_os REAL,
            
            -- Tonometry
            tonometry_type TEXT,
            tonometry_time TEXT,
            compensation_type TEXT,
            tonometry_od TEXT,
            tonometry_os TEXT,
            tonometry_notes TEXT,
            
            -- Aberometry
            aberometry_upload_path TEXT,
            aberometry_notes TEXT,
            
            -- Corneal Topography
            topography_upload_path TEXT,
            topography_notes TEXT,
            
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')
    
    # Fundus and Advanced Tests table
    c.execute('''
        CREATE TABLE IF NOT EXISTS fundus_exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            exam_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Fundus Examination
            fundus_type TEXT,
            fundus_upload_path TEXT,
            fundus_device_used BOOLEAN DEFAULT 0,
            fundus_notes TEXT,
            
            -- Pupillography
            pupillography_result TEXT,
            pupillography_notes TEXT,
            pupillography_device_used BOOLEAN DEFAULT 0,
            
            -- OCT
            oct_upload_path TEXT,
            oct_notes TEXT,
            
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')
    
    # Patient Groups table
    c.execute('''
        CREATE TABLE IF NOT EXISTS patient_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT,
            description TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Patient Group Assignments
    c.execute('''
        CREATE TABLE IF NOT EXISTS patient_group_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            group_id INTEGER,
            assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id),
            FOREIGN KEY (group_id) REFERENCES patient_groups (id)
        )
    ''')
    
    # Contact Lenses table - COMPREHENSIVE
    c.execute('''
        CREATE TABLE IF NOT EXISTS contact_lens_prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            prescription_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Lens Type
            lens_type TEXT,
            
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
            soft_replacement TEXT,
            
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
            special_type TEXT,
            special_parameters TEXT,
            
            -- General
            wearing_schedule TEXT,
            care_solution TEXT,
            follow_up_date DATE,
            notes TEXT,
            
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')
    
    # Examination Reports table
    c.execute('''
        CREATE TABLE IF NOT EXISTS examination_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            report_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            report_content TEXT,
            physician_name TEXT,
            physician_signature TEXT,
            notes TEXT,
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
    
    # Insert default admin user if not exists
    admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
              ("admin", admin_hash, "admin"))
    
    # Insert default patient groups
    default_groups = [
        ("Corneal Ectasias", "Keratoconus, Pellucid Marginal Degeneration"),
        ("Glaucoma", "Primary open-angle glaucoma, Angle-closure glaucoma"),
        ("Cataracts", "Various types of cataracts"),
        ("Posterior Segment Diseases", "Retinal diseases, Macular degeneration"),
        ("Contact Lens Patients", "Patients using contact lenses"),
        ("Pediatric Ophthalmology", "Children eye conditions"),
        ("Dry Eye Syndrome", "Various dry eye conditions")
    ]
    
    for group_name, description in default_groups:
        c.execute("INSERT OR IGNORE INTO patient_groups (group_name, description) VALUES (?, ?)", 
                 (group_name, description))
    
    # Insert default working hours
    default_hours = [
        (0, '08:00', '16:00', 1),
        (1, '08:00', '16:00', 1),
        (2, '08:00', '16:00', 1),
        (3, '08:00', '16:00', 1),
        (4, '08:00', '16:00', 1),
        (5, '08:00', '12:00', 1),
        (6, '00:00', '00:00', 0)
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

def get_todays_appointments():
    conn = init_db()
    today = datetime.now().date()
    appointments = pd.read_sql('''
        SELECT a.*, p.first_name, p.last_name, p.patient_id 
        FROM appointments a 
        JOIN patients p ON a.patient_id = p.id 
        WHERE DATE(a.appointment_date) = ? 
        ORDER BY a.appointment_date
    ''', conn, params=(today,))
    return appointments

def get_patient_stats():
    conn = init_db()
    today = datetime.now().date()
    
    # Total patients
    total_patients = pd.read_sql("SELECT COUNT(*) as count FROM patients", conn).iloc[0]['count']
    
    # Today's examinations
    today_exams = pd.read_sql('''
        SELECT COUNT(*) as count FROM appointments 
        WHERE DATE(appointment_date) = ? AND status = 'Completed'
    ''', conn, params=(today,)).iloc[0]['count']
    
    # Total contact lenses
    total_cl = pd.read_sql("SELECT COUNT(*) as count FROM contact_lens_prescriptions", conn).iloc[0]['count']
    
    return total_patients, today_exams, total_cl

# Custom CSS for styling
def load_css():
    st.markdown("""
    <style>
    .main-header {
        background-color: #ffffff;
        padding: 1rem;
        margin-bottom: 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .appointment-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
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
    .device-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 0.2rem;
    }
    .exam-step {
        background-color: #e3f2fd;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        margin: 0.2rem;
        display: inline-block;
        font-size: 0.9rem;
    }
    .exam-step.active {
        background-color: #1f77b4;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# DASHBOARD - Updated according to requirements
def show_dashboard():
    st.markdown("<h1 style='text-align: center;'>OphtalCAM Dashboard</h1>", unsafe_allow_html=True)
    
    # Date filter
    col_filter = st.columns([2, 1, 1, 1])
    with col_filter[0]:
        view_option = st.selectbox("View", ["Today", "This Week", "This Month"], key="view_filter")
    with col_filter[1]:
        st.write("")  # Spacer
    with col_filter[2]:
        st.write("")  # Spacer
    with col_filter[3]:
        if st.button("+ New Appointment"):
            st.session_state.menu = "Appointments"
            st.rerun()
    
    # Statistics cards
    total_patients, today_exams, total_cl = get_patient_stats()
    
    col_metrics = st.columns(3)
    with col_metrics[0]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_patients}</div>
            <div class="metric-label">Total Patients</div>
        </div>
        """, unsafe_allow_html=True)
    with col_metrics[1]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{today_exams}</div>
            <div class="metric-label">Today's Examinations</div>
        </div>
        """, unsafe_allow_html=True)
    with col_metrics[2]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_cl}</div>
            <div class="metric-label">Contact Lenses</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Main content area
    col_main = st.columns([2, 1])
    
    with col_main[0]:
        st.subheader("Today's Schedule")
        appointments = get_todays_appointments()
        
        if not appointments.empty:
            for _, apt in appointments.iterrows():
                apt_time = pd.to_datetime(apt['appointment_date']).strftime('%H:%M')
                with st.container():
                    st.markdown(f"""
                    <div class="appointment-card">
                        <strong>{apt_time}</strong> - {apt['first_name']} {apt['last_name']} ({apt['patient_id']})<br>
                        <small>Type: {apt['type']} | Status: {apt['status']}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col_btn = st.columns(3)
                    with col_btn[0]:
                        if st.button("Start Exam", key=f"start_{apt['id']}"):
                            st.session_state.selected_patient = get_patient_id_by_patient_id(apt['patient_id'])
                            st.session_state.menu = "Examination Protocol"
                            st.session_state.exam_step = "medical_history"
                            st.rerun()
                    with col_btn[1]:
                        if st.button("Reschedule", key=f"resched_{apt['id']}"):
                            st.session_state.selected_appointment = apt['id']
                            st.session_state.menu = "Appointments"
                            st.rerun()
                    with col_btn[2]:
                        if st.button("Details", key=f"details_{apt['id']}"):
                            st.session_state.selected_patient = get_patient_id_by_patient_id(apt['patient_id'])
                            st.session_state.menu = "Patient Details"
                            st.rerun()
        else:
            st.info("No appointments scheduled for today.")
    
    with col_main[1]:
        st.subheader("Calendar")
        
        # Mini calendar
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
                        cols[i].markdown(f"**<span style='color: red;'>{day_str}</span>**", unsafe_allow_html=True)
                    else:
                        cols[i].write(day_str)
        
        st.markdown("---")
        st.subheader("Quick Actions")
        
        if st.button("New Patient Registration", use_container_width=True):
            st.session_state.menu = "Patient Registration"
            st.rerun()
        
        if st.button("Patient Search", use_container_width=True):
            st.session_state.menu = "Patient Search"
            st.rerun()
        
        if st.button("Examination Analytics", use_container_width=True):
            st.session_state.menu = "Analytics"
            st.rerun()

def get_patient_id_by_patient_id(patient_id):
    """Get database ID from patient ID"""
    conn = init_db()
    result = pd.read_sql("SELECT id FROM patients WHERE patient_id = ?", conn, params=(patient_id,))
    return result.iloc[0]['id'] if not result.empty else None

# MEDICAL HISTORY - Complete anamnesis
def medical_history():
    st.subheader("📋 Medical History & Anamnesis")
    
    if 'selected_patient' not in st.session_state:
        st.warning("Please select a patient first from the Dashboard or Patient Search.")
        return
    
    patient_id = st.session_state.selected_patient
    
    # Get patient info
    patient_info = pd.read_sql("SELECT * FROM patients WHERE id = ?", conn, params=(patient_id,)).iloc[0]
    
    st.markdown(f"### Patient: {patient_info['first_name']} {patient_info['last_name']} ({patient_info['patient_id']})")
    
    with st.form("medical_history_form"):
        st.markdown("### General Health Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            general_health = st.text_area("General Health Status", placeholder="Overall health, chronic conditions...", height=80)
            medications = st.text_area("Current Medications", placeholder="List all current medications...", height=80)
            allergies = st.text_area("Allergies", placeholder="Drug allergies, environmental allergies...", height=80)
        
        with col2:
            headaches = st.text_area("Headaches", placeholder="Frequency, type, triggers...", height=80)
            family_history = st.text_area("Family History", placeholder="Family medical history, eye diseases...", height=80)
            eye_history = st.text_area("Ocular History", placeholder="Previous eye conditions, surgeries, treatments...", height=80)
        
        st.markdown("### Previous Medical Reports")
        previous_reports = st.file_uploader("Upload Previous Reports", type=['pdf', 'jpg', 'png', 'docx'], accept_multiple_files=True)
        
        submit_history = st.form_submit_button("💾 Save Medical History & Continue to Refraction")
        
        if submit_history:
            try:
                c = conn.cursor()
                
                # Save file paths if files uploaded
                report_paths = []
                if previous_reports:
                    os.makedirs("patient_reports", exist_ok=True)
                    for report in previous_reports:
                        file_path = f"patient_reports/{patient_info['patient_id']}_{report.name}"
                        with open(file_path, "wb") as f:
                            f.write(report.getvalue())
                        report_paths.append(file_path)
                
                c.execute('''
                    INSERT INTO patient_medical_history 
                    (patient_id, general_health, medications, allergies, headaches, family_history, eye_history, previous_reports_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (patient_id, general_health, medications, allergies, headaches, family_history, eye_history, 
                      ','.join(report_paths) if report_paths else None))
                
                conn.commit()
                st.success("✅ Medical history saved successfully!")
                
                # Auto-navigate to refraction
                st.session_state.exam_step = "refraction"
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error saving medical history: {str(e)}")

# REFRACTION EXAMINATION - Complete protocol
def refraction_examination():
    st.subheader("🔍 Refraction Examination")
    
    if 'selected_patient' not in st.session_state:
        st.warning("Please complete medical history first.")
        return
    
    patient_id = st.session_state.selected_patient
    
    with st.form("refraction_form"):
        st.markdown("### 1. Habitual Correction")
        
        col_habit1, col_habit2 = st.columns(2)
        
        with col_habit1:
            habitual_type = st.selectbox("Type of Correction", 
                                       ["None", "Glasses", "Contact Lenses", "Both"])
            
            st.write("**OD (Right Eye)**")
            habitual_od_sph = st.number_input("Sphere OD", value=0.0, step=0.25, key="hab_od_sph")
            habitual_od_cyl = st.number_input("Cylinder OD", value=0.0, step=0.25, key="hab_od_cyl")
            habitual_od_axis = st.number_input("Axis OD", min_value=0, max_value=180, value=0, key="hab_od_axis")
            habitual_od_add = st.number_input("Add OD", value=0.0, step=0.25, key="hab_od_add")
            habitual_od_va = st.text_input("VA OD", placeholder="e.g., 20/20", key="hab_od_va")
        
        with col_habit2:
            st.write("**OS (Left Eye)**")
            habitual_os_sph = st.number_input("Sphere OS", value=0.0, step=0.25, key="hab_os_sph")
            habitual_os_cyl = st.number_input("Cylinder OS", value=0.0, step=0.25, key="hab_os_cyl")
            habitual_os_axis = st.number_input("Axis OS", min_value=0, max_value=180, value=0, key="hab_os_axis")
            habitual_os_add = st.number_input("Add OS", value=0.0, step=0.25, key="hab_os_add")
            habitual_os_va = st.text_input("VA OS", placeholder="e.g., 20/20", key="hab_os_va")
            habitual_bin_va = st.text_input("Binocular VA", placeholder="e.g., 20/20", key="hab_bin_va")
        
        st.markdown("### 2. Vision Without Correction")
        
        col_uncorr = st.columns(3)
        with col_uncorr[0]:
            uncorrected_od_va = st.text_input("Uncorrected VA OD", placeholder="20/20", key="uncorr_od")
        with col_uncorr[1]:
            uncorrected_os_va = st.text_input("Uncorrected VA OS", placeholder="20/20", key="uncorr_os")
        with col_uncorr[2]:
            uncorrected_bin_va = st.text_input("Uncorrected Binocular VA", placeholder="20/20", key="uncorr_bin")
        
        st.markdown("### 3. Objective Refraction (Autorefractor)")
        
        col_obj = st.columns(2)
        with col_obj[0]:
            objective_time = st.text_input("Time of Measurement", placeholder="e.g., 10:00 AM")
            st.write("**OD**")
            obj_od_sph = st.number_input("Sphere OD", value=0.0, step=0.25, key="obj_od_sph")
            obj_od_cyl = st.number_input("Cylinder OD", value=0.0, step=0.25, key="obj_od_cyl")
            obj_od_axis = st.number_input("Axis OD", min_value=0, max_value=180, value=0, key="obj_od_axis")
        
        with col_obj[1]:
            st.write("**OS**")
            obj_os_sph = st.number_input("Sphere OS", value=0.0, step=0.25, key="obj_os_sph")
            obj_os_cyl = st.number_input("Cylinder OS", value=0.0, step=0.25, key="obj_os_cyl")
            obj_os_axis = st.number_input("Axis OS", min_value=0, max_value=180, value=0, key="obj_os_axis")
        
        st.markdown("### 4. Subjective Monocular Refraction")
        
        col_subj = st.columns(2)
        with col_subj[0]:
            subjective_method = st.selectbox("Method", ["Fogging", "With Cycloplegic"])
            if subjective_method == "With Cycloplegic":
                cycloplegic_type = st.text_input("Cycloplegic Type", placeholder="e.g., Cyclopentolate")
                cycloplegic_lot = st.text_input("Lot Number")
                cycloplegic_expiry = st.date_input("Expiry Date")
                cycloplegic_drops = st.number_input("Number of Drops", min_value=1, max_value=4, value=1)
            
            st.write("**OD**")
            subj_od_sph = st.number_input("Sphere OD", value=0.0, step=0.25, key="subj_od_sph")
            subj_od_cyl = st.number_input("Cylinder OD", value=0.0, step=0.25, key="subj_od_cyl")
            subj_od_axis = st.number_input("Axis OD", min_value=0, max_value=180, value=0, key="subj_od_axis")
        
        with col_subj[1]:
            st.write("**OS**")
            subj_os_sph = st.number_input("Sphere OS", value=0.0, step=0.25, key="subj_os_sph")
            subj_os_cyl = st.number_input("Cylinder OS", value=0.0, step=0.25, key="subj_os_cyl")
            subj_os_axis = st.number_input("Axis OS", min_value=0, max_value=180, value=0, key="subj_os_axis")
        
        st.markdown("### 5. Binocular Tests & Notes")
        
        binocular_tests_notes = st.text_area("Binocular Tests Notes", placeholder="Stereo tests, fusion, phoria measurements...", height=60)
        
        st.markdown("### 6. Binocular Correction & Balance")
        
        bin_correction_va = st.text_input("Binocular Correction VA", placeholder="20/20")
        binocular_balance = st.selectbox("Binocular Balance", ["Balanced", "OD better", "OS better", "Unbalanced"])
        
        st.markdown("### 7. Prescribed Correction")
        
        col_pres = st.columns(2)
        with col_pres[0]:
            st.write("**OD**")
            pres_od_sph = st.number_input("Sphere OD", value=0.0, step=0.25, key="pres_od_sph")
            pres_od_cyl = st.number_input("Cylinder OD", value=0.0, step=0.25, key="pres_od_cyl")
            pres_od_axis = st.number_input("Axis OD", min_value=0, max_value=180, value=0, key="pres_od_axis")
            pres_od_add = st.number_input("Add OD", value=0.0, step=0.25, key="pres_od_add")
            pres_od_va = st.text_input("VA OD", placeholder="20/20", key="pres_od_va")
        
        with col_pres[1]:
            st.write("**OS**")
            pres_os_sph = st.number_input("Sphere OS", value=0.0, step=0.25, key="pres_os_sph")
            pres_os_cyl = st.number_input("Cylinder OS", value=0.0, step=0.25, key="pres_os_cyl")
            pres_os_axis = st.number_input("Axis OS", min_value=0, max_value=180, value=0, key="pres_os_axis")
            pres_os_add = st.number_input("Add OS", value=0.0, step=0.25, key="pres_os_add")
            pres_os_va = st.text_input("VA OS", placeholder="20/20", key="pres_os_va")
        
        pres_bin_va = st.text_input("Binocular VA", placeholder="20/20", key="pres_bin_va")
        prescription_notes = st.text_area("Prescription Notes", placeholder="Anisometropia compromises, special considerations...")
        
        submit_refraction = st.form_submit_button("💾 Save Refraction & Continue to Functional Tests")
        
        if submit_refraction:
            try:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO refraction_examinations 
                    (patient_id, habitual_correction_type, habitual_od_sphere, habitual_od_cylinder, habitual_od_axis,
                     habitual_os_sphere, habitual_os_cylinder, habitual_os_axis, habitual_od_add, habitual_os_add,
                     habitual_od_va, habitual_os_va, habitual_binocular_va, uncorrected_od_va, uncorrected_os_va,
                     uncorrected_binocular_va, objective_time, objective_od_sphere, objective_od_cylinder, objective_od_axis,
                     objective_os_sphere, objective_os_cylinder, objective_os_axis, subjective_method, cycloplegic_type,
                     cycloplegic_lot, cycloplegic_expiry, cycloplegic_drops, subjective_od_sphere, subjective_od_cylinder,
                     subjective_od_axis, subjective_os_sphere, subjective_os_cylinder, subjective_os_axis,
                     binocular_correction_va, binocular_balance, prescribed_od_sphere, prescribed_od_cylinder,
                     prescribed_od_axis, prescribed_os_sphere, prescribed_os_cylinder, prescribed_os_axis,
                     prescribed_od_add, prescribed_os_add, prescribed_od_va, prescribed_os_va, prescribed_binocular_va,
                     prescription_notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (patient_id, habitual_type, habitual_od_sph, habitual_od_cyl, habitual_od_axis,
                     habitual_os_sph, habitual_os_cyl, habitual_os_axis, habitual_od_add, habitual_os_add,
                     habitual_od_va, habitual_os_va, habitual_bin_va, uncorrected_od_va, uncorrected_os_va,
                     uncorrected_bin_va, objective_time, obj_od_sph, obj_od_cyl, obj_od_axis,
                     obj_os_sph, obj_os_cyl, obj_os_axis, subjective_method, cycloplegic_type,
                     cycloplegic_lot, cycloplegic_expiry, cycloplegic_drops, subj_od_sph, subj_od_cyl,
                     subj_od_axis, subj_os_sph, subj_os_cyl, subj_os_axis, bin_correction_va,
                     binocular_balance, pres_od_sph, pres_od_cyl, pres_od_axis, pres_os_sph,
                     pres_os_cyl, pres_os_axis, pres_od_add, pres_os_add, pres_od_va, pres_os_va,
                     pres_bin_va, prescription_notes))
                
                conn.commit()
                st.success("✅ Refraction examination saved successfully!")
                
                # Auto-navigate to functional tests
                st.session_state.exam_step = "functional_tests"
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error saving refraction examination: {str(e)}")

# FUNCTIONAL TESTS - Complete implementation
def functional_tests():
    st.subheader("🧪 Functional Tests")
    
    if 'selected_patient' not in st.session_state:
        st.warning("Please complete refraction examination first.")
        return
    
    patient_id = st.session_state.selected_patient
    
    with st.form("functional_tests_form"):
        st.markdown("### 1. Motility Test")
        
        col_motility = st.columns([3, 1])
        with col_motility[0]:
            motility_notes = st.text_area("Motility Findings", placeholder="Extraocular movements, restrictions, nystagmus...", height=60)
        with col_motility[1]:
            motility_device = st.checkbox("Use OphtalCAM Device")
        
        st.markdown("### 2. Hirschberg Test")
        
        col_hirschberg = st.columns([3, 1])
        with col_hirschberg[0]:
            hirschberg_result = st.text_input("Hirschberg Test Result", placeholder="Corneal light reflex position...")
        with col_hirschberg[1]:
            hirschberg_device = st.checkbox("Use OphtalCAM Device")
        
        st.markdown("### 3. Near Point of Convergence (NPC)")
        
        col_npc = st.columns(3)
        with col_npc[0]:
            npc_break = st.number_input("NPC Break (cm)", min_value=0.0, value=0.0, step=0.1)
        with col_npc[1]:
            npc_recovery = st.number_input("NPC Recovery (cm)", min_value=0.0, value=0.0, step=0.1)
        with col_npc[2]:
            npc_device = st.checkbox("Use OphtalCAM Device")
        
        st.markdown("### 4. Confrontation Visual Field")
        
        confrontation_field = st.text_area("Confrontation Field Results", placeholder="Defects, limitations...", height=60)
        
        st.markdown("### 5. Cover/Uncover Test")
        
        cover_uncover_result = st.text_input("Cover/Uncover Test Result", placeholder="Phoria, tropia measurements...")
        
        st.markdown("### 6. Pupil Test")
        
        col_pupil = st.columns([3, 1])
        with col_pupil[0]:
            pupil_test_result = st.text_area("Pupil Test Findings", placeholder="Pupil size, shape, reactivity, afferent defect...", height=60)
        with col_pupil[1]:
            pupil_device = st.checkbox("Use OphtalCAM Device")
        
        st.markdown("### 7. Accommodation Measurement")
        
        accommodation_method = st.selectbox("Accommodation Method", ["Push-up", "Minus lens", "Dynamic retinoscopy"])
        npa_result = st.text_input("Near Point of Accommodation (NPA)", placeholder="Measurement in cm or diopters...")
        
        col_accommodation = st.columns([3, 1])
        with col_accommodation[0]:
            accommodation_notes = st.text_area("Accommodation Notes", placeholder="Amplitude, facility, findings...", height=60)
        with col_accommodation[1]:
            accommodation_device = st.checkbox("Use OphtalCAM Device")
        
        st.markdown("### 8. General Notes")
        
        functional_notes = st.text_area("Additional Functional Test Notes", placeholder="Other observations, special tests...", height=80)
        
        submit_functional = st.form_submit_button("💾 Save Functional Tests & Continue to Anterior Segment")
        
        if submit_functional:
            try:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO functional_tests 
                    (patient_id, motility_notes, motility_device_used, hirschberg_result, hirschberg_device_used,
                     npc_break, npc_recovery, npc_device_used, confrontation_field, cover_uncover_result,
                     pupil_test_result, pupil_device_used, accommodation_method, npa_result, 
                     accommodation_device_used, accommodation_notes, functional_notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (patient_id, motility_notes, motility_device, hirschberg_result, hirschberg_device,
                     npc_break, npc_recovery, npc_device, confrontation_field, cover_uncover_result,
                     pupil_test_result, pupil_device, accommodation_method, npa_result,
                     accommodation_device, accommodation_notes, functional_notes))
                
                conn.commit()
                st.success("✅ Functional tests saved successfully!")
                
                # Auto-navigate to anterior segment
                st.session_state.exam_step = "anterior_segment"
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error saving functional tests: {str(e)}")

# ANTERIOR SEGMENT EXAMINATION
def anterior_segment_examination():
    st.subheader("🔬 Anterior Segment Examination")
    
    if 'selected_patient' not in st.session_state:
        st.warning("Please complete functional tests first.")
        return
    
    patient_id = st.session_state.selected_patient
    
    with st.form("anterior_segment_form"):
        st.markdown("### 1. Biomicroscopy (Slit Lamp)")
        
        col_bio = st.columns([3, 1])
        with col_bio[0]:
            biomicroscopy_notes = st.text_area("Biomicroscopy Findings", 
                                             placeholder="Eyelids, conjunctiva, cornea, anterior chamber, iris, lens...", 
                                             height=80)
        with col_bio[1]:
            biomicroscopy_device = st.checkbox("Use OphtalCAM Device")
        
        biomicroscopy_upload = st.file_uploader("Upload Biomicroscopy Images", type=['jpg', 'png', 'jpeg'], accept_multiple_files=True)
        
        st.markdown("### 2. Anterior Chamber Analysis")
        
        col_ac = st.columns(2)
        with col_ac[0]:
            st.write("**OD**")
            ac_depth_od = st.selectbox("AC Depth OD", ["Deep", "Medium", "Shallow", "Very Shallow"])
            ac_volume_od = st.text_input("AC Volume OD", placeholder="Volume measurement...")
            iridocorneal_angle_od = st.selectbox("Irido-Corneal Angle OD", ["Open", "Narrow", "Closed"])
        with col_ac[1]:
            st.write("**OS**")
            ac_depth_os = st.selectbox("AC Depth OS", ["Deep", "Medium", "Shallow", "Very Shallow"])
            ac_volume_os = st.text_input("AC Volume OS", placeholder="Volume measurement...")
            iridocorneal_angle_os = st.selectbox("Irido-Corneal Angle OS", ["Open", "Narrow", "Closed"])
        
        anterior_chamber_notes = st.text_area("Anterior Chamber Notes", height=60)
        
        st.markdown("### 3. Pachymetry")
        
        col_pachy = st.columns(2)
        with col_pachy[0]:
            pachymetry_od = st.number_input("Pachymetry OD (μm)", min_value=0, value=0)
        with col_pachy[1]:
            pachymetry_os = st.number_input("Pachymetry OS (μm)", min_value=0, value=0)
        
        st.markdown("### 4. Tonometry")
        
        tonometry_type = st.selectbox("Tonometry Type", ["Applanation", "Non-contact", "Goldmann", "iCare"])
        tonometry_time = st.text_input("Time of Measurement", placeholder="e.g., 14:30")
        compensation_type = st.text_input("Compensation Type", placeholder="e.g., CCT compensation...")
        
        col_tono = st.columns(2)
        with col_tono[0]:
            tonometry_od = st.text_input("Tonometry OD (mmHg)", placeholder="e.g., 16")
        with col_tono[1]:
            tonometry_os = st.text_input("Tonometry OS (mmHg)", placeholder="e.g., 17")
        
        tonometry_notes = st.text_area("Tonometry Notes", height=60)
        
        st.markdown("### 5. Aberometry")
        
        aberometry_upload = st.file_uploader("Upload Aberometry Reports", type=['pdf', 'jpg', 'png'], accept_multiple_files=True)
        aberometry_notes = st.text_area("Aberometry Notes", height=60)
        
        st.markdown("### 6. Corneal Topography")
        
        topography_upload = st.file_uploader("Upload Topography Maps", type=['pdf', 'jpg', 'png'], accept_multiple_files=True)
        topography_notes = st.text_area("Topography Notes", height=60)
        
        submit_anterior = st.form_submit_button("💾 Save Anterior Segment & Continue to Fundus")
        
        if submit_anterior:
            try:
                c = conn.cursor()
                
                # Save uploaded files
                bio_paths = []
                if biomicroscopy_upload:
                    for file in biomicroscopy_upload:
                        path = f"uploads/{patient_id}_bio_{file.name}"
                        bio_paths.append(path)
                
                aber_paths = []
                if aberometry_upload:
                    for file in aberometry_upload:
                        path = f"uploads/{patient_id}_aber_{file.name}"
                        aber_paths.append(path)
                
                topo_paths = []
                if topography_upload:
                    for file in topography_upload:
                        path = f"uploads/{patient_id}_topo_{file.name}"
                        topo_paths.append(path)
                
                c.execute('''
                    INSERT INTO anterior_segment_exams 
                    (patient_id, biomicroscopy_notes, biomicroscopy_device_used, biomicroscopy_upload_path,
                     ac_depth_od, ac_depth_os, ac_volume_od, ac_volume_os, iridocorneal_angle_od, iridocorneal_angle_os,
                     anterior_chamber_notes, pachymetry_od, pachymetry_os, tonometry_type, tonometry_time,
                     compensation_type, tonometry_od, tonometry_os, tonometry_notes, aberometry_upload_path,
                     aberometry_notes, topography_upload_path, topography_notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (patient_id, biomicroscopy_notes, biomicroscopy_device, ','.join(bio_paths),
                     ac_depth_od, ac_depth_os, ac_volume_od, ac_volume_os, iridocorneal_angle_od, iridocorneal_angle_os,
                     anterior_chamber_notes, pachymetry_od, pachymetry_os, tonometry_type, tonometry_time,
                     compensation_type, tonometry_od, tonometry_os, tonometry_notes, ','.join(aber_paths),
                     aberometry_notes, ','.join(topo_paths), topography_notes))
                
                conn.commit()
                st.success("✅ Anterior segment examination saved successfully!")
                
                # Auto-navigate to fundus
                st.session_state.exam_step = "fundus"
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error saving anterior segment examination: {str(e)}")

# FUNDUS EXAMINATION
def fundus_examination():
    st.subheader("👁️ Fundus & Advanced Tests")
    
    if 'selected_patient' not in st.session_state:
        st.warning("Please complete anterior segment examination first.")
        return
    
    patient_id = st.session_state.selected_patient
    
    with st.form("fundus_form"):
        st.markdown("### 1. Fundus Examination")
        
        fundus_type = st.selectbox("Examination Type", ["Direct Ophthalmoscopy", "Indirect Ophthalmoscopy", "Slit Lamp Biomicroscopy", "Fundus Photography"])
        
        col_fundus = st.columns([3, 1])
        with col_fundus[0]:
            fundus_notes = st.text_area("Fundus Findings", 
                                      placeholder="Optic disc, macula, vessels, periphery, abnormalities...", 
                                      height=80)
        with col_fundus[1]:
            fundus_device = st.checkbox("Use OphtalCAM Device")
        
        fundus_upload = st.file_uploader("Upload Fundus Images", type=['jpg', 'png', 'jpeg', 'pdf'], accept_multiple_files=True)
        
        st.markdown("### 2. Pupillography")
        
        pupillography_result = st.text_area("Pupillography Findings", placeholder="Pupil dynamics, latency, constriction velocity...", height=60)
        pupillography_device = st.checkbox("Use OphtalCAM Device for Pupillography")
        pupillography_notes = st.text_area("Pupillography Notes", height=60)
        
        st.markdown("### 3. OCT (Optical Coherence Tomography)")
        
        oct_upload = st.file_uploader("Upload OCT Scans", type=['pdf', 'jpg', 'png'], accept_multiple_files=True)
        oct_notes = st.text_area("OCT Findings", placeholder="RNFL, macular thickness, retinal structure...", height=80)
        
        submit_fundus = st.form_submit_button("💾 Save Fundus Examination & Continue to Patient Groups")
        
        if submit_fundus:
            try:
                c = conn.cursor()
                
                # Save uploaded files
                fundus_paths = []
                if fundus_upload:
                    for file in fundus_upload:
                        path = f"uploads/{patient_id}_fundus_{file.name}"
                        fundus_paths.append(path)
                
                oct_paths = []
                if oct_upload:
                    for file in oct_upload:
                        path = f"uploads/{patient_id}_oct_{file.name}"
                        oct_paths.append(path)
                
                c.execute('''
                    INSERT INTO fundus_exams 
                    (patient_id, fundus_type, fundus_upload_path, fundus_device_used, fundus_notes,
                     pupillography_result, pupillography_notes, pupillography_device_used, oct_upload_path, oct_notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (patient_id, fundus_type, ','.join(fundus_paths), fundus_device, fundus_notes,
                     pupillography_result, pupillography_notes, pupillography_device, ','.join(oct_paths), oct_notes))
                
                conn.commit()
                st.success("✅ Fundus examination saved successfully!")
                
                # Auto-navigate to patient groups
                st.session_state.exam_step = "patient_groups"
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error saving fundus examination: {str(e)}")

# PATIENT GROUPS
def patient_groups():
    st.subheader("📊 Assign Patient Groups")
    
    if 'selected_patient' not in st.session_state:
        st.warning("Please complete fundus examination first.")
        return
    
    patient_id = st.session_state.selected_patient
    
    # Get available groups
    groups = pd.read_sql("SELECT * FROM patient_groups", conn)
    
    with st.form("patient_groups_form"):
        st.markdown("### Select Patient Groups")
        
        selected_groups = []
        for _, group in groups.iterrows():
            if st.checkbox(f"{group['group_name']} - {group['description']}", key=f"group_{group['id']}"):
                selected_groups.append(group['id'])
        
        group_notes = st.text_area("Group Assignment Notes", placeholder="Reason for group assignment, specific findings...", height=80)
        
        submit_groups = st.form_submit_button("💾 Save Groups & Generate Report")
        
        if submit_groups:
            try:
                c = conn.cursor()
                
                # Save group assignments
                for group_id in selected_groups:
                    c.execute('''
                        INSERT INTO patient_group_assignments (patient_id, group_id, notes)
                        VALUES (?, ?, ?)
                    ''', (patient_id, group_id, group_notes))
                
                conn.commit()
                st.success("✅ Patient groups assigned successfully!")
                
                # Auto-navigate to report
                st.session_state.exam_step = "generate_report"
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error saving patient groups: {str(e)}")

# CONTACT LENSES - COMPREHENSIVE MODULE
def contact_lenses():
    st.subheader("👓 Contact Lens Prescriptions")
    
    if 'selected_patient' not in st.session_state:
        st.warning("Please select a patient first.")
        return
    
    patient_id = st.session_state.selected_patient
    patient_info = pd.read_sql("SELECT * FROM patients WHERE id = ?", conn, params=(patient_id,)).iloc[0]
    
    st.markdown(f"### Patient: {patient_info['first_name']} {patient_info['last_name']} ({patient_info['patient_id']})")
    
    with st.form("contact_lens_form"):
        st.markdown("### 1. Lens Type Selection")
        
        lens_type = st.selectbox("Contact Lens Type", 
                               ["Soft Lenses", "RGP Lenses", "Scleral Lenses", "Special Lenses", "Hybrid Lenses"])
        
        if lens_type == "Soft Lenses":
            st.markdown("### Soft Lens Parameters")
            
            col_soft1, col_soft2 = st.columns(2)
            
            with col_soft1:
                soft_brand = st.text_input("Brand/Model")
                soft_base_curve = st.number_input("Base Curve (mm)", min_value=0.0, value=8.6, step=0.1)
                soft_diameter = st.number_input("Diameter (mm)", min_value=0.0, value=14.2, step=0.1)
                soft_power_od = st.number_input("Power OD", value=0.0, step=0.25)
                soft_axis_od = st.number_input("Axis OD", min_value=0, max_value=180, value=0)
                soft_add_od = st.number_input("Add OD", value=0.0, step=0.25)
            
            with col_soft2:
                soft_color = st.text_input("Color/Tint")
                soft_replacement = st.selectbox("Replacement Schedule", ["Daily", "2-week", "Monthly", "Quarterly", "Yearly"])
                soft_power_os = st.number_input("Power OS", value=0.0, step=0.25)
                soft_axis_os = st.number_input("Axis OS", min_value=0, max_value=180, value=0)
                soft_add_os = st.number_input("Add OS", value=0.0, step=0.25)
        
        elif lens_type == "RGP Lenses":
            st.markdown("### RGP Lens Parameters")
            
            col_rgp1, col_rgp2 = st.columns(2)
            
            with col_rgp1:
                rgp_design = st.text_input("Lens Design")
                rgp_material = st.text_input("Material")
                rgp_base_curve = st.number_input("Base Curve (mm)", min_value=0.0, value=7.8, step=0.1)
                rgp_secondary_curve = st.number_input("Secondary Curve (mm)", min_value=0.0, value=8.2, step=0.1)
                rgp_diameter = st.number_input("Diameter (mm)", min_value=0.0, value=9.2, step=0.1)
                rgp_power_od = st.number_input("Power OD", value=0.0, step=0.25)
                rgp_axis_od = st.number_input("Axis OD", min_value=0, max_value=180, value=0)
            
            with col_rgp2:
                rgp_add_od = st.number_input("Add OD", value=0.0, step=0.25)
                rgp_edge_lift = st.number_input("Edge Lift (mm)", min_value=0.0, value=0.08, step=0.01)
                rgp_optical_zone = st.number_input("Optical Zone (mm)", min_value=0.0, value=7.5, step=0.1)
                rgp_color = st.text_input("Color")
                rgp_stabilization = st.text_input("Stabilization")
                rgp_power_os = st.number_input("Power OS", value=0.0, step=0.25)
                rgp_axis_os = st.number_input("Axis OS", min_value=0, max_value=180, value=0)
                rgp_add_os = st.number_input("Add OS", value=0.0, step=0.25)
        
        elif lens_type == "Scleral Lenses":
            st.markdown("### Scleral Lens Parameters")
            
            col_scleral1, col_scleral2 = st.columns(2)
            
            with col_scleral1:
                scleral_design = st.text_input("Lens Design")
                scleral_material = st.text_input("Material")
                scleral_diameter = st.number_input("Diameter (mm)", min_value=0.0, value=16.0, step=0.1)
                scleral_clearance = st.number_input("Clearance (μm)", min_value=0, value=200)
                scleral_power_od = st.number_input("Power OD", value=0.0, step=0.25)
                scleral_axis_od = st.number_input("Axis OD", min_value=0, max_value=180, value=0)
            
            with col_scleral2:
                scleral_add_od = st.number_input("Add OD", value=0.0, step=0.25)
                scleral_power_os = st.number_input("Power OS", value=0.0, step=0.25)
                scleral_axis_os = st.number_input("Axis OS", min_value=0, max_value=180, value=0)
                scleral_add_os = st.number_input("Add OS", value=0.0, step=0.25)
        
        else:  # Special Lenses
            st.markdown("### Special Lens Parameters")
            special_type = st.text_input("Lens Type", placeholder="e.g., Prosthetic, Therapeutic, Custom...")
            special_parameters = st.text_area("Special Parameters", placeholder="Custom parameters, special requirements...", height=80)
        
        st.markdown("### General Information")
        
        wearing_schedule = st.text_input("Wearing Schedule", placeholder="e.g., Daily wear, Extended wear...")
        care_solution = st.text_input("Care Solution", placeholder="Recommended cleaning solution...")
        follow_up_date = st.date_input("Follow-up Date")
        notes = st.text_area("Additional Notes", placeholder="Fitting notes, patient instructions...", height=80)
        
        submit_cl = st.form_submit_button("💾 Save Contact Lens Prescription")
        
        if submit_cl:
            try:
                c = conn.cursor()
                
                # Prepare parameters based on lens type
                if lens_type == "Soft Lenses":
                    c.execute('''
                        INSERT INTO contact_lens_prescriptions 
                        (patient_id, lens_type, soft_brand, soft_base_curve, soft_diameter,
                         soft_power_od, soft_power_os, soft_axis_od, soft_axis_os, soft_add_od, soft_add_os,
                         soft_color, soft_replacement, wearing_schedule, care_solution, follow_up_date, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (patient_id, lens_type, soft_brand, soft_base_curve, soft_diameter,
                         soft_power_od, soft_power_os, soft_axis_od, soft_axis_os, soft_add_od, soft_add_os,
                         soft_color, soft_replacement, wearing_schedule, care_solution, follow_up_date, notes))
                
                elif lens_type == "RGP Lenses":
                    c.execute('''
                        INSERT INTO contact_lens_prescriptions 
                        (patient_id, lens_type, rgp_design, rgp_material, rgp_base_curve, rgp_secondary_curve,
                         rgp_diameter, rgp_power_od, rgp_power_os, rgp_axis_od, rgp_axis_os, rgp_add_od, rgp_add_os,
                         rgp_edge_lift, rgp_optical_zone, rgp_color, rgp_stabilization, wearing_schedule, care_solution, follow_up_date, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (patient_id, lens_type, rgp_design, rgp_material, rgp_base_curve, rgp_secondary_curve,
                         rgp_diameter, rgp_power_od, rgp_power_os, rgp_axis_od, rgp_axis_os, rgp_add_od, rgp_add_os,
                         rgp_edge_lift, rgp_optical_zone, rgp_color, rgp_stabilization, wearing_schedule, care_solution, follow_up_date, notes))
                
                elif lens_type == "Scleral Lenses":
                    c.execute('''
                        INSERT INTO contact_lens_prescriptions 
                        (patient_id, lens_type, scleral_design, scleral_material, scleral_diameter, scleral_clearance,
                         scleral_power_od, scleral_power_os, scleral_axis_od, scleral_axis_os, scleral_add_od, scleral_add_os,
                         wearing_schedule, care_solution, follow_up_date, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (patient_id, lens_type, scleral_design, scleral_material, scleral_diameter, scleral_clearance,
                         scleral_power_od, scleral_power_os, scleral_axis_od, scleral_axis_os, scleral_add_od, scleral_add_os,
                         wearing_schedule, care_solution, follow_up_date, notes))
                
                else:  # Special Lenses
                    c.execute('''
                        INSERT INTO contact_lens_prescriptions 
                        (patient_id, lens_type, special_type, special_parameters, wearing_schedule, care_solution, follow_up_date, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (patient_id, lens_type, special_type, special_parameters, wearing_schedule, care_solution, follow_up_date, notes))
                
                conn.commit()
                st.success("✅ Contact lens prescription saved successfully!")
                
            except Exception as e:
                st.error(f"❌ Error saving contact lens prescription: {str(e)}")

# GENERATE REPORT
def generate_report():
    st.subheader("📄 Generate Examination Report")
    
    if 'selected_patient' not in st.session_state:
        st.warning("Please complete the examination first.")
        return
    
    patient_id = st.session_state.selected_patient
    patient_info = pd.read_sql("SELECT * FROM patients WHERE id = ?", conn, params=(patient_id,)).iloc[0]
    
    st.markdown(f"### Final Report for: {patient_info['first_name']} {patient_info['last_name']}")
    
    with st.form("report_form"):
        physician_name = st.text_input("Physician Name", placeholder="Dr. Full Name")
        physician_signature = st.text_input("Physician Signature", placeholder="Signature")
        report_notes = st.text_area("Report Notes", placeholder="Summary, recommendations, follow-up instructions...", height=100)
        
        col_report = st.columns(2)
        with col_report[0]:
            generate_short = st.form_submit_button("📋 Generate Short Report")
        with col_report[1]:
            generate_detailed = st.form_submit_button("📊 Generate Detailed Report")
        
        if generate_short or generate_detailed:
            try:
                # Generate report content
                report_content = f"""
                OPHTALCAM EMR - EXAMINATION REPORT
                Patient: {patient_info['first_name']} {patient_info['last_name']}
                Patient ID: {patient_info['patient_id']}
                Date of Birth: {patient_info['date_of_birth']}
                Examination Date: {datetime.now().strftime('%Y-%m-%d')}
                
                PHYSICIAN: {physician_name}
                SIGNATURE: {physician_signature}
                
                SUMMARY:
                {report_notes}
                
                --- SHORT REPORT ---
                This report contains the essential findings and recommendations.
                Full examination protocol is available in the patient's electronic record.
                """
                
                c = conn.cursor()
                c.execute('''
                    INSERT INTO examination_reports (patient_id, report_content, physician_name, physician_signature, notes)
                    VALUES (?, ?, ?, ?, ?)
                ''', (patient_id, report_content, physician_name, physician_signature, report_notes))
                
                conn.commit()
                
                st.success("✅ Examination report generated successfully!")
                
                # Offer download
                st.download_button(
                    label="📥 Download Short Report",
                    data=report_content,
                    file_name=f"report_{patient_info['patient_id']}_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain"
                )
                
                if st.button("🏁 Complete Examination"):
                    st.session_state.exam_step = None
                    st.session_state.selected_patient = None
                    st.session_state.menu = "Dashboard"
                    st.success("Examination completed successfully!")
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Error generating report: {str(e)}")

# [OSTALE FUNKCIJE - patient_registration, patient_search, show_analytics, show_calendar, manage_working_hours]

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
                        if st.button("Start Examination", key=f"exam_{patient['id']}"):
                            st.session_state.selected_patient = patient['id']
                            st.session_state.menu = "Examination Protocol"
                            st.session_state.exam_step = "medical_history"
                            st.rerun()
                    with col_btn2:
                        if st.button("Contact Lenses", key=f"cl_{patient['id']}"):
                            st.session_state.selected_patient = patient['id']
                            st.session_state.menu = "Contact Lenses"
                            st.rerun()
                    with col_btn3:
                        if st.button("View History", key=f"history_{patient['id']}"):
                            st.session_state.selected_patient = patient['id']
                            st.session_state.menu = "Patient History"
                            st.rerun()
        else:
            st.info("No patients found matching your search criteria.")

def show_analytics():
    st.subheader("📊 Examination Analytics")
    
    # Placeholder for analytics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Patients", "150")
    with col2:
        st.metric("Exams This Month", "45")
    with col3:
        st.metric("Contact Lens Patients", "38")
    with col4:
        st.metric("Follow-up Rate", "92%")
    
    # Sample charts
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.write("**Patient Groups Distribution**")
        groups_data = pd.DataFrame({
            'Group': ['Corneal Ectasias', 'Glaucoma', 'Cataracts', 'Contact Lenses', 'Other'],
            'Count': [25, 18, 32, 38, 37]
        })
        fig = px.pie(groups_data, values='Count', names='Group')
        st.plotly_chart(fig, use_container_width=True)
    
    with col_chart2:
        st.write("**Monthly Examinations**")
        monthly_data = pd.DataFrame({
            'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            'Examinations': [35, 42, 38, 45, 50, 48]
        })
        fig = px.bar(monthly_data, x='Month', y='Examinations')
        st.plotly_chart(fig, use_container_width=True)

# MAIN NAVIGATION
def main_navigation():
    st.sidebar.title("👁️ OphtalCAM EMR")
    
    if 'menu' not in st.session_state:
        st.session_state.menu = "Dashboard"
    if 'exam_step' not in st.session_state:
        st.session_state.exam_step = None
    
    # Main menu
    menu_options = [
        "Dashboard",
        "Patient Registration",
        "Patient Search", 
        "Examination Protocol",
        "Contact Lenses",
        "Analytics",
        "Settings"
    ]
    
    menu = st.sidebar.selectbox("Navigation", menu_options, 
                              index=menu_options.index(st.session_state.menu))
    
    st.session_state.menu = menu
    
    # Examination workflow steps
    if st.session_state.exam_step:
        st.sidebar.markdown("---")
        st.sidebar.subheader("Examination Steps")
        
        steps = [
            ("medical_history", "1. Medical History"),
            ("refraction", "2. Refraction"), 
            ("functional_tests", "3. Functional Tests"),
            ("anterior_segment", "4. Anterior Segment"),
            ("fundus", "5. Fundus & Advanced"),
            ("patient_groups", "6. Patient Groups"),
            ("generate_report", "7. Final Report")
        ]
        
        for step, label in steps:
            if step == st.session_state.exam_step:
                st.sidebar.markdown(f"**{label}** ✅")
            else:
                st.sidebar.text(label)
    
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
        elif st.session_state.exam_step == "fundus":
            fundus_examination()
        elif st.session_state.exam_step == "patient_groups":
            patient_groups()
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
            st.info("Please select a patient from Dashboard or Patient Search to start examination.")
        elif menu == "Contact Lenses":
            contact_lenses()
        elif menu == "Analytics":
            show_analytics()
        elif menu == "Settings":
            st.info("Settings - Implementation in progress")

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
        # Header
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.image("https://i.postimg.cc/PrRFzQLv/Logo-Transparency-01.png", width=300)
        
        with col3:
            st.write(f"**User:** {st.session_state.username}")
            if st.button("Logout"):
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
