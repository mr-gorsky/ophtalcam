# app.py - OphtalCAM EMR (PROFESSIONAL MEDICAL VERSION)
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta, date
import calendar
import os
import json
import hashlib
import math

st.set_page_config(page_title="OphtalCAM EMR", page_icon="👁️", layout="wide", initial_sidebar_state="collapsed")

# -----------------------
# Database init + auto-migration
# -----------------------
@st.cache_resource
def init_db():
    # AUTO-MIGRATION - Dodaj sve missing stupce
    try:
        conn_temp = sqlite3.connect('ophtalcam.db', check_same_thread=False)
        c_temp = conn_temp.cursor()
        
        # Provjeri i dodaj sve missing stupce
        tables_columns = {
            'refraction_exams': [
                'subjective_add_od', 'subjective_add_os', 'subjective_deg_od', 'subjective_deg_os',
                'habitual_add_od', 'habitual_add_os', 'habitual_deg_od', 'habitual_deg_os',
                'final_add_od', 'final_add_os', 'final_deg_od', 'final_deg_os'
            ],
            'posterior_segment_exams': [
                'ophthalmoscopy_od', 'ophthalmoscopy_os'
            ],
            'anterior_segment_exams': [
                'anterior_chamber_depth_od', 'anterior_chamber_depth_os', 
                'anterior_chamber_volume_od', 'anterior_chamber_volume_os'
            ],
            'functional_tests': [
                'rapd'
            ],
            'medical_history': [
                'chief_complaint'
            ]
        }
        
        for table, columns in tables_columns.items():
            c_temp.execute(f"PRAGMA table_info({table})")
            existing_columns = [col[1] for col in c_temp.fetchall()]
            
            for column in columns:
                if column not in existing_columns:
                    c_temp.execute(f"ALTER TABLE {table} ADD COLUMN {column} TEXT")
                    print(f"Added column {column} to {table}")
        
        conn_temp.commit()
        conn_temp.close()
        print("Database migration completed successfully")
    except Exception as e:
        print(f"Database migration: {e}")

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
            chief_complaint TEXT,
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
            subjective_deg_distance TEXT,
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
            final_deg_distance TEXT,
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
            ophthalmoscopy_od TEXT,
            ophthalmoscopy_os TEXT,
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

    # Appointment schedule settings
    c.execute('''
        CREATE TABLE IF NOT EXISTS appointment_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day_of_week INTEGER NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            appointment_duration INTEGER DEFAULT 30,
            max_appointments INTEGER DEFAULT 10,
            is_active BOOLEAN DEFAULT TRUE
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

def get_recent_patients(limit=5):
    """Get recently registered patients"""
    conn = init_db()
    try:
        patients = pd.read_sql('''
            SELECT patient_id, first_name, last_name, date_of_birth, created_date 
            FROM patients 
            ORDER BY created_date DESC 
            LIMIT ?
        ''', conn, params=(limit,))
        return patients
    except Exception:
        return pd.DataFrame()

def get_upcoming_appointments(days=7):
    """Get upcoming appointments for the next days"""
    conn = init_db()
    try:
        start_date = date.today()
        end_date = start_date + timedelta(days=days)
        appointments = pd.read_sql('''
            SELECT a.*, p.first_name, p.last_name, p.patient_id 
            FROM appointments a 
            JOIN patients p ON a.patient_id = p.id 
            WHERE DATE(a.appointment_date) BETWEEN ? AND ?
            ORDER BY a.appointment_date
        ''', conn, params=(start_date, end_date))
        return appointments
    except Exception:
        return pd.DataFrame()

def schedule_appointment():
    """Function to schedule new appointments"""
    st.markdown("<h2 class='main-header'>Schedule Appointment</h2>", unsafe_allow_html=True)
    
    with st.form("appointment_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Patient search and selection
            patients_df = pd.read_sql("SELECT patient_id, first_name, last_name FROM patients ORDER BY last_name, first_name", conn)
            if not patients_df.empty:
                patient_options = [f"{row['patient_id']} - {row['first_name']} {row['last_name']}" for _, row in patients_df.iterrows()]
                selected_patient = st.selectbox("Select Patient", patient_options)
                patient_id = selected_patient.split(" - ")[0] if selected_patient else None
            else:
                st.info("No patients found. Please register patients first.")
                patient_id = None
            
            appointment_date = st.date_input("Appointment Date", value=date.today())
            appointment_time = st.time_input("Appointment Time", value=datetime.now().time())
            
        with col2:
            appointment_type = st.selectbox("Appointment Type", 
                                          ["Routine Examination", "Contact Lens Fitting", "Post-operative Check", 
                                           "Emergency", "Consultation", "Follow-up", "Other"])
            duration = st.number_input("Duration (minutes)", min_value=15, max_value=180, value=30, step=15)
            status = st.selectbox("Status", ["Scheduled", "Confirmed", "Cancelled", "Completed"])
        
        notes = st.text_area("Appointment Notes", placeholder="Additional notes or instructions...")
        
        submit_button = st.form_submit_button("Schedule Appointment", use_container_width=True)
        
        if submit_button:
            if patient_id:
                try:
                    # Get patient database ID
                    patient_db_id = pd.read_sql("SELECT id FROM patients WHERE patient_id = ?", conn, params=(patient_id,)).iloc[0]['id']
                    
                    # Combine date and time
                    appointment_datetime = datetime.combine(appointment_date, appointment_time)
                    
                    c = conn.cursor()
                    c.execute('''
                        INSERT INTO appointments 
                        (patient_id, appointment_date, duration_minutes, appointment_type, status, notes)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (patient_db_id, appointment_datetime, duration, appointment_type, status, notes))
                    conn.commit()
                    st.success(f"Appointment scheduled successfully for {appointment_datetime.strftime('%d.%m.%Y %H:%M')}")
                except Exception as e:
                    st.error(f"Error scheduling appointment: {str(e)}")
            else:
                st.error("Please select a patient")

def view_patient_history():
    """View comprehensive patient history"""
    if 'selected_patient' not in st.session_state or not st.session_state.selected_patient:
        st.info("Please select a patient first from Patient Search")
        return
    
    pid = st.session_state.selected_patient
    
    try:
        patient_info = pd.read_sql("SELECT * FROM patients WHERE patient_id = ?", conn, params=(pid,)).iloc[0]
        st.markdown(f"<h2 class='main-header'>Patient History: {patient_info['first_name']} {patient_info['last_name']}</h2>", unsafe_allow_html=True)
        
        # Patient基本信息
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Patient Information")
            st.write(f"**Patient ID:** {patient_info['patient_id']}")
            st.write(f"**Date of Birth:** {patient_info['date_of_birth']}")
            st.write(f"**Gender:** {patient_info['gender']}")
            st.write(f"**Phone:** {patient_info['phone']}")
        with col2:
            st.write(f"**Email:** {patient_info['email']}")
            st.write(f"**ID Number:** {patient_info['id_number']}")
            st.write(f"**Emergency Contact:** {patient_info['emergency_contact']}")
            st.write(f"**Insurance:** {patient_info['insurance_info']}")
        
        # Medical History
        st.markdown("#### Medical History")
        medical_history = pd.read_sql('''
            SELECT * FROM medical_history 
            WHERE patient_id = (SELECT id FROM patients WHERE patient_id = ?)
            ORDER BY visit_date DESC
        ''', conn, params=(pid,))
        
        if not medical_history.empty:
            for _, record in medical_history.iterrows():
                with st.expander(f"Medical History - {record['visit_date'][:10]}"):
                    col_mh1, col_mh2 = st.columns(2)
                    with col_mh1:
                        st.write(f"**Chief Complaint:** {record.get('chief_complaint', '')}")
                        st.write(f"**General Health:** {record['general_health']}")
                        st.write(f"**Medications:** {record['current_medications']}")
                        st.write(f"**Allergies:** {record['allergies']}")
                    with col_mh2:
                        st.write(f"**Ocular History:** {record['ocular_history']}")
                        st.write(f"**Family History:** {record['family_history']}")
                        st.write(f"**Last Eye Exam:** {record['last_eye_exam']}")
        else:
            st.info("No medical history records found.")
        
        # Refraction History
        st.markdown("#### Refraction History")
        refraction_history = pd.read_sql('''
            SELECT * FROM refraction_exams 
            WHERE patient_id = (SELECT id FROM patients WHERE patient_id = ?)
            ORDER BY exam_date DESC
        ''', conn, params=(pid,))
        
        if not refraction_history.empty:
            for _, record in refraction_history.iterrows():
                with st.expander(f"Refraction - {record['exam_date'][:10]}"):
                    col_ref1, col_ref2 = st.columns(2)
                    with col_ref1:
                        st.write(f"**OD:** {record.get('final_prescribed_od_sphere', '')} {record.get('final_prescribed_od_cylinder', '')} x {record.get('final_prescribed_od_axis', '')}")
                        st.write(f"**ADD OD:** {record.get('final_add_od', '')}")
                    with col_ref2:
                        st.write(f"**OS:** {record.get('final_prescribed_os_sphere', '')} {record.get('final_prescribed_os_cylinder', '')} x {record.get('final_prescribed_os_axis', '')}")
                        st.write(f"**ADD OS:** {record.get('final_add_os', '')}")
        
        # Appointment History
        st.markdown("#### Appointment History")
        appointment_history = pd.read_sql('''
            SELECT a.*, p.first_name, p.last_name 
            FROM appointments a 
            JOIN patients p ON a.patient_id = p.id 
            WHERE p.patient_id = ?
            ORDER BY a.appointment_date DESC
        ''', conn, params=(pid,))
        
        if not appointment_history.empty:
            for _, apt in appointment_history.iterrows():
                apt_time = pd.to_datetime(apt['appointment_date']).strftime('%d.%m.%Y %H:%M')
                st.write(f"**{apt_time}** - {apt['appointment_type']} ({apt['status']})")
                if apt['notes']:
                    st.caption(f"Notes: {apt['notes']}")
        else:
            st.info("No appointment history found.")
            
    except Exception as e:
        st.error(f"Error loading patient history: {str(e)}")

def clinical_analytics():
    """Clinical analytics and reporting"""
    st.markdown("<h2 class='main-header'>Clinical Analytics</h2>", unsafe_allow_html=True)
    
    try:
        # Basic statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_patients = pd.read_sql("SELECT COUNT(*) as count FROM patients", conn).iloc[0]['count']
            st.metric("Total Patients", total_patients)
        
        with col2:
            total_exams = pd.read_sql("SELECT COUNT(*) as count FROM refraction_exams", conn).iloc[0]['count']
            st.metric("Total Examinations", total_exams)
        
        with col3:
            total_cl = pd.read_sql("SELECT COUNT(*) as count FROM contact_lens_prescriptions", conn).iloc[0]['count']
            st.metric("Contact Lens Fittings", total_cl)
        
        with col4:
            today_appointments = pd.read_sql('''
                SELECT COUNT(*) as count FROM appointments 
                WHERE DATE(appointment_date) = ?
            ''', conn, params=(date.today(),)).iloc[0]['count']
            st.metric("Today's Appointments", today_appointments)
        
        # Recent activity
        st.markdown("#### Recent Activity")
        col_act1, col_act2 = st.columns(2)
        
        with col_act1:
            st.markdown("**Recent Patients**")
            recent_patients = get_recent_patients(5)
            if not recent_patients.empty:
                for _, patient in recent_patients.iterrows():
                    st.write(f"{patient['first_name']} {patient['last_name']} ({patient['patient_id']})")
                    st.caption(f"Registered: {patient['created_date'][:10]}")
            else:
                st.info("No patients found")
        
        with col_act2:
            st.markdown("**Upcoming Appointments**")
            upcoming_appointments = get_upcoming_appointments(7)
            if not upcoming_appointments.empty:
                for _, apt in upcoming_appointments.iterrows():
                    apt_time = pd.to_datetime(apt['appointment_date']).strftime('%d.%m.%Y %H:%M')
                    st.write(f"**{apt_time}** - {apt['first_name']} {apt['last_name']}")
                    st.caption(f"{apt['appointment_type']} - {apt['status']}")
            else:
                st.info("No upcoming appointments")
        
        # Examination statistics
        st.markdown("#### Examination Types")
        exam_stats = pd.read_sql('''
            SELECT appointment_type, COUNT(*) as count 
            FROM appointments 
            GROUP BY appointment_type 
            ORDER BY count DESC
        ''', conn)
        
        if not exam_stats.empty:
            st.dataframe(exam_stats, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error loading analytics: {str(e)}")

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
    .appointment-card {
        background: white;
        padding: 1rem;
        border-radius: 6px;
        border-left: 4px solid #1e3c72;
        margin-bottom: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .calendar-day {
        text-align: center;
        padding: 5px;
        margin: 2px;
        border-radius: 4px;
    }
    .calendar-day.today {
        background: #1e3c72;
        color: white;
    }
    .eye-comparison {
        display: flex;
        gap: 1rem;
        margin-bottom: 1rem;
    }
    .eye-comparison > div {
        flex: 1;
    }
    .compact-input {
        margin-bottom: 0.5rem;
    }
    .tabo-scheme {
        width: 250px;
        height: 250px;
        position: relative;
        border: 2px solid #333;
        border-radius: 50%;
        margin: 10px auto;
        background: white;
    }
    .tabo-axis {
        position: absolute;
        background: #1e3c72;
        font-weight: bold;
        color: white;
        padding: 2px 5px;
        border-radius: 3px;
        font-size: 12px;
    }
    .tabo-container {
        display: flex;
        justify-content: center;
        gap: 2rem;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

def draw_tabo_scheme(axis_od, axis_os):
    """Draw professional Tabo scheme for refraction reports"""
    html = """
    <div class="tabo-container">
        <div>
            <h4 style="text-align:center; color:#d32f2f;">OD (Right Eye)</h4>
            <div class="tabo-scheme">
                <div style="position:absolute; top:50%; left:0; right:0; height:1px; background:#333;"></div>
                <div style="position:absolute; top:0; bottom:0; left:50%; width:1px; background:#333;"></div>
                <!-- Oznake za gornju polovicu (0-180°) -->
                <div style="position:absolute; top:10px; left:50%; transform:translateX(-50%); font-weight:bold; color:#d32f2f;">90°</div>
                <div style="position:absolute; top:50%; left:10px; transform:translateY(-50%); font-weight:bold; color:#d32f2f;">180°</div>
                <div style="position:absolute; top:50%; right:10px; transform:translateY(-50%); font-weight:bold; color:#d32f2f;">0°</div>
                
                <!-- Crtice za stupnjeve -->
                <div style="position:absolute; top:25%; left:50%; transform:translateX(-50%); font-size:10px; color:#666;">75°</div>
                <div style="position:absolute; top:25%; left:25%; transform:translate(-50%, -50%); font-size:10px; color:#666;">105°</div>
                <div style="position:absolute; top:25%; right:25%; transform:translate(50%, -50%); font-size:10px; color:#666;">75°</div>
                <div style="position:absolute; top:75%; left:25%; transform:translate(-50%, -50%); font-size:10px; color:#666;">165°</div>
                <div style="position:absolute; top:75%; right:25%; transform:translate(50%, -50%); font-size:10px; color:#666;">15°</div>
    """
    
    if axis_od and axis_od != "":
        try:
            angle = int(axis_od)
            rad = math.radians(angle)
            x = 125 + 90 * math.sin(rad)
            y = 125 - 90 * math.cos(rad)
            html += f"""
                <div style="position:absolute; top:{y-10}px; left:{x-10}px; width:20px; height:20px; background:#d32f2f; border-radius:50%;"></div>
                <div style="position:absolute; top:{y-25}px; left:{x-15}px; background:#d32f2f; color:white; padding:2px 5px; border-radius:3px; font-size:10px; font-weight:bold;">
                    {axis_od}°
                </div>
            """
        except ValueError:
            pass
    
    html += """
            </div>
        </div>
        <div>
            <h4 style="text-align:center; color:#1976d2;">OS (Left Eye)</h4>
            <div class="tabo-scheme">
                <div style="position:absolute; top:50%; left:0; right:0; height:1px; background:#333;"></div>
                <div style="position:absolute; top:0; bottom:0; left:50%; width:1px; background:#333;"></div>
                <!-- Oznake za gornju polovicu (0-180°) -->
                <div style="position:absolute; top:10px; left:50%; transform:translateX(-50%); font-weight:bold; color:#1976d2;">90°</div>
                <div style="position:absolute; top:50%; left:10px; transform:translateY(-50%); font-weight:bold; color:#1976d2;">180°</div>
                <div style="position:absolute; top:50%; right:10px; transform:translateY(-50%); font-weight:bold; color:#1976d2;">0°</div>
                
                <!-- Crtice za stupnjeve -->
                <div style="position:absolute; top:25%; left:50%; transform:translateX(-50%); font-size:10px; color:#666;">75°</div>
                <div style="position:absolute; top:25%; left:25%; transform:translate(-50%, -50%); font-size:10px; color:#666;">105°</div>
                <div style="position:absolute; top:25%; right:25%; transform:translate(50%, -50%); font-size:10px; color:#666;">75°</div>
                <div style="position:absolute; top:75%; left:25%; transform:translate(-50%, -50%); font-size:10px; color:#666;">165°</div>
                <div style="position:absolute; top:75%; right:25%; transform:translate(50%, -50%); font-size:10px; color:#666;">15°</div>
    """
    
    if axis_os and axis_os != "":
        try:
            angle = int(axis_os)
            rad = math.radians(angle)
            x = 125 + 90 * math.sin(rad)
            y = 125 - 90 * math.cos(rad)
            html += f"""
                <div style="position:absolute; top:{y-10}px; left:{x-10}px; width:20px; height:20px; background:#1976d2; border-radius:50%;"></div>
                <div style="position:absolute; top:{y-25}px; left:{x-15}px; background:#1976d2; color:white; padding:2px 5px; border-radius:3px; font-size:10px; font-weight:bold;">
                    {axis_os}°
                </div>
            """
        except ValueError:
            pass
    
    html += """
            </div>
        </div>
    </div>
    """
    return html

# -----------------------
# PROFESSIONAL DASHBOARD - COMPLETELY FUNCTIONAL
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
        if st.button("Clinical Analytics", use_container_width=True, key="analytics_dash"):
            st.session_state.menu = "Clinical Analytics"
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
                with st.container():
                    col_a, col_b, col_c = st.columns([3, 1, 1])
                    with col_a:
                        t = pd.to_datetime(apt['appointment_date']).strftime('%H:%M')
                        st.markdown(f"**{t}** - {apt['first_name']} {apt['last_name']} ({apt['patient_id']})")
                        st.caption(f"{apt['appointment_type']} | {apt['status']}")
                    with col_b:
                        if st.button("Begin Exam", key=f"begin_{apt['id']}", use_container_width=True):
                            st.session_state.selected_patient = apt['patient_id']
                            st.session_state.menu = "Examination Protocol"
                            st.session_state.exam_step = "medical_history"
                            st.rerun()
                    with col_c:
                        if st.button("History", key=f"history_{apt['id']}", use_container_width=True):
                            st.session_state.selected_patient = apt['patient_id']
                            st.session_state.menu = "Patient History"
                            st.rerun()
        else:
            st.info("No appointments scheduled for today.")
            
        # Recent Patients Section
        st.subheader("Recent Patients")
        recent_patients = get_recent_patients(5)
        if not recent_patients.empty:
            for _, patient in recent_patients.iterrows():
                col_pat1, col_pat2, col_pat3 = st.columns([3, 1, 1])
                with col_pat1:
                    st.write(f"**{patient['first_name']} {patient['last_name']}** ({patient['patient_id']})")
                    st.caption(f"DOB: {patient['date_of_birth']} | Registered: {patient['created_date'][:10]}")
                with col_pat2:
                    if st.button("Examine", key=f"exam_{patient['patient_id']}", use_container_width=True):
                        st.session_state.selected_patient = patient['patient_id']
                        st.session_state.menu = "Examination Protocol"
                        st.session_state.exam_step = "medical_history"
                        st.rerun()
                with col_pat3:
                    if st.button("History", key=f"phist_{patient['patient_id']}", use_container_width=True):
                        st.session_state.selected_patient = patient['patient_id']
                        st.session_state.menu = "Patient History"
                        st.rerun()
        else:
            st.info("No patients registered yet.")

    with col_main[1]:
        st.subheader("Calendar")
        today = datetime.now()
        
        # Current month calendar - FUNCTIONAL
        cal = calendar.monthcalendar(today.year, today.month)
        st.write(f"**{today.strftime('%B %Y')}**")
        
        # Day headers
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        header_cols = st.columns(7)
        for i, day in enumerate(days):
            header_cols[i].write(f"**{day}**")
        
        # Calendar days - INTERACTIVE
        for week in cal:
            week_cols = st.columns(7)
            for i, day in enumerate(week):
                if day == 0:
                    week_cols[i].write("")
                else:
                    day_str = str(day)
                    if day == today.day:
                        # Highlight today
                        week_cols[i].markdown(
                            f"<div class='calendar-day today'><strong>{day_str}</strong></div>", 
                            unsafe_allow_html=True
                        )
                    else:
                        # Make days clickable
                        if week_cols[i].button(day_str, key=f"day_{day}", use_container_width=True):
                            selected_date = date(today.year, today.month, day)
                            st.session_state.selected_calendar_date = selected_date
                            st.info(f"Selected date: {selected_date.strftime('%d.%m.%Y')}")
                            # Here you could show appointments for selected date
        
        st.markdown("---")
        
        # Quick Actions
        st.subheader("Quick Actions")
        if st.button("View All Appointments", use_container_width=True):
            st.session_state.menu = "Schedule Appointment"
            st.rerun()
            
        if st.button("Contact Lens Management", use_container_width=True):
            st.session_state.menu = "Contact Lenses"
            st.rerun()
            
        if st.button("System Settings", use_container_width=True) and st.session_state.role == "admin":
            st.session_state.menu = "System Settings"
            st.rerun()
        
        # Upcoming Appointments
        st.subheader("Upcoming Appointments")
        upcoming = get_upcoming_appointments(3)
        if not upcoming.empty:
            for _, apt in upcoming.iterrows():
                apt_time = pd.to_datetime(apt['appointment_date']).strftime('%d.%m.%Y %H:%M')
                st.write(f"**{apt_time}**")
                st.caption(f"{apt['first_name']} {apt['last_name']} - {apt['appointment_type']}")
        else:
            st.info("No upcoming appointments")

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
            st.markdown("#### Chief Complaint & General Health")
            chief_complaint = st.text_area("Chief Complaint / Reason for Visit", height=60)
            general_health = st.text_area("General health status", height=80)
            current_medications = st.text_area("Current medications", height=80)
            allergies = st.text_area("Allergies", height=80)
            
        with col2:
            st.markdown("#### History")
            headaches = st.text_area("Headaches / Migraines", height=80)
            family_history = st.text_area("Family medical history", height=80)
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
        
        # Dodana Run Ophtalcam Device tipka IZVAN forme
        uploaded = st.file_uploader("Upload medical reports (PDF/JPG/PNG)", 
                                  type=['pdf', 'jpg', 'png'], 
                                  accept_multiple_files=True)
        
        col_device = st.columns(2)
        with col_device[0]:
            # OphtalCAM button outside the form
            pass
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            back_button = st.form_submit_button("Back to Dashboard", use_container_width=True)
        with col_btn2:
            submit_button = st.form_submit_button("Save & Continue → Refraction", use_container_width=True)
        
        if back_button:
            st.session_state.menu = "Dashboard"
            st.session_state.exam_step = None
            st.rerun()
        
        if submit_button:
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
                    (patient_id, chief_complaint, general_health, current_medications, allergies, headaches_history, family_history,
                     ocular_history, previous_surgeries, last_eye_exam, smoking_status, alcohol_consumption, occupation, hobbies, uploaded_reports)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (pinfo['id'], chief_complaint, general_health, current_medications, allergies, headaches, family_history, 
                     ocular_history, previous_surgeries, last_eye_exam, smoking, alcohol, occupation, hobbies, json.dumps(files)))
                conn.commit()
                st.success("Medical history saved successfully!")
                st.session_state.exam_step = "refraction"
                st.rerun()
            except Exception as e:
                st.error(f"Database error: {str(e)}")
    
    # OphtalCAM button OUTSIDE the form
    st.markdown("#### OphtalCAM Device Integration")
    if st.button("Run Ophtalcam Device", use_container_width=True, key="run_ophtalcam_mh"):
        st.info("OphtalCAM device integration would be implemented here")

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

    # 1) Vision Examination WITH ADD/DEG - COMPACT HORIZONTAL LAYOUT
    st.markdown("<div class='exam-section'><h4>Vision Examination</h4></div>", unsafe_allow_html=True)
    with st.form("vision_form"):
        st.markdown("**Habitual Correction**")
        habitual_type = st.selectbox("Type of Correction", 
                                   ["None", "Spectacles", "Soft Contact Lenses", "RGP", "Scleral", "Ortho-K", "Other"])
        
        # COMPACT HORIZONTAL LAYOUT za habitual korekciju
        st.markdown("**Habitual Correction Parameters**")
        col_headers = st.columns(9)
        with col_headers[0]:
            st.write("**Eye**")
        with col_headers[1]:
            st.write("**Dsph**")
        with col_headers[2]:
            st.write("**Dcyl**")
        with col_headers[3]:
            st.write("**Ax**")
        with col_headers[4]:
            st.write("**Add**")
        with col_headers[5]:
            st.write("**Deg**")
        with col_headers[6]:
            st.write("**Dist**")
        with col_headers[7]:
            st.write("**VA**")
        with col_headers[8]:
            st.write("**Mod**")
        
        col_od = st.columns(9)
        with col_od[0]:
            st.write("**OD**")
        with col_od[1]:
            h_od_dsph = st.text_input("Dsph OD", placeholder="-2.00", key="h_od_dsph", label_visibility="collapsed")
        with col_od[2]:
            h_od_dcyl = st.text_input("Dcyl OD", placeholder="-0.50", key="h_od_dcyl", label_visibility="collapsed")
        with col_od[3]:
            h_od_ax = st.text_input("Ax OD", placeholder="180", key="h_od_ax", label_visibility="collapsed")
        with col_od[4]:
            h_od_add = st.text_input("Add OD", placeholder="+1.50", key="h_od_add", label_visibility="collapsed")
        with col_od[5]:
            h_od_deg = st.text_input("Deg OD", placeholder="2.00", key="h_od_deg", label_visibility="collapsed")
        with col_od[6]:
            h_od_dist = st.text_input("Dist OD", placeholder="6m", key="h_od_dist", label_visibility="collapsed")
        with col_od[7]:
            h_od_va = st.text_input("VA OD", placeholder="1.0", key="h_od_va", label_visibility="collapsed")
        with col_od[8]:
            h_od_mod = st.text_input("Mod OD", placeholder="-2", key="h_od_mod", label_visibility="collapsed")
        
        col_os = st.columns(9)
        with col_os[0]:
            st.write("**OS**")
        with col_os[1]:
            h_os_dsph = st.text_input("Dsph OS", placeholder="-2.00", key="h_os_dsph", label_visibility="collapsed")
        with col_os[2]:
            h_os_dcyl = st.text_input("Dcyl OS", placeholder="-0.50", key="h_os_dcyl", label_visibility="collapsed")
        with col_os[3]:
            h_os_ax = st.text_input("Ax OS", placeholder="180", key="h_os_ax", label_visibility="collapsed")
        with col_os[4]:
            h_os_add = st.text_input("Add OS", placeholder="+1.50", key="h_os_add", label_visibility="collapsed")
        with col_os[5]:
            h_os_deg = st.text_input("Deg OS", placeholder="2.00", key="h_os_deg", label_visibility="collapsed")
        with col_os[6]:
            h_os_dist = st.text_input("Dist OS", placeholder="6m", key="h_os_dist", label_visibility="collapsed")
        with col_os[7]:
            h_os_va = st.text_input("VA OS", placeholder="1.0", key="h_os_va", label_visibility="collapsed")
        with col_os[8]:
            h_os_mod = st.text_input("Mod OS", placeholder="-2", key="h_os_mod", label_visibility="collapsed")
        
        # Binocular vision centrirano
        st.markdown("**Binocular Vision**")
        col_bin = st.columns(2)
        with col_bin[0]:
            h_bin_va = st.text_input("Habitual Binocular VA", placeholder="1.0 or 20/20", key="h_bin_va")
        with col_bin[1]:
            h_pd = st.text_input("PD (mm)", placeholder="e.g., 62", key="h_pd")
        
        st.markdown("**Uncorrected Vision**")
        col_uc_headers = st.columns(4)
        with col_uc_headers[0]:
            st.write("**Eye**")
        with col_uc_headers[1]:
            st.write("**VA**")
        with col_uc_headers[2]:
            st.write("**Mod**")
        with col_uc_headers[3]:
            st.write("**Binocular**")
        
        col_uc_od = st.columns(4)
        with col_uc_od[0]:
            st.write("**OD**")
        with col_uc_od[1]:
            uc_od_va = st.text_input("Uncorrected VA OD", placeholder="1.0", key="uc_od_va", label_visibility="collapsed")
        with col_uc_od[2]:
            uc_od_mod = st.text_input("Modifier OD", placeholder="-2", key="uc_od_mod", label_visibility="collapsed")
        with col_uc_od[3]:
            uc_bin_va = st.text_input("Uncorrected Binocular VA", placeholder="1.0", key="uc_bin_va", label_visibility="collapsed")
        
        col_uc_os = st.columns(4)
        with col_uc_os[0]:
            st.write("**OS**")
        with col_uc_os[1]:
            uc_os_va = st.text_input("Uncorrected VA OS", placeholder="1.0", key="uc_os_va", label_visibility="collapsed")
        with col_uc_os[2]:
            uc_os_mod = st.text_input("Modifier OS", placeholder="-2", key="uc_os_mod", label_visibility="collapsed")
        with col_uc_os[3]:
            # Empty space for alignment
            st.write("")
        
        vision_notes = st.text_area("Vision Notes", height=60, key="vision_notes")
        
        submit_vision = st.form_submit_button("Save Vision Data", use_container_width=True)
        
        if submit_vision:
            st.session_state.refraction.update({
                'habitual_type': habitual_type,
                'habitual_od_va': h_od_va, 'habitual_od_modifier': h_od_mod,
                'habitual_os_va': h_os_va, 'habitual_os_modifier': h_os_mod,
                'habitual_binocular_va': h_bin_va, 'habitual_pd': h_pd,
                'habitual_add_od': h_od_add, 'habitual_add_os': h_os_add,
                'habitual_deg_od': h_od_deg, 'habitual_deg_os': h_os_deg,
                'uncorrected_od_va': uc_od_va, 'uncorrected_od_modifier': uc_od_mod,
                'uncorrected_os_va': uc_os_va, 'uncorrected_os_modifier': uc_os_mod,
                'uncorrected_binocular_va': uc_bin_va,
                'vision_notes': vision_notes
            })
            st.success("Vision data saved!")

    # 2) Objective Refraction
    st.markdown("<div class='exam-section'><h4>Objective Refraction</h4></div>", unsafe_allow_html=True)
    with st.form("objective_form"):
        # Metoda i vrijeme jedno pored drugog
        col_method_time = st.columns(2)
        with col_method_time[0]:
            objective_method = st.selectbox("Method", ["Autorefractor", "Retinoscopy", "Other"], key="obj_method")
        with col_method_time[1]:
            objective_time = st.time_input("Time of measurement", value=datetime.now().time(), key="obj_time")
        
        # COMPACT HORIZONTAL LAYOUT za objektivnu refrakciju
        st.markdown("**Objective Refraction Parameters**")
        col_obj_headers = st.columns(6)
        with col_obj_headers[0]:
            st.write("**Eye**")
        with col_obj_headers[1]:
            st.write("**Sphere**")
        with col_obj_headers[2]:
            st.write("**Cylinder**")
        with col_obj_headers[3]:
            st.write("**Axis**")
        with col_obj_headers[4]:
            st.write("**VA**")
        with col_obj_headers[5]:
            st.write("**Mod**")
        
        col_obj_od = st.columns(6)
        with col_obj_od[0]:
            st.write("**OD**")
        with col_obj_od[1]:
            obj_od_sph = st.number_input("Sphere OD", value=0.0, step=0.25, format="%.2f", key="obj_od_sph", label_visibility="collapsed")
        with col_obj_od[2]:
            obj_od_cyl = st.number_input("Cylinder OD", value=0.0, step=0.25, format="%.2f", key="obj_od_cyl", label_visibility="collapsed")
        with col_obj_od[3]:
            obj_od_axis = st.number_input("Axis OD", min_value=0, max_value=180, value=0, key="obj_od_axis", label_visibility="collapsed")
        with col_obj_od[4]:
            obj_od_va = st.text_input("VA OD", placeholder="1.0", key="obj_od_va", label_visibility="collapsed")
        with col_obj_od[5]:
            obj_od_mod = st.text_input("Mod OD", placeholder="-2", key="obj_od_mod", label_visibility="collapsed")
            
        col_obj_os = st.columns(6)
        with col_obj_os[0]:
            st.write("**OS**")
        with col_obj_os[1]:
            obj_os_sph = st.number_input("Sphere OS", value=0.0, step=0.25, format="%.2f", key="obj_os_sph", label_visibility="collapsed")
        with col_obj_os[2]:
            obj_os_cyl = st.number_input("Cylinder OS", value=0.0, step=0.25, format="%.2f", key="obj_os_cyl", label_visibility="collapsed")
        with col_obj_os[3]:
            obj_os_axis = st.number_input("Axis OS", min_value=0, max_value=180, value=0, key="obj_os_axis", label_visibility="collapsed")
        with col_obj_os[4]:
            obj_os_va = st.text_input("VA OS", placeholder="1.0", key="obj_os_va", label_visibility="collapsed")
        with col_obj_os[5]:
            obj_os_mod = st.text_input("Mod OS", placeholder="-2", key="obj_os_mod", label_visibility="collapsed")
            
        objective_notes = st.text_area("Objective Notes", height=60, key="obj_notes")
        
        submit_objective = st.form_submit_button("Save Objective Data", use_container_width=True)
        
        if submit_objective:
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
        subj_method = st.selectbox("Subjective Method", ["Fogging", "With Cycloplegic", "Other"], key="subj_method")
        
        # COMPACT HORIZONTAL LAYOUT za subjektivnu refrakciju
        st.markdown("**Subjective Refraction Parameters**")
        col_subj_headers = st.columns(9)
        with col_subj_headers[0]:
            st.write("**Eye**")
        with col_subj_headers[1]:
            st.write("**Sphere**")
        with col_subj_headers[2]:
            st.write("**Cylinder**")
        with col_subj_headers[3]:
            st.write("**Axis**")
        with col_subj_headers[4]:
            st.write("**VA**")
        with col_subj_headers[5]:
            st.write("**Add**")
        with col_subj_headers[6]:
            st.write("**Deg**")
        with col_subj_headers[7]:
            st.write("**Dist**")
        with col_subj_headers[8]:
            st.write("**Mod**")
        
        col_subj_od = st.columns(9)
        with col_subj_od[0]:
            st.write("**OD**")
        with col_subj_od[1]:
            subj_od_sph = st.number_input("Sphere OD", value=0.0, step=0.25, format="%.2f", key="subj_od_sph", label_visibility="collapsed")
        with col_subj_od[2]:
            subj_od_cyl = st.number_input("Cylinder OD", value=0.0, step=0.25, format="%.2f", key="subj_od_cyl", label_visibility="collapsed")
        with col_subj_od[3]:
            subj_od_axis = st.number_input("Axis OD", min_value=0, max_value=180, value=0, key="subj_od_axis", label_visibility="collapsed")
        with col_subj_od[4]:
            subj_od_va = st.text_input("VA OD", placeholder="1.0", key="subj_od_va", label_visibility="collapsed")
        with col_subj_od[5]:
            subj_od_add = st.text_input("ADD OD", placeholder="+1.50", key="subj_od_add", label_visibility="collapsed")
        with col_subj_od[6]:
            subj_od_deg = st.text_input("DEG OD", placeholder="2.00", key="subj_od_deg", label_visibility="collapsed")
        with col_subj_od[7]:
            subj_od_dist = st.text_input("Dist OD", placeholder="6m", key="subj_od_dist", label_visibility="collapsed")
        with col_subj_od[8]:
            subj_od_mod = st.text_input("Mod OD", placeholder="-2", key="subj_od_mod", label_visibility="collapsed")
            
        col_subj_os = st.columns(9)
        with col_subj_os[0]:
            st.write("**OS**")
        with col_subj_os[1]:
            subj_os_sph = st.number_input("Sphere OS", value=0.0, step=0.25, format="%.2f", key="subj_os_sph", label_visibility="collapsed")
        with col_subj_os[2]:
            subj_os_cyl = st.number_input("Cylinder OS", value=0.0, step=0.25, format="%.2f", key="subj_os_cyl", label_visibility="collapsed")
        with col_subj_os[3]:
            subj_os_axis = st.number_input("Axis OS", min_value=0, max_value=180, value=0, key="subj_os_axis", label_visibility="collapsed")
        with col_subj_os[4]:
            subj_os_va = st.text_input("VA OS", placeholder="1.0", key="subj_os_va", label_visibility="collapsed")
        with col_subj_os[5]:
            subj_os_add = st.text_input("ADD OS", placeholder="+1.50", key="subj_os_add", label_visibility="collapsed")
        with col_subj_os[6]:
            subj_os_deg = st.text_input("DEG OS", placeholder="2.00", key="subj_os_deg", label_visibility="collapsed")
        with col_subj_os[7]:
            subj_os_dist = st.text_input("Dist OS", placeholder="6m", key="subj_os_dist", label_visibility="collapsed")
        with col_subj_os[8]:
            subj_os_mod = st.text_input("Mod OS", placeholder="-2", key="subj_os_mod", label_visibility="collapsed")
        
        # Distance s DEG Distance
        col_distance = st.columns(2)
        with col_distance[0]:
            subjective_distance = st.text_input("Distance", placeholder="e.g., 6m", key="subj_distance")
        with col_distance[1]:
            subjective_deg_distance = st.text_input("DEG Distance", placeholder="e.g., 2.00", key="subj_deg_distance")
        
        subjective_notes = st.text_area("Subjective Notes", height=60, key="subj_notes")
        
        submit_subjective = st.form_submit_button("Save Subjective Data", use_container_width=True)
        
        if submit_subjective:
            st.session_state.refraction.update({
                'subjective_method': subj_method,
                'subjective_od_sphere': subj_od_sph, 'subjective_od_cylinder': subj_od_cyl, 'subjective_od_axis': subj_od_axis,
                'subjective_od_va': subj_od_va, 'subjective_add_od': subj_od_add, 'subjective_deg_od': subj_od_deg,
                'subjective_os_sphere': subj_os_sph, 'subjective_os_cylinder': subj_os_cyl, 'subjective_os_axis': subj_os_axis,
                'subjective_os_va': subj_os_va, 'subjective_add_os': subj_os_add, 'subjective_deg_os': subj_os_deg,
                'subjective_distance': subjective_distance,
                'subjective_deg_distance': subjective_deg_distance,
                'subjective_notes': subjective_notes
            })
            st.success("Subjective data saved!")

    # 4) Final Prescription WITH ADD/DEG
    st.markdown("<div class='exam-section'><h4>Final Prescription</h4></div>", unsafe_allow_html=True)
    with st.form("final_form"):
        # COMPACT HORIZONTAL LAYOUT za finalnu korekciju
        st.markdown("**Final Prescription Parameters**")
        col_final_headers = st.columns(9)
        with col_final_headers[0]:
            st.write("**Eye**")
        with col_final_headers[1]:
            st.write("**Sphere**")
        with col_final_headers[2]:
            st.write("**Cylinder**")
        with col_final_headers[3]:
            st.write("**Axis**")
        with col_final_headers[4]:
            st.write("**VA**")
        with col_final_headers[5]:
            st.write("**Add**")
        with col_final_headers[6]:
            st.write("**Deg**")
        with col_final_headers[7]:
            st.write("**Dist**")
        with col_final_headers[8]:
            st.write("**Mod**")
        
        col_final_od = st.columns(9)
        with col_final_od[0]:
            st.write("**OD**")
        with col_final_od[1]:
            final_od_sph = st.number_input("Final Sphere OD", value=0.0, step=0.25, format="%.2f", key="final_od_sph", label_visibility="collapsed")
        with col_final_od[2]:
            final_od_cyl = st.number_input("Final Cylinder OD", value=0.0, step=0.25, format="%.2f", key="final_od_cyl", label_visibility="collapsed")
        with col_final_od[3]:
            final_od_axis = st.number_input("Final Axis OD", min_value=0, max_value=180, value=0, key="final_od_axis", label_visibility="collapsed")
        with col_final_od[4]:
            final_od_va = st.text_input("VA OD", placeholder="1.0", key="final_od_va", label_visibility="collapsed")
        with col_final_od[5]:
            final_add_od = st.text_input("Final ADD OD", placeholder="+1.50", key="final_add_od", label_visibility="collapsed")
        with col_final_od[6]:
            final_deg_od = st.text_input("Final DEG OD", placeholder="2.00", key="final_deg_od", label_visibility="collapsed")
        with col_final_od[7]:
            final_od_dist = st.text_input("Dist OD", placeholder="6m", key="final_od_dist", label_visibility="collapsed")
        with col_final_od[8]:
            final_od_mod = st.text_input("Mod OD", placeholder="-2", key="final_od_mod", label_visibility="collapsed")
            
        col_final_os = st.columns(9)
        with col_final_os[0]:
            st.write("**OS**")
        with col_final_os[1]:
            final_os_sph = st.number_input("Final Sphere OS", value=0.0, step=0.25, format="%.2f", key="final_os_sph", label_visibility="collapsed")
        with col_final_os[2]:
            final_os_cyl = st.number_input("Final Cylinder OS", value=0.0, step=0.25, format="%.2f", key="final_os_cyl", label_visibility="collapsed")
        with col_final_os[3]:
            final_os_axis = st.number_input("Final Axis OS", min_value=0, max_value=180, value=0, key="final_os_axis", label_visibility="collapsed")
        with col_final_os[4]:
            final_os_va = st.text_input("VA OS", placeholder="1.0", key="final_os_va", label_visibility="collapsed")
        with col_final_os[5]:
            final_add_os = st.text_input("Final ADD OS", placeholder="+1.50", key="final_add_os", label_visibility="collapsed")
        with col_final_os[6]:
            final_deg_os = st.text_input("Final DEG OS", placeholder="2.00", key="final_deg_os", label_visibility="collapsed")
        with col_final_os[7]:
            final_os_dist = st.text_input("Dist OS", placeholder="6m", key="final_os_dist", label_visibility="collapsed")
        with col_final_os[8]:
            final_os_mod = st.text_input("Mod OS", placeholder="-2", key="final_os_mod", label_visibility="collapsed")
        
        col_bin1, col_bin2 = st.columns(2)
        with col_bin1:
            binocular_balance = st.selectbox("Binocular Balance", ["Balanced", "OD dominant", "OS dominant", "Unbalanced"], key="bin_balance")
            stereopsis = st.text_input("Stereoacuity", placeholder="e.g., 40 arcsec", key="stereopsis")
            final_bin_va = st.text_input("Final Binocular VA", placeholder="e.g., 1.0 or 20/20", key="final_bin_va")
            
        with col_bin2:
            final_deg_distance = st.text_input("DEG Distance", placeholder="e.g., 2.00", key="final_deg_distance")
            prescription_notes = st.text_area("Prescription Notes", height=80, key="presc_notes")
        
        # Tabo Scheme Display - DVA SCHEMA JEDAN PORED DRUGOG
        st.markdown("#### Tabo Scheme - Axis Visualization")
        tabo_html = draw_tabo_scheme(final_od_axis, final_os_axis)
        st.markdown(tabo_html, unsafe_allow_html=True)
        
        submit_final = st.form_submit_button("Save Refraction & Continue", use_container_width=True)
        
        if submit_final:
            try:
                p = pd.read_sql("SELECT id FROM patients WHERE patient_id = ?", conn, params=(pid_code,)).iloc[0]
                pid = p['id']
                
                c = conn.cursor()
                c.execute('''
                    INSERT INTO refraction_exams (
                        patient_id, habitual_type, habitual_od_va, habitual_od_modifier, habitual_os_va, habitual_os_modifier,
                        habitual_binocular_va, habitual_pd, habitual_add_od, habitual_add_os, habitual_deg_od, habitual_deg_os,
                        vision_notes, uncorrected_od_va, uncorrected_od_modifier, uncorrected_os_va, uncorrected_os_modifier, uncorrected_binocular_va,
                        objective_method, objective_time, autorefractor_od_sphere, autorefractor_od_cylinder, autorefractor_od_axis,
                        autorefractor_os_sphere, autorefractor_os_cylinder, autorefractor_os_axis, objective_notes,
                        subjective_method, subjective_od_sphere, subjective_od_cylinder, subjective_od_axis, subjective_od_va, subjective_add_od, subjective_deg_od,
                        subjective_os_sphere, subjective_os_cylinder, subjective_os_axis, subjective_os_va, subjective_add_os, subjective_deg_os, subjective_distance, subjective_deg_distance, subjective_notes,
                        binocular_balance, stereopsis,
                        final_prescribed_od_sphere, final_prescribed_od_cylinder, final_prescribed_od_axis, final_add_od, final_deg_od,
                        final_prescribed_os_sphere, final_prescribed_os_cylinder, final_prescribed_os_axis, final_add_os, final_deg_os,
                        final_prescribed_binocular_va, final_deg_distance, prescription_notes
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ''', (
                    pid, st.session_state.refraction.get('habitual_type'),
                    st.session_state.refraction.get('habitual_od_va'), st.session_state.refraction.get('habitual_od_modifier'),
                    st.session_state.refraction.get('habitual_os_va'), st.session_state.refraction.get('habitual_os_modifier'),
                    st.session_state.refraction.get('habitual_binocular_va'), st.session_state.refraction.get('habitual_pd'),
                    st.session_state.refraction.get('habitual_add_od'), st.session_state.refraction.get('habitual_add_os'),
                    st.session_state.refraction.get('habitual_deg_od'), st.session_state.refraction.get('habitual_deg_os'),
                    st.session_state.refraction.get('vision_notes'),
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
                    st.session_state.refraction.get('subjective_distance'), st.session_state.refraction.get('subjective_deg_distance'), st.session_state.refraction.get('subjective_notes'),
                    binocular_balance, stereopsis,
                    final_od_sph, final_od_cyl, final_od_axis, final_add_od, final_deg_od,
                    final_os_sph, final_os_cyl, final_os_axis, final_add_os, final_deg_os,
                    final_bin_va, final_deg_distance, prescription_notes
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
            motility = st.text_area("Ocular motility", placeholder="Ductions, versions", height=80, key="motility")
            hirschberg = st.text_input("Hirschberg test", placeholder="e.g., Central, 15° temporal", key="hirschberg")
            cover_distance = st.text_input("Cover test - Distance", placeholder="e.g., Ortho, 4△ XP", key="cover_dist")
            cover_near = st.text_input("Cover test - Near", placeholder="e.g., Ortho, 6△ XP", key="cover_near")
            
        with col2:
            st.markdown("#### Pupils & Visual Fields")
            pupils = st.text_input("Pupils", placeholder="e.g., 4mm, round, reactive", key="pupils")
            rapd = st.selectbox("RAPD", ["None", "Present OD", "Present OS", "Unsure"], key="rapd")
            confrontation = st.text_area("Confrontation fields", placeholder="Visual field assessment", height=80, key="confrontation")
            other_notes = st.text_area("Other functional notes", height=60, key="func_other_notes")
        
        submit_functional = st.form_submit_button("Save Functional Tests", use_container_width=True)
        
        if submit_functional:
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
                                          height=120, key="bio_od")
        with col_bio2:
            st.markdown("<div class='eye-column'><strong>Left Eye (OS)</strong></div>", unsafe_allow_html=True)
            biomicroscopy_os = st.text_area("Biomicroscopy OS", 
                                          placeholder="Cornea, conjunctiva, anterior chamber, iris, lens", 
                                          height=120, key="bio_os")
        biomicroscopy_notes = st.text_area("Biomicroscopy notes", height=60, key="bio_notes")

        st.markdown("#### Anterior Chamber & Angle")
        col_ac1, col_ac2 = st.columns(2)
        with col_ac1:
            st.markdown("<div class='eye-column'><strong>Right Eye (OD)</strong></div>", unsafe_allow_html=True)
            ac_depth_od = st.selectbox("AC Depth OD", ["Deep", "Medium", "Shallow", "Flat"], key="ac_depth_od")
            ac_depth_value_od = st.text_input("AC Depth Value OD (mm)", placeholder="e.g., 3.2", key="ac_depth_value_od")
            ac_volume_od = st.text_input("AC Volume OD", placeholder="e.g., Normal", key="ac_vol_od")
            angle_od = st.selectbox("Iridocorneal Angle OD", ["Open", "Narrow", "Closed", "Grade 0-4"], key="angle_od")
            angle_value_od = st.text_input("Angle Value OD (°)", placeholder="e.g., 45", key="angle_value_od")
        with col_ac2:
            st.markdown("<div class='eye-column'><strong>Left Eye (OS)</strong></div>", unsafe_allow_html=True)
            ac_depth_os = st.selectbox("AC Depth OS", ["Deep", "Medium", "Shallow", "Flat"], key="ac_depth_os")
            ac_depth_value_os = st.text_input("AC Depth Value OS (mm)", placeholder="e.g., 3.1", key="ac_depth_value_os")
            ac_volume_os = st.text_input("AC Volume OS", placeholder="e.g., Normal", key="ac_vol_os")
            angle_os = st.selectbox("Iridocorneal Angle OS", ["Open", "Narrow", "Closed", "Grade 0-4"], key="angle_os")
            angle_value_os = st.text_input("Angle Value OS (°)", placeholder="e.g., 40", key="angle_value_os")

        st.markdown("#### Tonometry & Pachymetry")
        col_tono1, col_tono2 = st.columns(2)
        with col_tono1:
            st.markdown("<div class='eye-column'><strong>Right Eye (OD)</strong></div>", unsafe_allow_html=True)
            pachymetry_od = st.number_input("CCT OD (μm)", min_value=400, max_value=700, value=540, step=5, key="pachy_od")
            iop_od = st.text_input("IOP OD (mmHg)", placeholder="e.g., 16", key="iop_od")
        with col_tono2:
            st.markdown("<div class='eye-column'><strong>Left Eye (OS)</strong></div>", unsafe_allow_html=True)
            pachymetry_os = st.number_input("CCT OS (μm)", min_value=400, max_value=700, value=540, step=5, key="pachy_os")
            iop_os = st.text_input("IOP OS (mmHg)", placeholder="e.g., 15", key="iop_os")
        
        col_tono3, col_tono4 = st.columns(2)
        with col_tono3:
            tonometry_type = st.selectbox("Tonometry Type", 
                                        ["Goldmann", "Non-contact", "iCare", "Perkins", "Other"], key="tono_type")
            tonometry_time = st.time_input("Tonometry Time", value=datetime.now().time(), key="tono_time")
        with col_tono4:
            tonometry_compensation = st.selectbox("Compensation", 
                                               ["None", "CCT adjusted", "DCT", "Other"], key="tono_comp")

        st.markdown("#### Pupillography")
        pupillography_results = st.text_area("Pupillography results", 
                                           placeholder="Pupil size, reactivity, shape", 
                                           height=80, key="pupil_results")
        pupillography_notes = st.text_area("Pupillography notes", height=60, key="pupil_notes")
        
        uploaded_files = st.file_uploader("Upload anterior segment images", 
                                        type=['pdf', 'png', 'jpg', 'jpeg'], 
                                        accept_multiple_files=True, key="ant_upload")

        submit_anterior = st.form_submit_button("Save Anterior Segment", use_container_width=True)
        
        if submit_anterior:
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
                                 ["Indirect ophthalmoscopy", "Fundus camera", "Widefield", "Slit lamp", "Other"], key="fundus_type")
        
        col_fundus1, col_fundus2 = st.columns(2)
        with col_fundus1:
            st.markdown("<div class='eye-column'><strong>Right Eye (OD)</strong></div>", unsafe_allow_html=True)
            fundus_od = st.text_area("Fundus OD", 
                                   placeholder="Optic disc, macula, vessels, periphery", 
                                   height=120, key="fundus_od")
        with col_fundus2:
            st.markdown("<div class='eye-column'><strong>Left Eye (OS)</strong></div>", unsafe_allow_html=True)
            fundus_os = st.text_area("Fundus OS", 
                                   placeholder="Optic disc, macula, vessels, periphery", 
                                   height=120, key="fundus_os")
        fundus_notes = st.text_area("Fundus examination notes", height=80, key="fundus_notes")

        st.markdown("#### Direct/Indirect Ophthalmoscopy")
        col_ophth1, col_ophth2 = st.columns(2)
        with col_ophth1:
            st.markdown("<div class='eye-column'><strong>Right Eye (OD)</strong></div>", unsafe_allow_html=True)
            ophthalmoscopy_od = st.text_area("Ophthalmoscopy OD", 
                                           placeholder="Optic disc, macula, vessels, periphery findings", 
                                           height=100, key="ophth_od")
        with col_ophth2:
            st.markdown("<div class='eye-column'><strong>Left Eye (OS)</strong></div>", unsafe_allow_html=True)
            ophthalmoscopy_os = st.text_area("Ophthalmoscopy OS", 
                                           placeholder="Optic disc, macula, vessels, periphery findings", 
                                           height=100, key="ophth_os")

        st.markdown("#### OCT Imaging")
        col_oct1, col_oct2 = st.columns(2)
        with col_oct1:
            st.markdown("<div class='eye-column'><strong>Right Eye (OD)</strong></div>", unsafe_allow_html=True)
            oct_macula_od = st.text_area("OCT Macula OD", placeholder="Macular thickness, morphology", height=80, key="oct_mac_od")
            oct_rnfl_od = st.text_area("OCT RNFL OD", placeholder="RNFL thickness, symmetry", height=80, key="oct_rnfl_od")
        with col_oct2:
            st.markdown("<div class='eye-column'><strong>Left Eye (OS)</strong></div>", unsafe_allow_html=True)
            oct_macula_os = st.text_area("OCT Macula OS", placeholder="Macular thickness, morphology", height=80, key="oct_mac_os")
            oct_rnfl_os = st.text_area("OCT RNFL OS", placeholder="RNFL thickness, symmetry", height=80, key="oct_rnfl_os")
        oct_notes = st.text_area("OCT notes", height=60, key="oct_notes")

        # Enhanced image upload for posterior segment
        st.markdown("#### Fundus & OCT Images")
        uploaded_files = st.file_uploader("Upload posterior segment images (OCT, fundus photos, angiography)", 
                                        type=['pdf', 'png', 'jpg', 'jpeg', 'tiff'], 
                                        accept_multiple_files=True,
                                        help="Upload high-quality fundus photos, OCT scans, angiography images", key="post_upload")
        
        if uploaded_files:
            st.info(f"{len(uploaded_files)} file(s) selected for upload")

        submit_posterior = st.form_submit_button("Save Posterior Segment", use_container_width=True)
        
        if submit_posterior:
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
                     oct_macula_od, oct_macula_os, oct_rnfl_od, oct_rnfl_os, oct_notes, 
                     ophthalmoscopy_od, ophthalmoscopy_os, uploaded_files)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (p['id'], fundus_type, fundus_od, fundus_os, fundus_notes,
                     oct_macula_od, oct_macula_os, oct_rnfl_od, oct_rnfl_os, oct_notes,
                     ophthalmoscopy_od, ophthalmoscopy_os, json.dumps(file_paths)))
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
                               ["Soft", "RGP", "Scleral", "Custom", "Ortho-K", "Hybrid", "Other"], key="lens_type")
        
        # General lens parameters
        st.markdown("#### General Lens Parameters")
        col_gen1, col_gen2 = st.columns(2)
        with col_gen1:
            lens_design = st.text_input("Lens Design", placeholder="e.g., Spherical, Aspheric, Toric, Multifocal, Back Toric, Bitoric, Rose K2, etc.", key="lens_design")
            lens_material = st.text_input("Lens Material", placeholder="e.g., Boston XO, Senofilcon A, etc.", key="lens_material")
        with col_gen2:
            lens_color = st.text_input("Lens Color/Visibility", placeholder="e.g., Clear, Blue, Handling tint", key="lens_color")
            brand = st.text_input("Brand/Manufacturer", placeholder="e.g., Acuvue, Biofinity, etc.", key="cl_brand")
        
        # Power parameters with ADD for both eyes
        st.markdown("#### Lens Power Parameters")
        col_power1, col_power2 = st.columns(2)
        
        with col_power1:
            st.markdown("<div class='eye-column'><strong>Right Eye (OD)</strong></div>", unsafe_allow_html=True)
            od_sphere = st.number_input("Sphere OD", value=0.0, step=0.25, format="%.2f", key="cl_od_sph")
            od_cylinder = st.number_input("Cylinder OD", value=0.0, step=0.25, format="%.2f", key="cl_od_cyl")
            od_axis = st.number_input("Axis OD", min_value=0, max_value=180, value=0, key="cl_od_axis")
            od_add = st.text_input("ADD OD", placeholder="e.g., +1.50 for multifocal", key="cl_od_add")
            
        with col_power2:
            st.markdown("<div class='eye-column'><strong>Left Eye (OS)</strong></div>", unsafe_allow_html=True)
            os_sphere = st.number_input("Sphere OS", value=0.0, step=0.25, format="%.2f", key="cl_os_sph")
            os_cylinder = st.number_input("Cylinder OS", value=0.0, step=0.25, format="%.2f", key="cl_os_cyl")
            os_axis = st.number_input("Axis OS", min_value=0, max_value=180, value=0, key="cl_os_axis")
            os_add = st.text_input("ADD OS", placeholder="e.g., +1.50 for multifocal", key="cl_os_add")
        
        # Lens-specific parameters
        if lens_type == "Soft":
            st.markdown("#### Soft Lens Parameters")
            col_soft1, col_soft2 = st.columns(2)
            with col_soft1:
                soft_base_curve = st.number_input("Base Curve (mm)", min_value=7.0, max_value=10.0, value=8.6, step=0.1, key="soft_bc")
            with col_soft2:
                soft_diameter = st.number_input("Diameter (mm)", min_value=13.0, max_value=16.0, value=14.2, step=0.1, key="soft_diam")
                
        elif lens_type == "RGP":
            st.markdown("#### RGP Lens Parameters")
            col_rgp1, col_rgp2 = st.columns(2)
            with col_rgp1:
                rgp_base_curve = st.number_input("Base Curve (mm)", min_value=6.0, max_value=9.0, value=7.8, step=0.1, key="rgp_bc")
            with col_rgp2:
                rgp_diameter = st.number_input("Diameter (mm)", min_value=8.0, max_value=11.0, value=9.2, step=0.1, key="rgp_diam")
                
        elif lens_type == "Scleral":
            st.markdown("#### Scleral Lens Parameters")
            col_scl1, col_scl2 = st.columns(2)
            with col_scl1:
                scleral_diameter = st.text_input("Diameter", placeholder="e.g., 16.5mm, 18.0mm", key="scl_diam")
            with col_scl2:
                scleral_design = st.text_input("Specific Design", placeholder="e.g., PROSE, Zenlens, etc.", key="scl_design")
                
        elif lens_type == "Ortho-K":
            st.markdown("#### Ortho-K Parameters")
            ortho_k_parameters = st.text_area("Ortho-K Treatment Parameters", 
                                            placeholder="Treatment zone, reverse curve, alignment curve details",
                                            height=100, key="ortho_k")
        
        # Fitting details
        st.markdown("#### Fitting Details & Assessment")
        col_fit1, col_fit2 = st.columns(2)
        with col_fit1:
            wearing_schedule = st.selectbox("Wearing Schedule", 
                                          ["Daily", "Weekly", "Monthly", "Extended", "Flexible", "Other"], key="wear_sched")
            care_solution = st.text_input("Care Solution", placeholder="e.g., Boston Advance, PeroxiClear", key="care_sol")
        with col_fit2:
            follow_up_date = st.date_input("Follow-up Date", value=date.today() + timedelta(days=30), key="follow_up")
        
        # Professional assessment
        professional_assessment = st.text_area("Professional Assessment", 
                                            placeholder="Lens fit evaluation, centration, movement, corneal coverage",
                                            height=100, key="prof_assess")
        patient_feedback = st.text_area("Patient Feedback & Comfort", 
                                      placeholder="Patient subjective experience, comfort, vision quality",
                                      height=80, key="pat_feedback")
        fitting_notes = st.text_area("Additional Fitting Notes", height=80, key="fit_notes")
        
        # Enhanced file upload for fitting documentation
        st.markdown("#### Fitting Documentation")
        fitting_images = st.file_uploader("Upload fitting images/videos (slit lamp, topography, fit assessment)", 
                                        type=['png', 'jpg', 'jpeg', 'mp4', 'mov'],
                                        accept_multiple_files=True,
                                        help="Document lens fit with slit lamp images, topography maps, etc.", key="cl_upload")
        
        submit_cl = st.form_submit_button("Save Contact Lens Prescription", use_container_width=True)
        
        if submit_cl:
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
    
    # OphtalCAM device integration - IZVAN forme
    st.markdown("#### OphtalCAM Device Integration")
    if st.button("Start OphtalCAM Device", use_container_width=True, key="start_ophtalcam"):
        st.info("OphtalCAM device integration would be implemented here")

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
	    if st.button("Generate Prescription Report (For Optical Dispensing)", use_container_width=True, key="generate_prescription_main"):
    generate_prescription_report()
        # Custom Report Notes
        st.markdown("#### Clinical Assessment & Recommendations")
        assessment = st.text_area("Clinical Assessment", height=150, 
                                placeholder="Summarize findings, diagnosis, and treatment plan...", key="assessment")
        
        recommendations = st.text_area("Recommendations & Follow-up", height=120,
                                     placeholder="Next steps, medications, follow-up schedule...", key="recommendations")

        # Generate Professional Report
        st.markdown("#### Generate Final Report")
        
        # HTML Report za print
        if st.button("Generate Printable Report (HTML)", use_container_width=True, key="generate_html"):
            
            # Collect data for report
            refraction_data = pd.read_sql('''
                SELECT * FROM refraction_exams 
                WHERE patient_id = (SELECT id FROM patients WHERE patient_id = ?) 
                ORDER BY exam_date DESC LIMIT 1
            ''', conn, params=(pid_code,))
            
            anterior_data = pd.read_sql('''
                SELECT * FROM anterior_segment_exams 
                WHERE patient_id = (SELECT id FROM patients WHERE patient_id = ?) 
                ORDER BY exam_date DESC LIMIT 1
            ''', conn, params=(pid_code,))
            
            cl_data = pd.read_sql('''
                SELECT * FROM contact_lens_prescriptions 
                WHERE patient_id = (SELECT id FROM patients WHERE patient_id = ?) 
                ORDER BY prescription_date DESC LIMIT 1
            ''', conn, params=(pid_code,))

            # Generiraj HTML za print
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Clinical Report - {p['first_name']} {p['last_name']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; }}
        .section {{ margin-bottom: 20px; }}
        .section-title {{ font-weight: bold; font-size: 16px; margin-bottom: 10px; border-bottom: 1px solid #ccc; padding-bottom: 5px; }}
        .patient-info {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
        .signature {{ margin-top: 50px; border-top: 1px solid #333; padding-top: 20px; }}
        @media print {{
            body {{ margin: 0; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>OPHTHALCAM CLINICAL MANAGEMENT SYSTEM</h1>
        <h2>CLINICAL REPORT</h2>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>

    <div class="section">
        <div class="section-title">CLINICIAN INFORMATION</div>
        <div class="patient-info">
            <div><strong>Clinician:</strong> {st.session_state.username}</div>
            <div><strong>Role:</strong> {st.session_state.role}</div>
            <div><strong>Report Date:</strong> {date.today().strftime('%d.%m.%Y')}</div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">PATIENT INFORMATION</div>
        <div class="patient-info">
            <div><strong>Name:</strong> {p['first_name']} {p['last_name']}</div>
            <div><strong>Patient ID:</strong> {p['patient_id']}</div>
            <div><strong>Date of Birth:</strong> {p['date_of_birth']}</div>
            <div><strong>Gender:</strong> {p['gender']}</div>
            <div><strong>Phone:</strong> {p['phone']}</div>
            <div><strong>Email:</strong> {p['email']}</div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">EXAMINATION SUMMARY</div>
        <p>{assessment if assessment else "Comprehensive ophthalmological examination performed."}</p>
    </div>

    <div class="section">
        <div class="section-title">CLINICAL FINDINGS</div>
        {"<p><strong>Refraction:</strong><br>" + 
         f"OD: {refraction_data.iloc[0].get('final_prescribed_od_sphere', '')} {refraction_data.iloc[0].get('final_prescribed_od_cylinder', '')} x {refraction_data.iloc[0].get('final_prescribed_od_axis', '')}<br>" +
         f"OS: {refraction_data.iloc[0].get('final_prescribed_os_sphere', '')} {refraction_data.iloc[0].get('final_prescribed_os_cylinder', '')} x {refraction_data.iloc[0].get('final_prescribed_os_axis', '')}<br>" +
         f"Binocular VA: {refraction_data.iloc[0].get('final_prescribed_binocular_va', 'Not recorded')}</p>" if not refraction_data.empty else "<p>Refraction: Not recorded</p>"}
        
        {"<p><strong>Anterior Segment:</strong><br>" +
         f"IOP: OD {anterior_data.iloc[0].get('tonometry_od', '')} mmHg | OS {anterior_data.iloc[0].get('tonometry_os', '')} mmHg<br>" +
         f"CCT: OD {anterior_data.iloc[0].get('pachymetry_od', '')} μm | OS {anterior_data.iloc[0].get('pachymetry_os', '')} μm</p>" if not anterior_data.empty else "<p>Anterior Segment: Not recorded</p>"}
        
        {"<p><strong>Contact Lenses:</strong> " + f"{cl_data.iloc[0].get('lens_type', '')} lenses prescribed</p>" if not cl_data.empty else ""}
    </div>

    <div class="section">
        <div class="section-title">RECOMMENDATIONS</div>
        <p>{recommendations if recommendations else "Routine follow-up recommended."}</p>
    </div>

    <div class="signature">
        <p><strong>Clinician Signature:</strong></p>
        <br><br>
        <p>_________________________________________</p>
        <p>{st.session_state.username}</p>
        <p>{date.today().strftime('%d %B %Y')}</p>
    </div>

    <div class="no-print" style="margin-top: 30px; padding: 10px; background: #f0f0f0;">
        <p><strong>Print Instructions:</strong> Press Ctrl+P to print this report</p>
    </div>
</body>
</html>
"""
            
            # Prikaži HTML u Streamlitu i omogući download
            st.markdown("### Printable Report Preview")
            st.components.v1.html(html_content, height=800, scrolling=True)
            
            # Download button za HTML file
            st.download_button(
                label="Download HTML Report",
                data=html_content,
                file_name=f"clinical_report_{p['patient_id']}_{date.today().strftime('%Y%m%d')}.html",
                mime="text/html",
                use_container_width=True
            )
            
            st.success("HTML report generated! Click 'Download HTML Report' and open the file in your browser to print.")

    except Exception as e:
        st.error(f"Error generating report: {str(e)}")
def generate_prescription_report():
    """Generate professional optometric prescription report with Tabo scheme"""
    st.markdown("<h2 class='main-header'>Optometric Prescription Report</h2>", unsafe_allow_html=True)
    
    if 'selected_patient' not in st.session_state or not st.session_state.selected_patient:
        st.error("No patient selected.")
        return
    
    pid_code = st.session_state.selected_patient
    
    try:
        # Get patient info
        p = pd.read_sql("SELECT * FROM patients WHERE patient_id = ?", conn, params=(pid_code,)).iloc[0]
        
        # Get latest refraction
        refraction_data = pd.read_sql('''
            SELECT * FROM refraction_exams 
            WHERE patient_id = (SELECT id FROM patients WHERE patient_id = ?) 
            ORDER BY exam_date DESC LIMIT 1
        ''', conn, params=(pid_code,))
        
        if refraction_data.empty:
            st.error("No refraction data found for this patient.")
            return
        
        ref = refraction_data.iloc[0]
        
        # Navigation
        col_nav = st.columns(3)
        with col_nav[0]:
            if st.button("Back to Reports", use_container_width=True):
                st.session_state.exam_step = "generate_report"
                st.rerun()
        
        st.markdown(f"### Patient: {p['first_name']} {p['last_name']} (ID: {p['patient_id']})")
        
        # Prescription parameters
        st.markdown("#### Prescription Details")
        col1, col2 = st.columns(2)
        
        with col1:
            prescription_type = st.selectbox("Prescription Type", 
                                           ["Spectacles", "Contact Lenses", "Both", "Reading Glasses", "Distance Glasses"],
                                           key="presc_type")
            pd_value = st.text_input("PD (mm)", value=ref.get('habitual_pd', '62'), key="pd_value")
            frame_type = st.text_input("Frame Type", placeholder="e.g., Full-rim, Semi-rimless", key="frame_type")
            
        with col2:
            lens_material = st.selectbox("Lens Material", 
                                       ["CR-39", "Polycarbonate", "High-Index", "Trivex", "Glass"],
                                       key="lens_material")
            lens_coating = st.multiselect("Lens Coating", 
                                        ["Anti-reflective", "UV Protection", "Scratch-resistant", "Blue Light", "Photochromic"],
                                        key="lens_coating")
            special_instructions = st.text_area("Special Instructions", height=80, key="spec_inst")
        
        # Generate Prescription Report
        if st.button("Generate Prescription Report (HTML)", use_container_width=True, key="generate_prescription"):
            
            # Tabo scheme za prescription
            tabo_html = draw_tabo_scheme(
                ref.get('final_prescribed_od_axis', ''),
                ref.get('final_prescribed_os_axis', '')
            )
            
            # Generiraj HTML za optometrijski nalaz
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Optometric Prescription - {p['first_name']} {p['last_name']}</title>
    <style>
        body {{ 
            font-family: 'Arial', sans-serif; 
            margin: 0;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }}
        .header {{ 
            text-align: center; 
            border-bottom: 3px solid #1e3c72; 
            padding-bottom: 15px; 
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #1e3c72;
            margin-bottom: 5px;
            font-size: 24px;
        }}
        .header h2 {{
            color: #2a5298;
            margin-bottom: 10px;
            font-size: 20px;
        }}
        .prescription-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin: 20px 0;
        }}
        .prescription-card {{
            border: 2px solid #1e3c72;
            border-radius: 8px;
            padding: 15px;
            background: #f8f9fa;
        }}
        .prescription-title {{
            text-align: center;
            font-weight: bold;
            font-size: 18px;
            margin-bottom: 15px;
            color: #1e3c72;
        }}
        .axis-display {{
            text-align: center;
            margin: 15px 0;
        }}
        .parameters {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 10px;
        }}
        .parameter {{
            padding: 5px;
            border-bottom: 1px solid #ddd;
        }}
        .tabo-container {{
            margin: 20px 0;
        }}
        .signature {{ 
            margin-top: 40px; 
            border-top: 2px solid #333; 
            padding-top: 20px;
        }}
        @media print {{
            body {{ margin: 0.5in; }}
            .no-print {{ display: none; }}
        }}
        .clinic-info {{
            background-color: #e8f4fd;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>OPHTHALCAM EYE CLINIC</h1>
        <h2>OPTOMETRIC PRESCRIPTION</h2>
        <p><strong>Date:</strong> {date.today().strftime('%d.%m.%Y')} | <strong>Valid Until:</strong> {(date.today() + timedelta(days=365)).strftime('%d.%m.%Y')}</p>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 20px;">
        <div>
            <strong>Patient:</strong> {p['first_name']} {p['last_name']}<br>
            <strong>ID:</strong> {p['patient_id']}<br>
            <strong>DOB:</strong> {p['date_of_birth']}<br>
            <strong>Gender:</strong> {p['gender']}
        </div>
        <div>
            <strong>Clinician:</strong> {st.session_state.username}<br>
            <strong>License:</strong> Professional Optometrist<br>
            <strong>Prescription Type:</strong> {prescription_type}<br>
            <strong>PD:</strong> {pd_value} mm
        </div>
    </div>

    <div class="prescription-grid">
        <div class="prescription-card">
            <div class="prescription-title">RIGHT EYE (OD)</div>
            <div style="text-align: center; font-size: 18px; font-weight: bold; margin: 10px 0;">
                {ref.get('final_prescribed_od_sphere', '')} {ref.get('final_prescribed_od_cylinder', '')} x {ref.get('final_prescribed_od_axis', '')}
            </div>
            <div class="parameters">
                <div class="parameter"><strong>Sphere:</strong> {ref.get('final_prescribed_od_sphere', '')}</div>
                <div class="parameter"><strong>Cylinder:</strong> {ref.get('final_prescribed_od_cylinder', '')}</div>
                <div class="parameter"><strong>Axis:</strong> {ref.get('final_prescribed_od_axis', '')}°</div>
                <div class="parameter"><strong>ADD:</strong> {ref.get('final_add_od', 'N/A')}</div>
                <div class="parameter"><strong>VA:</strong> {ref.get('final_prescribed_binocular_va', 'N/A')}</div>
            </div>
        </div>

        <div class="prescription-card">
            <div class="prescription-title">LEFT EYE (OS)</div>
            <div style="text-align: center; font-size: 18px; font-weight: bold; margin: 10px 0;">
                {ref.get('final_prescribed_os_sphere', '')} {ref.get('final_prescribed_os_cylinder', '')} x {ref.get('final_prescribed_os_axis', '')}
            </div>
            <div class="parameters">
                <div class="parameter"><strong>Sphere:</strong> {ref.get('final_prescribed_os_sphere', '')}</div>
                <div class="parameter"><strong>Cylinder:</strong> {ref.get('final_prescribed_os_cylinder', '')}</div>
                <div class="parameter"><strong>Axis:</strong> {ref.get('final_prescribed_os_axis', '')}°</div>
                <div class="parameter"><strong>ADD:</strong> {ref.get('final_add_os', 'N/A')}</div>
                <div class="parameter"><strong>VA:</strong> {ref.get('final_prescribed_binocular_va', 'N/A')}</div>
            </div>
        </div>
    </div>

    <div class="axis-display">
        <h3 style="text-align: center; color: #1e3c72;">Axis Visualization - Tabo Scheme</h3>
        {tabo_html}
    </div>

    <div style="margin: 20px 0;">
        <strong>Lens Specifications:</strong><br>
        Material: {lens_material} | Coating: {', '.join(lens_coating) if lens_coating else 'None'}<br>
        Frame: {frame_type} | Type: {prescription_type}
    </div>

    {f"<div style='margin: 15px 0; padding: 10px; background: #fff3cd; border-radius: 5px;'><strong>Special Instructions:</strong> {special_instructions}</div>" if special_instructions else ""}

    <div class="clinic-info">
        <strong>For Optical Dispensing:</strong><br>
        This prescription is valid for optical dispensing. Patient should return for follow-up in 12 months or sooner if vision changes occur.
    </div>

    <div class="signature">
        <p><strong>Optometrist's Signature:</strong></p>
        <br><br>
        <p>_________________________________________</p>
        <p><strong>{st.session_state.username}</strong></p>
        <p>Licensed Optometrist</p>
        <p>OphtalCAM Eye Clinic</p>
        <p>Date: {date.today().strftime('%d %B %Y')}</p>
    </div>

    <div class="no-print" style="margin-top: 30px; padding: 15px; background: #e8f4fd; border-radius: 5px;">
        <p><strong>🖨️ Print Instructions:</strong> Press Ctrl+P to print this prescription</p>
    </div>
</body>
</html>
"""
            
            # Prikaži i omogući download
            st.markdown("### 📄 Prescription Report Preview")
            st.components.v1.html(html_content, height=1000, scrolling=True)
            
            st.download_button(
                label="📥 Download Prescription Report",
                data=html_content,
                file_name=f"prescription_{p['patient_id']}_{date.today().strftime('%Y%m%d')}.html",
                mime="text/html",
                use_container_width=True
            )
            
            st.success("✅ Professional prescription report generated! Perfect for optical dispensing.")
    
    except Exception as e:
        st.error(f"Error generating prescription report: {str(e)}")
# -----------------------
# OTHER MODULES (Patient Registration, Search, etc.)
# -----------------------
def patient_registration():
    st.markdown("<h2 class='main-header'>New Patient Registration</h2>", unsafe_allow_html=True)
    with st.form("reg_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            patient_id = st.text_input("Patient ID (optional)", 
                                     placeholder="Leave blank for auto-generation", key="pat_id")
            first_name = st.text_input("First Name*", placeholder="Given name", key="first_name")
            last_name = st.text_input("Last Name*", placeholder="Family name", key="last_name")
            date_of_birth = st.date_input("Date of Birth*", 
                                        value=date(1990, 1, 1),
                                        min_value=date(1900, 1, 1),
                                        max_value=date.today(),
                                        format="DD.MM.YYYY", key="dob")
            gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"], key="gender")
            
        with col2:
            phone = st.text_input("Phone", placeholder="+1234567890", key="phone")
            email = st.text_input("Email", placeholder="patient@example.com", key="email")
            address = st.text_area("Address", height=60, placeholder="Full address", key="address")
            id_number = st.text_input("ID / Passport Number", placeholder="National ID or passport", key="id_number")
        
        with st.expander("Emergency Contact & Insurance"):
            emergency_contact = st.text_input("Emergency Contact", 
                                           placeholder="Name and phone number", key="emergency_contact")
            insurance_info = st.text_input("Insurance Information", 
                                         placeholder="Insurance provider and number", key="insurance_info")
        
        submit_reg = st.form_submit_button("Register New Patient", use_container_width=True)
        
        if submit_reg:
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
                                   placeholder="Enter patient ID, name, phone, or ID number...", key="search_query")
    with col_search2:
        search_type = st.selectbox("Search by", 
                                 ["All Fields", "Patient ID", "Name", "Phone", "ID Number"], key="search_type")
    
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
                            if st.button("Begin Exam", key=f"exam_{row['id']}"):
                                st.session_state.selected_patient = row['patient_id']
                                st.session_state.menu = "Examination Protocol"
                                st.session_state.exam_step = "medical_history"
                                st.rerun()
                                
                        with col_act2:
                            if st.button("View History", key=f"history_{row['id']}"):
                                st.session_state.selected_patient = row['patient_id']
                                st.info(f"Showing history for {row['first_name']} {row['last_name']}")
                                
                        with col_act3:
                            if st.button("Contact Lenses", key=f"cl_{row['id']}"):
                                st.session_state.selected_patient = row['patient_id']
                                st.session_state.menu = "Contact Lenses"
                                st.rerun()
                                
                        with col_act4:
                            if st.button("Schedule", key=f"schedule_{row['id']}"):
                                st.session_state.selected_patient = row['patient_id']
                                st.session_state.menu = "Schedule Appointment"
                                st.rerun()
                                
        except Exception as e:
            st.error(f"Search error: {str(e)}")

# -----------------------
# USER MANAGEMENT WITH FIXED LICENSE EXPIRY
# -----------------------
def user_management():
    """Admin function to manage users and licenses"""
    if st.session_state.role != "admin":
        st.error("Access denied. Admin privileges required.")
        return
        
    st.markdown("<h2 class='main-header'>User Management & License Control</h2>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["User Management", "Appointment Schedule", "Patient Groups"])
    
    with tab1:
        st.markdown("#### Add New User")
        with st.form("add_user_form"):
            col_user1, col_user2 = st.columns(2)
            with col_user1:
                new_username = st.text_input("Username", key="new_username")
                new_password = st.text_input("Password", type="password", key="new_password")
            with col_user2:
                new_role = st.selectbox("Role", ["admin", "clinician", "assistant"], key="new_role")
                license_expiry = st.date_input("License Expiry", value=date.today() + timedelta(days=365), key="license_expiry")
            
            submit_user = st.form_submit_button("Add User", use_container_width=True)
            
            if submit_user:
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
            # FIXED: Koristimo ispravan SQL upit sa postojećim stupcima
            users_df = pd.read_sql("SELECT id, username, role, license_expiry FROM users ORDER BY username", conn)
            if not users_df.empty:
                for _, user in users_df.iterrows():
                    col_user, col_role, col_license, col_action = st.columns([2, 1, 1, 1])
                    with col_user:
                        st.write(user['username'])
                    with col_role:
                        st.write(user['role'])
                    with col_license:
                        if user['license_expiry']:
                            expiry_date = pd.to_datetime(user['license_expiry']).date()
                            expiry_color = "🟢" if expiry_date > date.today() else "🔴"
                            st.write(f"{expiry_color} {user['license_expiry']}")
                        else:
                            st.write("No expiry")
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
    
    with tab2:
        st.markdown("#### Appointment Schedule Settings")
        
        # Define working hours for each day
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for day_idx, day_name in enumerate(days):
            with st.expander(f"{day_name} Schedule"):
                col_day1, col_day2, col_day3 = st.columns(3)
                
                with col_day1:
                    start_time = st.time_input(f"{day_name} Start", value=datetime.strptime("08:00", "%H:%M").time(), key=f"start_{day_idx}")
                with col_day2:
                    end_time = st.time_input(f"{day_name} End", value=datetime.strptime("17:00", "%H:%M").time(), key=f"end_{day_idx}")
                with col_day3:
                    duration = st.number_input(f"{day_name} Duration (min)", min_value=15, max_value=60, value=30, step=15, key=f"dur_{day_idx}")
                    max_appts = st.number_input(f"{day_name} Max Appts", min_value=1, max_value=50, value=10, key=f"max_{day_idx}")
                    is_active = st.checkbox(f"Active on {day_name}", value=day_idx < 5, key=f"active_{day_idx}")
                
                if st.button(f"Save {day_name} Schedule", key=f"save_{day_idx}"):
                    try:
                        c = conn.cursor()
                        # Remove existing schedule for this day
                        c.execute("DELETE FROM appointment_schedule WHERE day_of_week = ?", (day_idx,))
                        # Insert new schedule
                        c.execute('''
                            INSERT INTO appointment_schedule 
                            (day_of_week, start_time, end_time, appointment_duration, max_appointments, is_active)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (day_idx, start_time, end_time, duration, max_appts, is_active))
                        conn.commit()
                        st.success(f"{day_name} schedule saved!")
                    except Exception as e:
                        st.error(f"Error saving schedule: {str(e)}")
        
        # OphtalCAM Device Connect button
        st.markdown("#### OphtalCAM Device Integration")
        if st.button("Connect OphtalCAM Device", use_container_width=True, key="connect_ophtalcam"):
            st.info("OphtalCAM device connection would be implemented here")
            # This would integrate with actual OphtalCAM hardware
    
    with tab3:
        st.markdown("#### Patient Groups Management")
        
        # Create new group
        col_group1, col_group2 = st.columns(2)
        with col_group1:
            new_group_name = st.text_input("New Group Name", placeholder="e.g., Myopia Control", key="new_group_name")
        with col_group2:
            new_group_desc = st.text_input("Group Description", placeholder="e.g., Patients undergoing myopia control treatment", key="new_group_desc")
        
        if st.button("Create New Group", use_container_width=True, key="create_group"):
            if new_group_name:
                try:
                    c = conn.cursor()
                    c.execute("INSERT INTO patient_groups (group_name, description) VALUES (?, ?)", 
                             (new_group_name, new_group_desc))
                    conn.commit()
                    st.success(f"Group '{new_group_name}' created successfully!")
                except sqlite3.IntegrityError:
                    st.error("Group name already exists.")
                except Exception as e:
                    st.error(f"Error creating group: {str(e)}")
            else:
                st.error("Please enter a group name.")
        
        # Display existing groups
        st.markdown("#### Existing Patient Groups")
        try:
            groups_df = pd.read_sql("SELECT * FROM patient_groups ORDER BY group_name", conn)
            if not groups_df.empty:
                for _, group in groups_df.iterrows():
                    col_grp1, col_grp2, col_grp3 = st.columns([3, 2, 1])
                    with col_grp1:
                        st.write(f"**{group['group_name']}**")
                    with col_grp2:
                        st.write(group['description'])
                    with col_grp3:
                        if st.button("Delete", key=f"del_grp_{group['id']}"):
                            c = conn.cursor()
                            c.execute("DELETE FROM patient_groups WHERE id = ?", (group['id'],))
                            conn.commit()
                            st.success(f"Group '{group['group_name']}' deleted.")
                            st.rerun()
            else:
                st.info("No patient groups found.")
        except Exception as e:
            st.error(f"Error loading groups: {str(e)}")

# -----------------------
# MODERN TOP NAVIGATION
# -----------------------
def main_navigation():
    # Top navigation bar - Examination Protocol maknut
    col_nav1, col_nav2, col_nav3, col_nav4, col_nav5, col_nav6 = st.columns(6)
    
    nav_options = {
        "Dashboard": col_nav1,
        "Patient Registration": col_nav2, 
        "Patient Search": col_nav3,
        "Contact Lenses": col_nav4,
        "Clinical Analytics": col_nav5,
        "System Settings": col_nav6
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
        elif st.session_state.menu == "Schedule Appointment":
            schedule_appointment()
        elif st.session_state.menu == "Patient History":
            view_patient_history()
        elif st.session_state.menu == "Clinical Analytics":
            clinical_analytics()
        elif st.session_state.menu == "System Settings" and st.session_state.role == "admin":
            user_management()
        else:
            st.info("This module is under development.")

def login_page():
    st.markdown("<h2 style='text-align:center;'>OphtalCAM Clinical Management System</h2>", unsafe_allow_html=True)
    
    # Professional login interface
    col_logo, col_form = st.columns([1, 2])
    
    with col_logo:
        # POVEĆAN LOGO - duplo veći (width=400 umjesto 200)
        st.image("https://i.postimg.cc/PrRFzQLv/Logo-Transparency-01.png", width=400)
        # Uklonjen dupli naslov "OPHTALCAM Clinical Management System"
    
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
    if 'selected_calendar_date' not in st.session_state:
        st.session_state.selected_calendar_date = None

    if not st.session_state.logged_in:
        login_page()
    else:
        # Professional header s PhantasMED logom
        col_header1, col_header2, col_header3 = st.columns([2, 1, 1])
        with col_header1:
            st.image("https://i.postimg.cc/qq656tks/Phantasmed-logo.png", width=250)
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