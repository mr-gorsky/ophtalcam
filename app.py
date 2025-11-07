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
            ac_depth TEXT,
            ac_volume TEXT,
            iridocorneal_angle TEXT,
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
            patient_id INTEGER,
            group_name TEXT,
            assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')
    
    # Contact Lenses table
    c.execute('''
        CREATE TABLE IF NOT EXISTS contact_lens_prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            prescription_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            lens_type TEXT,
            parameters TEXT,
            follow_up_date DATE,
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
                            st.session_state.selected_patient = apt['patient_id']
                            st.session_state.menu = "Medical History"
                            st.rerun()
                    with col_btn[1]:
                        if st.button("Reschedule", key=f"resched_{apt['id']}"):
                            st.session_state.selected_appointment = apt['id']
                            st.session_state.menu = "Appointments"
                            st.rerun()
                    with col_btn[2]:
                        if st.button("Details", key=f"details_{apt['id']}"):
                            st.session_state.selected_patient = apt['patient_id']
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

# MEDICAL HISTORY - Complete anamnesis
def medical_history():
    st.subheader("📋 Medical History & Anamnesis")
    
    if 'selected_patient' not in st.session_state:
        st.warning("Please select a patient first from the Dashboard or Patient Search.")
        return
    
    patient_id = st.session_state.selected_patient
    
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
        
        submit_history = st.form_submit_button("💾 Save Medical History")
        
        if submit_history:
            try:
                c = conn.cursor()
                
                # Save file paths if files uploaded
                report_paths = []
                if previous_reports:
                    os.makedirs("patient_reports", exist_ok=True)
                    for report in previous_reports:
                        file_path = f"patient_reports/{patient_id}_{report.name}"
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
        
        st.markdown("### 5. Binocular Correction & Balance")
        
        bin_correction_va = st.text_input("Binocular Correction VA", placeholder="20/20")
        binocular_balance = st.selectbox("Binocular Balance", ["Balanced", "OD better", "OS better", "Unbalanced"])
        
        st.markdown("### 6. Prescribed Correction")
        
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

# [OSTALE FUNKCIJE - functional_tests(), anterior_segment_examination(), fundus_examination(), patient_groups(), generate_report() itd.]

# Placeholder functions for other modules
def functional_tests():
    st.subheader("🧪 Functional Tests")
    st.info("Functional tests module - Implementation in progress")
    
    if st.button("Continue to Anterior Segment Examination"):
        st.session_state.exam_step = "anterior_segment"
        st.rerun()

def anterior_segment_examination():
    st.subheader("🔬 Anterior Segment Examination")
    st.info("Anterior segment examination module - Implementation in progress")
    
    if st.button("Continue to Fundus Examination"):
        st.session_state.exam_step = "fundus"
        st.rerun()

def fundus_examination():
    st.subheader("👁️ Fundus & Advanced Tests")
    st.info("Fundus examination module - Implementation in progress")
    
    if st.button("Continue to Patient Groups"):
        st.session_state.exam_step = "groups"
        st.rerun()

def patient_groups():
    st.subheader("📊 Assign Patient Groups")
    st.info("Patient groups module - Implementation in progress")
    
    if st.button("Generate Final Report"):
        st.session_state.exam_step = "report"
        st.rerun()

def generate_report():
    st.subheader("📄 Examination Report")
    st.info("Report generation module - Implementation in progress")
    
    if st.button("Complete Examination"):
        st.session_state.exam_step = None
        st.session_state.menu = "Dashboard"
        st.success("Examination completed successfully!")
        st.rerun()

# MAIN NAVIGATION
def main_navigation():
    st.sidebar.title("👁️ OphtalCAM EMR")
    
    if 'menu' not in st.session_state:
        st.session_state.menu = "Dashboard"
    if 'exam_step' not in st.session_state:
        st.session_state.exam_step = None
    
    # Main menu
    menu = st.sidebar.selectbox("Navigation", [
        "Dashboard",
        "Patient Registration",
        "Patient Search", 
        "Appointments",
        "Contact Lenses",
        "Analytics",
        "Settings"
    ], index=["Dashboard", "Patient Registration", "Patient Search", "Appointments", 
              "Contact Lenses", "Analytics", "Settings"].index(st.session_state.menu))
    
    st.session_state.menu = menu
    
    # Examination workflow
    if st.session_state.exam_step:
        st.sidebar.markdown("---")
        st.sidebar.subheader("Examination Steps")
        
        steps = {
            "medical_history": "1. Medical History",
            "refraction": "2. Refraction", 
            "functional_tests": "3. Functional Tests",
            "anterior_segment": "4. Anterior Segment",
            "fundus": "5. Fundus & Advanced",
            "groups": "6. Patient Groups",
            "report": "7. Final Report"
        }
        
        for step, label in steps.items():
            if step == st.session_state.exam_step:
                st.sidebar.markdown(f"**{label}**")
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
        elif st.session_state.exam_step == "groups":
            patient_groups()
        elif st.session_state.exam_step == "report":
            generate_report()
    else:
        if menu == "Dashboard":
            show_dashboard()
        elif menu == "Patient Registration":
            st.info("Patient Registration - Implementation in progress")
        elif menu == "Patient Search":
            st.info("Patient Search - Implementation in progress")
        elif menu == "Appointments":
            st.info("Appointments Management - Implementation in progress")
        elif menu == "Contact Lenses":
            st.info("Contact Lenses - Implementation in progress")
        elif menu == "Analytics":
            st.info("Analytics - Implementation in progress")
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
