# app.py - OphtalCAM EMR (updated full)
import streamlit as st
import sqlite3
import pandas as pd
import datetime
import hashlib
from datetime import datetime, timedelta
import calendar
import io
import os
import json

# Page configuration
st.set_page_config(
    page_title="OphtalCAM EMR",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------
# Database setup + auto-migration
# ---------------------
@st.cache_resource
def init_db():
    conn = sqlite3.connect('ophtalcam.db', check_same_thread=False)
    c = conn.cursor()

    # USERS
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
        # --- AUTO-MIGRATION for functional_tests ---
    try:
        c.execute("PRAGMA table_info(functional_tests)")
        existing_cols = [col[1] for col in c.fetchall()]
        new_cols = {
            "motility": "TEXT",
            "hirschberg": "TEXT",
            "cover_test_distance": "TEXT",
            "cover_test_near": "TEXT",
            "pupils": "TEXT",
            "confrontation_fields": "TEXT",
            "other_notes": "TEXT"
        }
        for col, coltype in new_cols.items():
            if col not in existing_cols:
                try:
                    c.execute(f"ALTER TABLE functional_tests ADD COLUMN {col} {coltype}")
                    print(f"✅ Added missing column in functional_tests: {col}")
                except Exception as e:
                    print(f"⚠ Could not add column {col}: {e}")
    except Exception as e:
        print(f"⚠ Migration check failed for functional_tests: {e}")

    # PATIENTS - create base schema (include optional columns) then auto-migrate missing
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

        # Auto-migrate refraction_exams missing columns
    try:
        c.execute("PRAGMA table_info(refraction_exams)")
        existing = [col[1] for col in c.fetchall()]

        new_cols = {
            # Habitual
            "habitual_type": "TEXT",
            "habitual_od_va": "TEXT",
            "habitual_os_va": "TEXT",
            "habitual_binocular_va": "TEXT",
            "habitual_pd": "TEXT",
            "habitual_notes": "TEXT",
            "vision_notes": "TEXT",

            # Objective
            "objective_method": "TEXT",
            "objective_time": "TEXT",
            "autorefractor_od_sphere": "REAL",
            "autorefractor_od_cylinder": "REAL",
            "autorefractor_od_axis": "INTEGER",
            "autorefractor_os_sphere": "REAL",
            "autorefractor_os_cylinder": "REAL",
            "autorefractor_os_axis": "INTEGER",

            # Cycloplegic & Subjective
            "cycloplegic_used": "BOOLEAN",
            "cycloplegic_agent": "TEXT",
            "cycloplegic_lot": "TEXT",
            "cycloplegic_expiry": "DATE",
            "cycloplegic_drops": "INTEGER",
            "subjective_method": "TEXT",
            "subjective_od_sphere": "REAL",
            "subjective_od_cylinder": "REAL",
            "subjective_od_axis": "INTEGER",
            "subjective_os_sphere": "REAL",
            "subjective_os_cylinder": "REAL",
            "subjective_os_axis": "INTEGER",
            "subjective_notes": "TEXT",

            # Binocular & Final
            "binocular_balance": "TEXT",
            "stereopsis": "TEXT",
            "near_point_convergence_break": "TEXT",
            "near_point_convergence_recovery": "TEXT",
            "final_prescribed_od_sphere": "REAL",
            "final_prescribed_od_cylinder": "REAL",
            "final_prescribed_od_axis": "INTEGER",
            "final_prescribed_os_sphere": "REAL",
            "final_prescribed_os_cylinder": "REAL",
            "final_prescribed_os_axis": "INTEGER",
            "final_prescribed_binocular_va": "TEXT",
            "bvp": "TEXT",
            "pinhole": "TEXT",
            "prescription_notes": "TEXT",

            # Other
            "binocular_tests": "TEXT",
            "functional_tests": "TEXT",
            "accommodation_tests": "TEXT",
            "uploaded_files": "TEXT"
        }

        for col, ctype in new_cols.items():
            if col not in existing:
                try:
                    c.execute(f"ALTER TABLE refraction_exams ADD COLUMN {col} {ctype}")
                    print(f"✅ Added missing column: {col}")
                except Exception as e:
                    print(f"⚠ Could not add column {col}: {e}")

    except Exception as e:
        print(f"⚠ Migration error for refraction_exams: {e}")


    # MEDICAL HISTORY
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
    # Auto-migrate medical_history missing columns
    try:
        c.execute("PRAGMA table_info(medical_history)")
        cols = [col[1] for col in c.fetchall()]
        if "uploaded_reports" not in cols:
            c.execute("ALTER TABLE medical_history ADD COLUMN uploaded_reports TEXT")
    except Exception:
        pass

    # REFRACTION EXAMS - expanded
    c.execute('''
        CREATE TABLE IF NOT EXISTS refraction_exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            exam_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            -- Habitual
            habitual_type TEXT,
            habitual_od_va TEXT,
            habitual_os_va TEXT,
            habitual_binocular_va TEXT,
            habitual_pd TEXT,
            habitual_notes TEXT,

            -- Uncorrected vision
            uncorrected_od_va TEXT,
            uncorrected_os_va TEXT,
            uncorrected_binocular_va TEXT,

            -- Objective
            objective_method TEXT,
            objective_time TEXT,
            autorefractor_od_sphere REAL,
            autorefractor_od_cylinder REAL,
            autorefractor_od_axis INTEGER,
            autorefractor_os_sphere REAL,
            autorefractor_os_cylinder REAL,
            autorefractor_os_axis INTEGER,

            -- Cycloplegic
            cycloplegic_used BOOLEAN,
            cycloplegic_agent TEXT,
            cycloplegic_lot TEXT,
            cycloplegic_expiry DATE,
            cycloplegic_drops INTEGER,
            cycloplegic_objective_od TEXT,
            cycloplegic_objective_os TEXT,

            -- Subjective (monocular)
            subjective_method TEXT,
            subjective_od_sphere REAL,
            subjective_od_cylinder REAL,
            subjective_od_axis INTEGER,
            subjective_os_sphere REAL,
            subjective_os_cylinder REAL,
            subjective_os_axis INTEGER,
            subjective_notes TEXT,

            -- Binocular & final prescription
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
            bvp TEXT,
            pinhole TEXT,
            prescription_notes TEXT,

            -- Additional
            binocular_tests TEXT,
            functional_tests TEXT,
            accommodation_tests TEXT,
            uploaded_files TEXT,

            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')

    # Auto-migrate refraction_exams missing columns
    try:
        c.execute("PRAGMA table_info(refraction_exams)")
        existing = [col[1] for col in c.fetchall()]
        new_cols = {
            "habitual_type": "TEXT",
            "habitual_pd": "TEXT",
            "objective_method": "TEXT",
            "objective_time": "TEXT",
            "cycloplegic_used": "BOOLEAN",
            "cycloplegic_agent": "TEXT",
            "cycloplegic_lot": "TEXT",
            "cycloplegic_expiry": "DATE",
            "cycloplegic_drops": "INTEGER",
            "binocular_balance": "TEXT",
            "stereopsis": "TEXT",
            "near_point_convergence_break": "TEXT",
            "near_point_convergence_recovery": "TEXT",
            "final_prescribed_binocular_va": "TEXT",
            "bvp": "TEXT",
            "pinhole": "TEXT",
            "prescription_notes": "TEXT",
            "uploaded_files": "TEXT"
        }
        for col, ctype in new_cols.items():
            if col not in existing:
                try:
                    c.execute(f"ALTER TABLE refraction_exams ADD COLUMN {col} {ctype}")
                except Exception:
                    pass
    except Exception:
        pass

    # FUNCTIONAL TESTS
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
            confrontation_fields TEXT,
            other_notes TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')

    # ANTERIOR SEGMENT
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
            uploaded_files TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')
        # --- AUTO-MIGRATION for anterior_segment_exams ---
    try:
        c.execute("PRAGMA table_info(anterior_segment_exams)")
        existing_cols = [col[1] for col in c.fetchall()]

        new_cols = {
            "biomicroscopy_od": "TEXT",
            "biomicroscopy_os": "TEXT",
            "biomicroscopy_notes": "TEXT",
            "anterior_chamber_depth_od": "TEXT",
            "anterior_chamber_depth_os": "TEXT",
            "anterior_chamber_volume_od": "TEXT",
            "anterior_chamber_volume_os": "TEXT",
            "iridocorneal_angle_od": "TEXT",
            "iridocorneal_angle_os": "TEXT",
            "pachymetry_od": "REAL",
            "pachymetry_os": "REAL",
            "tonometry_type": "TEXT",
            "tonometry_time": "TEXT",
            "tonometry_compensation": "TEXT",
            "tonometry_od": "TEXT",
            "tonometry_os": "TEXT",
            "aberometry_notes": "TEXT",
            "corneal_topography_notes": "TEXT",
            "anterior_segment_notes": "TEXT",
            "uploaded_files": "TEXT"
        }

        for col, col_type in new_cols.items():
            if col not in existing_cols:
                try:
                    c.execute(f"ALTER TABLE anterior_segment_exams ADD COLUMN {col} {col_type}")
                    print(f"✅ Added missing column in anterior_segment_exams: {col}")
                except Exception as e:
                    print(f"⚠ Could not add column {col}: {e}")

    except Exception as e:
        print(f"⚠ Migration check failed for anterior_segment_exams: {e}")

    # POSTERIOR SEGMENT
    c.execute('''
        CREATE TABLE IF NOT EXISTS posterior_segment_exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            exam_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fundus_exam_type TEXT,
            fundus_od TEXT,
            fundus_os TEXT,
            fundus_notes TEXT,
            pupillography_results TEXT,
            pupillography_notes TEXT,
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
        # --- AUTO-MIGRATION for posterior_segment_exams ---
    try:
        c.execute("PRAGMA table_info(posterior_segment_exams)")
        existing_cols = [col[1] for col in c.fetchall()]

        new_cols = {
            "fundus_exam_type": "TEXT",
            "fundus_od": "TEXT",
            "fundus_os": "TEXT",
            "fundus_notes": "TEXT",
            "pupillography_results": "TEXT",
            "pupillography_notes": "TEXT",
            "oct_macula_od": "TEXT",
            "oct_macula_os": "TEXT",
            "oct_rnfl_od": "TEXT",
            "oct_rnfl_os": "TEXT",
            "oct_notes": "TEXT",
            "posterior_segment_notes": "TEXT",
            "uploaded_files": "TEXT"
        }

        for col, col_type in new_cols.items():
            if col not in existing_cols:
                try:
                    c.execute(f"ALTER TABLE posterior_segment_exams ADD COLUMN {col} {col_type}")
                    print(f"✅ Added missing column in posterior_segment_exams: {col}")
                except Exception as e:
                    print(f"⚠ Could not add column {col}: {e}")

    except Exception as e:
        print(f"⚠ Migration check failed for posterior_segment_exams: {e}")

    # CONTACT LENSES
    c.execute('''
        CREATE TABLE IF NOT EXISTS contact_lens_prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            prescription_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            lens_type TEXT NOT NULL,
            soft_brand TEXT,
            soft_base_curve REAL,
            soft_diameter REAL,
            soft_power_od REAL,
            soft_power_os REAL,
            rgp_design TEXT,
            rgp_material TEXT,
            rgp_base_curve REAL,
            rgp_diameter REAL,
            scleral_design TEXT,
            scleral_material TEXT,
            scleral_diameter REAL,
            wearing_schedule TEXT,
            care_solution TEXT,
            follow_up_date DATE,
            fitting_notes TEXT,
            uploaded_files TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')

    # PATIENT GROUPS
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

    # APPOINTMENTS
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

    # default admin
    try:
        admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                  ("admin", admin_hash, "admin"))
    except Exception:
        pass

    # default groups
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
    for g, d in default_groups:
        try:
            c.execute("INSERT OR IGNORE INTO patient_groups (group_name, description) VALUES (?, ?)", (g, d))
        except Exception:
            pass

    conn.commit()
    return conn

# initialize db
conn = init_db()

# ---------------------
# Utilities
# ---------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashv):
    return hash_password(password) == hashv

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
    except Exception:
        return pd.DataFrame()

def get_patient_stats():
    conn = init_db()
    try:
        total_patients = pd.read_sql("SELECT COUNT(*) as count FROM patients", conn).iloc[0]['count']
        today = datetime.now().date()
        today_exams = pd.read_sql('SELECT COUNT(*) as count FROM appointments WHERE DATE(appointment_date) = ?', conn, params=(today,)).iloc[0]['count']
        total_cl = pd.read_sql("SELECT COUNT(*) as count FROM contact_lens_prescriptions", conn).iloc[0]['count']
        return total_patients, today_exams, total_cl
    except Exception:
        return 0, 0, 0

# CSS
def load_css():
    st.markdown("""
    <style>
    body { font-family: Arial, sans-serif; }
    .metric-card { background: linear-gradient(135deg,#1e3c72 0%,#2a5298 100%); color: white; padding: 1.2rem; border-radius: 10px; text-align:center; margin:0.4rem; }
    .metric-value { font-size:1.6rem; font-weight:bold; }
    .appointment-card { background-color:#f8f9fa; padding:0.9rem; border-radius:8px; margin:0.4rem 0; border-left:4px solid #1e3c72; }
    .protocol-section { background-color:#ffffff; padding:1rem; border-radius:8px; margin-bottom:0.8rem; border:1px solid #e0e0e0; border-left:4px solid #1e3c72; }
    .exam-step { background-color:#e3f2fd; padding:0.4rem 0.8rem; border-radius:15px; margin:0.15rem; display:inline-block; font-size:0.85rem;}
    .exam-step.active { background-color:#1e3c72; color:white; font-weight:bold; }
    </style>
    """, unsafe_allow_html=True)

# ---------------------
# DASHBOARD
# ---------------------
def show_dashboard():
    st.markdown("<h1 style='text-align:center;'>OphtalCAM Clinical Dashboard</h1>", unsafe_allow_html=True)

    col_filter = st.columns([2,1,1,1])
    with col_filter[0]:
        view_option = st.selectbox("Time View", ["Today", "This Week", "This Month"], key="view_filter")
    with col_filter[3]:
        if st.button("+ New Appointment", use_container_width=True):
            st.session_state.menu = "Schedule Appointment"
            st.rerun()

    total_patients, today_exams, total_cl = get_patient_stats()
    col_metrics = st.columns(3)
    with col_metrics[0]:
        st.markdown(f"<div class='metric-card'><div class='metric-value'>{total_patients}</div><div>Registered Patients</div></div>", unsafe_allow_html=True)
    with col_metrics[1]:
        st.markdown(f"<div class='metric-card'><div class='metric-value'>{today_exams}</div><div>Scheduled Examinations (today)</div></div>", unsafe_allow_html=True)
    with col_metrics[2]:
        st.markdown(f"<div class='metric-card'><div class='metric-value'>{total_cl}</div><div>Contact Lens Patients</div></div>", unsafe_allow_html=True)

    col_main = st.columns([2,1])
    with col_main[0]:
        st.subheader("Today's Clinical Schedule")
        appointments = get_todays_appointments()
        if not appointments.empty:
            for _, apt in appointments.iterrows():
                apt_time = pd.to_datetime(apt['appointment_date']).strftime('%H:%M')
                with st.container():
                    st.markdown(f"<div class='appointment-card'><strong>{apt_time}</strong> - {apt['first_name']} {apt['last_name']} ({apt['patient_id']})<br><small>Type: {apt['appointment_type']} | Status: {apt['status']}</small></div>", unsafe_allow_html=True)
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
                            st.session_state.menu = "Patient Search"
                            st.rerun()
        else:
            st.info("No appointments scheduled for today.")

    with col_main[1]:
        st.subheader("Clinical Calendar")
        today = datetime.now()
        cal = calendar.monthcalendar(today.year, today.month)
        st.write(f"**{today.strftime('%B %Y')}**")
        days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        cols = st.columns(7)
        for i,d in enumerate(days):
            cols[i].write(f"**{d}**")
        for week in cal:
            cols = st.columns(7)
            for i,day in enumerate(week):
                if day == 0:
                    cols[i].write("")
                else:
                    if day == today.day:
                        cols[i].markdown(f"<div style='background-color:#1e3c72;color:white;padding:5px;border-radius:50%;text-align:center;'><strong>{day}</strong></div>", unsafe_allow_html=True)
                    else:
                        cols[i].write(str(day))
        st.markdown("---")
        st.subheader("Clinical Actions")
        if st.button("New Patient Registration", use_container_width=True):
            st.session_state.menu = "Patient Registration"
            st.rerun()
        if st.button("Patient Search & Records", use_container_width=True):
            st.session_state.menu = "Patient Search"
            st.rerun()
        if st.button("Clinical Analytics", use_container_width=True):
            st.session_state.menu = "Clinical Analytics"
            st.rerun()

# ---------------------
# MEDICAL HISTORY
# ---------------------
def medical_history():
    st.subheader("Comprehensive Medical History & Anamnesis")
    if 'selected_patient' not in st.session_state or not st.session_state.selected_patient:
        st.error("No patient selected. Please select a patient from the Dashboard.")
        return
    patient_id = st.session_state.selected_patient
    try:
        patient_info = pd.read_sql("SELECT * FROM patients WHERE patient_id = ?", conn, params=(patient_id,)).iloc[0]
        st.markdown(f"### Patient: {patient_info['first_name']} {patient_info['last_name']} (ID: {patient_info['patient_id']})")
    except Exception:
        st.error("Patient not found in database.")
        return

    with st.form("medical_history_form"):
        st.markdown("#### General Health")
        col1, col2 = st.columns(2)
        with col1:
            general_health = st.text_area("General Health Status", height=100)
            current_medications = st.text_area("Current Medications", height=100)
            allergies = st.text_area("Allergies & Reactions", height=80)
        with col2:
            headaches_history = st.text_area("Headaches & Migraines", height=80)
            family_history = st.text_area("Family Medical History", height=100)
        st.markdown("#### Ocular History")
        col_o1, col_o2 = st.columns(2)
        with col_o1:
            ocular_history = st.text_area("Ocular History & Conditions", height=100)
            previous_surgeries = st.text_area("Previous Ocular Surgeries", height=80)
        with col_o2:
            eye_medications = st.text_area("Ocular Medications", height=80)
            last_eye_exam = st.date_input("Last Comprehensive Eye Examination")
        st.markdown("#### Social & Lifestyle")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            smoking_status = st.selectbox("Smoking Status", ["Non-smoker","Former smoker","Current smoker","Unknown"])
            alcohol_consumption = st.selectbox("Alcohol Consumption", ["None","Occasional","Moderate","Heavy"])
        with col_s2:
            occupation = st.text_input("Occupation")
            hobbies = st.text_area("Hobbies & Activities", height=60)
        previous_reports = st.file_uploader("Upload Previous Medical Reports (pdf, jpg, png, docx)", type=['pdf','jpg','png','docx'], accept_multiple_files=True)
        submit_history = st.form_submit_button("Save Medical History & Continue")
        if submit_history:
            try:
                files_list = []
                if previous_reports:
                    os.makedirs("uploads", exist_ok=True)
                    for f in previous_reports:
                        file_path = os.path.join("uploads", f"{datetime.now().timestamp()}_{f.name}")
                        with open(file_path, "wb") as fp:
                            fp.write(f.getbuffer())
                        files_list.append(file_path)
                c = conn.cursor()
                c.execute('''
                    INSERT INTO medical_history
                    (patient_id, general_health, current_medications, allergies, headaches_history, family_history,
                     ocular_history, previous_surgeries, eye_medications, last_eye_exam, smoking_status, alcohol_consumption,
                     occupation, hobbies, uploaded_reports)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (patient_info['id'], general_health, current_medications, allergies, headaches_history, family_history,
                      ocular_history, previous_surgeries, eye_medications, last_eye_exam, smoking_status, alcohol_consumption,
                      occupation, hobbies, json.dumps(files_list)))
                conn.commit()
                st.success("Medical history saved.")
                st.session_state.exam_step = "refraction"
                st.rerun()
            except Exception as e:
                st.error(f"Database error: {str(e)}")

# ---------------------
# REFRACTION EXAMINATION (modular)
# ---------------------
def refraction_examination():
    st.subheader("Comprehensive Refraction & Vision Examination")
    if 'selected_patient' not in st.session_state or not st.session_state.selected_patient:
        st.error("Please select a patient first.")
        return
    patient_id = st.session_state.selected_patient
    try:
        patient_info = pd.read_sql("SELECT * FROM patients WHERE patient_id = ?", conn, params=(patient_id,)).iloc[0]
        st.markdown(f"### Patient: {patient_info['first_name']} {patient_info['last_name']} (ID: {patient_info['patient_id']})")
    except Exception:
        st.error("Patient not found.")
        return

    if 'refraction' not in st.session_state:
        st.session_state.refraction = {}

    # --- Vision section (Habitual + Uncorrected) ---
    st.markdown("#### 1) Vision Examination — Habitual & Uncorrected")
    with st.form("vision_exam_form"):
        col_h1, col_h2, col_h3 = st.columns([2,2,1])
        with col_h1:
            st.markdown("**Habitual Correction**")
            habitual_type = st.selectbox("Type of Habitual Correction", ["None","Spectacles","Soft Contact Lenses","RGP","Scleral","Ortho-K","Other"], index=0, key="habit_type")
            habitual_od_va = st.text_input("Habitual VA OD", placeholder="20/20")
            habitual_os_va = st.text_input("Habitual VA OS", placeholder="20/20")
            habitual_binocular_va = st.text_input("Habitual Binocular VA", placeholder="20/20")
            habitual_pd = st.text_input("PD (mm)", placeholder="62")
        with col_h2:
            st.markdown("**Uncorrected Vision**")
            uncorrected_od_va = st.text_input("Uncorrected VA OD", placeholder="20/200")
            uncorrected_os_va = st.text_input("Uncorrected VA OS", placeholder="20/200")
            uncorrected_binocular_va = st.text_input("Uncorrected Binocular VA", placeholder="20/200")
        with col_h3:
            vision_notes = st.text_area("Vision notes", height=150)
        save_vision = st.form_submit_button("Save Vision Section")
        if save_vision:
            st.session_state.refraction.update({
                'habitual_type': habitual_type,
                'habitual_od_va': habitual_od_va,
                'habitual_os_va': habitual_os_va,
                'habitual_binocular_va': habitual_binocular_va,
                'habitual_pd': habitual_pd,
                'uncorrected_od_va': uncorrected_od_va,
                'uncorrected_os_va': uncorrected_os_va,
                'uncorrected_binocular_va': uncorrected_binocular_va,
                'vision_notes': vision_notes
            })
            st.success("Vision section saved locally.")
            st.session_state.ref_section = "vision"
            st.rerun()

    st.markdown("---")
    # --- Objective refraction (aligned fields) ---
    st.markdown("#### 2) Objective Refraction (Autorefractor / Retinoscopy)")
    with st.form("objective_form"):
        top_cols = st.columns([2,2,1])
        with top_cols[0]:
            objective_method = st.selectbox("Method", ["Autorefractor","Retinoscopy","Other"], index=0)
        with top_cols[1]:
            objective_time = st.time_input("Time of Measurement", value=datetime.now().time())
        # aligned OD vs OS: show Sph/Cyl/Axis in two columns side-by-side
        col_od, spacer, col_os = st.columns([2,0.2,2])
        with col_od:
            st.markdown("**Right Eye (OD)**")
            autorefractor_od_sphere = st.number_input("Sphere OD", value=0.0, step=0.25, format="%.2f", key="obj_od_sph")
            autorefractor_od_cylinder = st.number_input("Cylinder OD", value=0.0, step=0.25, format="%.2f", key="obj_od_cyl")
            autorefractor_od_axis = st.number_input("Axis OD", min_value=0, max_value=180, value=0, key="obj_od_ax")
        with col_os:
            st.markdown("**Left Eye (OS)**")
            autorefractor_os_sphere = st.number_input("Sphere OS", value=0.0, step=0.25, format="%.2f", key="obj_os_sph")
            autorefractor_os_cylinder = st.number_input("Cylinder OS", value=0.0, step=0.25, format="%.2f", key="obj_os_cyl")
            autorefractor_os_axis = st.number_input("Axis OS", min_value=0, max_value=180, value=0, key="obj_os_ax")
        objective_notes = st.text_area("Objective notes", height=100)
        save_objective = st.form_submit_button("Save Objective Section")
        if save_objective:
            st.session_state.refraction.update({
                'objective_method': objective_method,
                'objective_time': objective_time.strftime("%H:%M"),
                'autorefractor_od_sphere': autorefractor_od_sphere,
                'autorefractor_od_cylinder': autorefractor_od_cylinder,
                'autorefractor_od_axis': autorefractor_od_axis,
                'autorefractor_os_sphere': autorefractor_os_sphere,
                'autorefractor_os_cylinder': autorefractor_os_cylinder,
                'autorefractor_os_axis': autorefractor_os_axis,
                'objective_notes': objective_notes
            })
            st.success("Objective saved locally.")
            st.session_state.ref_section = "objective"
            st.rerun()

    st.markdown("---")
    # --- Cycloplegic & Subjective (aligned) ---
    st.markdown("#### 3) Cycloplegic (if used) & Subjective Monocular Refraction")
    with st.form("subjective_form"):
        col_top = st.columns([2,2])
        with col_top[0]:
            subjective_method = st.selectbox("Subjective method", ["Fogging","With Cycloplegic","Other"])
        with col_top[1]:
            cycloplegic_used = True if subjective_method == "With Cycloplegic" else False

        # Cycloplegic details aligned in smaller input boxes
        if cycloplegic_used:
            cycl_cols = st.columns([1,1,1,1])
            with cycl_cols[0]:
                cycloplegic_agent = st.text_input("Agent", placeholder="Cyclopentolate 1%")
            with cycl_cols[1]:
                cycloplegic_lot = st.text_input("Lot #", placeholder="LOT123")
            with cycl_cols[2]:
                cycloplegic_expiry = st.date_input("Expiry")
            with cycl_cols[3]:
                cycloplegic_drops = st.number_input("Drops", min_value=1, max_value=10, value=1)
        else:
            cycloplegic_agent = ""
            cycloplegic_lot = ""
            cycloplegic_expiry = None
            cycloplegic_drops = None

        # Subjective aligned OD/OS
        col_od2, spacer2, col_os2 = st.columns([2,0.2,2])
        with col_od2:
            st.markdown("**Right Eye (OD) - Subjective**")
            subjective_od_sphere = st.number_input("Subjective Sphere OD", value=0.0, step=0.25, format="%.2f", key="subj_od_sph")
            subjective_od_cylinder = st.number_input("Subjective Cylinder OD", value=0.0, step=0.25, format="%.2f", key="subj_od_cyl")
            subjective_od_axis = st.number_input("Subjective Axis OD", min_value=0, max_value=180, value=0, key="subj_od_ax")
        with col_os2:
            st.markdown("**Left Eye (OS) - Subjective**")
            subjective_os_sphere = st.number_input("Subjective Sphere OS", value=0.0, step=0.25, format="%.2f", key="subj_os_sph")
            subjective_os_cylinder = st.number_input("Subjective Cylinder OS", value=0.0, step=0.25, format="%.2f", key="subj_os_cyl")
            subjective_os_axis = st.number_input("Subjective Axis OS", min_value=0, max_value=180, value=0, key="subj_os_ax")
        subjective_notes = st.text_area("Subjective notes", height=120)
        save_subjective = st.form_submit_button("Save Subjective Section")
        if save_subjective:
            st.session_state.refraction.update({
                'subjective_method': subjective_method,
                'cycloplegic_used': cycloplegic_used,
                'cycloplegic_agent': cycloplegic_agent,
                'cycloplegic_lot': cycloplegic_lot,
                'cycloplegic_expiry': cycloplegic_expiry,
                'cycloplegic_drops': cycloplegic_drops,
                'subjective_od_sphere': subjective_od_sphere,
                'subjective_od_cylinder': subjective_od_cylinder,
                'subjective_od_axis': subjective_od_axis,
                'subjective_os_sphere': subjective_os_sphere,
                'subjective_os_cylinder': subjective_os_cylinder,
                'subjective_os_axis': subjective_os_axis,
                'subjective_notes': subjective_notes
            })
            st.success("Subjective saved locally.")
            st.session_state.ref_section = "subjective"
            st.rerun()

    st.markdown("---")
    # --- Binocular & Final Prescription (Finalize) ---
    st.markdown("#### 4) Binocular Tests & Final Prescription")
    with st.form("binocular_form"):
        col_b1, col_b2 = st.columns([2,2])
        with col_b1:
            binocular_balance = st.selectbox("Binocular Balance", ["Balanced","OD dominant","OS dominant","Unbalanced"])
            stereopsis = st.text_input("Stereoacuity", placeholder="e.g., 40 arc sec")
            npc_break = st.text_input("NPC Break", placeholder="6 cm")
            npc_recovery = st.text_input("NPC Recovery", placeholder="8 cm")
            binocular_tests = st.text_area("Binocular tests (phoria, cover test, Worth, etc.)", height=120)
        with col_b2:
            st.markdown("**Final Prescription**")
            final_od_sph = st.number_input("Final Sphere OD", value=0.0, step=0.25, format="%.2f", key="final_od_sph")
            final_od_cyl = st.number_input("Final Cylinder OD", value=0.0, step=0.25, format="%.2f", key="final_od_cyl")
            final_od_axis = st.number_input("Final Axis OD", min_value=0, max_value=180, value=0, key="final_od_ax")
            final_os_sph = st.number_input("Final Sphere OS", value=0.0, step=0.25, format="%.2f", key="final_os_sph")
            final_os_cyl = st.number_input("Final Cylinder OS", value=0.0, step=0.25, format="%.2f", key="final_os_cyl")
            final_os_axis = st.number_input("Final Axis OS", min_value=0, max_value=180, value=0, key="final_os_ax")
            final_bin_va = st.text_input("Final Binocular VA", placeholder="20/20")
            bvp = st.text_input("BVP")
            pinhole = st.text_input("Pinhole VA")
            prescription_notes = st.text_area("Prescription notes / rationale", height=120)

        save_binocular = st.form_submit_button("Save & Finalize Refraction")
        if save_binocular:
            # collect session data and insert into DB
            try:
                p = pd.read_sql("SELECT id FROM patients WHERE patient_id = ?", conn, params=(patient_id,)).iloc[0]
                pid = p['id']
                uploaded_files = st.session_state.refraction.get('uploaded_files', [])
                c = conn.cursor()
                c.execute('''
                    INSERT INTO refraction_exams
                    (patient_id, habitual_type, habitual_od_va, habitual_os_va, habitual_binocular_va, habitual_pd, habitual_notes,
                     uncorrected_od_va, uncorrected_os_va, uncorrected_binocular_va,
                     objective_method, objective_time,
                     autorefractor_od_sphere, autorefractor_od_cylinder, autorefractor_od_axis,
                     autorefractor_os_sphere, autorefractor_os_cylinder, autorefractor_os_axis,
                     cycloplegic_used, cycloplegic_agent, cycloplegic_lot, cycloplegic_expiry, cycloplegic_drops,
                     subjective_method, subjective_od_sphere, subjective_od_cylinder, subjective_od_axis,
                     subjective_os_sphere, subjective_os_cylinder, subjective_os_axis, subjective_notes,
                     binocular_balance, stereopsis, near_point_convergence_break, near_point_convergence_recovery,
                     final_prescribed_od_sphere, final_prescribed_od_cylinder, final_prescribed_od_axis,
                     final_prescribed_os_sphere, final_prescribed_os_cylinder, final_prescribed_os_axis,
                     final_prescribed_binocular_va, bvp, pinhole, prescription_notes,
                     binocular_tests, functional_tests, accommodation_tests, uploaded_files)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)

                ''', (
                    pid,
                    st.session_state.refraction.get('habitual_type'),
                    st.session_state.refraction.get('habitual_od_va'),
                    st.session_state.refraction.get('habitual_os_va'),
                    st.session_state.refraction.get('habitual_binocular_va'),
                    st.session_state.refraction.get('habitual_pd'),
                    st.session_state.refraction.get('vision_notes'),
                    st.session_state.refraction.get('uncorrected_od_va'),
                    st.session_state.refraction.get('uncorrected_os_va'),
                    st.session_state.refraction.get('uncorrected_binocular_va'),
                    st.session_state.refraction.get('objective_method'),
                    st.session_state.refraction.get('objective_time'),
                    st.session_state.refraction.get('autorefractor_od_sphere'),
                    st.session_state.refraction.get('autorefractor_od_cylinder'),
                    st.session_state.refraction.get('autorefractor_od_axis'),
                    st.session_state.refraction.get('autorefractor_os_sphere'),
                    st.session_state.refraction.get('autorefractor_os_cylinder'),
                    st.session_state.refraction.get('autorefractor_os_axis'),
                    st.session_state.refraction.get('cycloplegic_used'),
                    st.session_state.refraction.get('cycloplegic_agent'),
                    st.session_state.refraction.get('cycloplegic_lot'),
                    st.session_state.refraction.get('cycloplegic_expiry'),
                    st.session_state.refraction.get('cycloplegic_drops'),
                    st.session_state.refraction.get('subjective_method'),
                    st.session_state.refraction.get('subjective_od_sphere'),
                    st.session_state.refraction.get('subjective_od_cylinder'),
                    st.session_state.refraction.get('subjective_od_axis'),
                    st.session_state.refraction.get('subjective_os_sphere'),
                    st.session_state.refraction.get('subjective_os_cylinder'),
                    st.session_state.refraction.get('subjective_os_axis'),
                    st.session_state.refraction.get('subjective_notes'),
                    binocular_balance,
                    stereopsis,
                    npc_break,
                    npc_recovery,
                    final_od_sph,
                    final_od_cyl,
                    final_od_axis,
                    final_os_sph,
                    final_os_cyl,
                    final_os_axis,
                    final_bin_va,
                    bvp,
                    pinhole,
                    prescription_notes,
                    binocular_tests,
                    st.session_state.refraction.get('functional_tests'),
                    st.session_state.refraction.get('accommodation_tests'),
                    json.dumps(uploaded_files)
                ))
                conn.commit()
                st.success("Refraction saved to database.")
                # clear session and advance
                st.session_state.refraction = {}
                st.session_state.exam_step = "functional_tests"
                st.rerun()
            except Exception as e:
                st.error(f"Database error when saving refraction: {str(e)}")

# ---------------------
# Functional / Anterior / Posterior (simplified but saving)
# ---------------------
def functional_tests():
    st.subheader("Functional Vision Tests")
    if 'selected_patient' not in st.session_state or not st.session_state.selected_patient:
        st.error("No patient selected.")
        return
    patient_id = st.session_state.selected_patient
    with st.form("functional_tests_form"):
        st.markdown("Motility, Hirschberg, NPC, Pupils, Visual Fields")
        col1, col2 = st.columns(2)
        with col1:
            motility = st.text_area("Ocular Motility (notes)", height=120)
            hirschberg = st.text_input("Hirschberg result")
            npc_break = st.text_input("NPC Break")
            npc_recovery = st.text_input("NPC Recovery")
        with col2:
            pupils = st.text_input("Pupils (size/reactivity)")
            rapd = st.selectbox("RAPD", ["None","Present","Unsure"])
            confrontation = st.text_area("Confrontation Visual Field", height=120)
            functional_notes = st.text_area("Functional Notes", height=80)
        save_func = st.form_submit_button("Save Functional Tests")
        if save_func:
            try:
                p = pd.read_sql("SELECT id FROM patients WHERE patient_id = ?", conn, params=(patient_id,)).iloc[0]
                c = conn.cursor()
                c.execute('''
                    INSERT INTO functional_tests (patient_id, motility, hirschberg, cover_test_distance, cover_test_near, pupils, confrontation_fields, other_notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (p['id'], motility, hirschberg, npc_break, npc_recovery, pupils, confrontation, functional_notes))
                conn.commit()
                st.success("Functional tests saved.")
                st.session_state.exam_step = "anterior_segment"
                st.rerun()
            except Exception as e:
                st.error(f"Database error: {str(e)}")

def anterior_segment_examination():
    st.subheader("Anterior Segment Examination & Biomicroscopy")
    if 'selected_patient' not in st.session_state or not st.session_state.selected_patient:
        st.error("No patient selected.")
        return
    patient_id = st.session_state.selected_patient
    with st.form("anterior_form"):
        col1, col2 = st.columns(2)
        with col1:
            biomicroscopy_od = st.text_area("Biomicroscopy OD", height=120)
            biomicroscopy_os = st.text_area("Biomicroscopy OS", height=120)
            biomicroscopy_notes = st.text_area("Biomicroscopy notes", height=80)
        with col2:
            acd_od = st.text_input("AC Depth OD")
            acd_os = st.text_input("AC Depth OS")
            acv_od = st.text_input("AC Volume OD")
            acv_os = st.text_input("AC Volume OS")
            iridocorneal_od = st.text_input("Iridocorneal Angle OD")
            iridocorneal_os = st.text_input("Iridocorneal Angle OS")
        files = st.file_uploader("Upload slit-lamp / pachymetry / topography", type=['pdf','png','jpg','jpeg'], accept_multiple_files=True)
        save_anterior = st.form_submit_button("Save Anterior Segment")
        if save_anterior:
            try:
                p = pd.read_sql("SELECT id FROM patients WHERE patient_id = ?", conn, params=(patient_id,)).iloc[0]
                file_paths = []
                if files:
                    os.makedirs("uploads", exist_ok=True)
                    for f in files:
                        path = os.path.join("uploads", f"{datetime.now().timestamp()}_{f.name}")
                        with open(path, "wb") as fp:
                            fp.write(f.getbuffer())
                        file_paths.append(path)
                c = conn.cursor()
                c.execute('''
                    INSERT INTO anterior_segment_exams (patient_id, biomicroscopy_od, biomicroscopy_os, biomicroscopy_notes,
                        anterior_chamber_depth_od, anterior_chamber_depth_os, anterior_chamber_volume_od, anterior_chamber_volume_os,
                        iridocorneal_angle_od, iridocorneal_angle_os, uploaded_files)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (p['id'], biomicroscopy_od, biomicroscopy_os, biomicroscopy_notes, acd_od, acd_os, acv_od, acv_os, iridocorneal_od, iridocorneal_os, json.dumps(file_paths)))
                conn.commit()
                st.success("Anterior segment saved.")
                st.session_state.exam_step = "posterior_segment"
                st.rerun()
            except Exception as e:
                st.error(f"Database error: {str(e)}")

def posterior_segment_examination():
    st.subheader("Posterior Segment Examination & Imaging")
    if 'selected_patient' not in st.session_state or not st.session_state.selected_patient:
        st.error("No patient selected.")
        return
    patient_id = st.session_state.selected_patient
    with st.form("posterior_form"):
        fundus_type = st.selectbox("Fundus Exam Type", ["Indirect ophthalmoscopy","Fundus camera","Widefield","Other"])
        fundus_od = st.text_area("Fundus OD findings", height=120)
        fundus_os = st.text_area("Fundus OS findings", height=120)
        fundus_notes = st.text_area("Fundus notes", height=80)
        pupillography = st.text_area("Pupillography results", height=80)
        oct_uploads = st.file_uploader("Upload OCT / fundus images", type=['pdf','png','jpg','jpeg'], accept_multiple_files=True)
        save_posterior = st.form_submit_button("Save Posterior Segment")
        if save_posterior:
            try:
                p = pd.read_sql("SELECT id FROM patients WHERE patient_id = ?", conn, params=(patient_id,)).iloc[0]
                file_paths = []
                if oct_uploads:
                    os.makedirs("uploads", exist_ok=True)
                    for f in oct_uploads:
                        path = os.path.join("uploads", f"{datetime.now().timestamp()}_{f.name}")
                        with open(path, "wb") as fp:
                            fp.write(f.getbuffer())
                        file_paths.append(path)
                c = conn.cursor()
                c.execute('''
                    INSERT INTO posterior_segment_exams (patient_id, fundus_exam_type, fundus_od, fundus_os, fundus_notes, pupillography_results, uploaded_files)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (p['id'], fundus_type, fundus_od, fundus_os, fundus_notes, pupillography, json.dumps(file_paths)))
                conn.commit()
                st.success("Posterior segment saved.")
                # finish exam
                st.session_state.exam_step = None
                st.session_state.selected_patient = None
                st.session_state.menu = "Dashboard"
                st.rerun()
            except Exception as e:
                st.error(f"Database error: {str(e)}")

# ---------------------
# PATIENT REGISTRATION
# ---------------------
def patient_registration():
    st.subheader("New Patient Registration")
    with st.form("patient_registration_form"):
        st.markdown("#### Personal Information")
        col1, col2 = st.columns(2)
        with col1:
            patient_id = st.text_input("Patient ID (optional)")
            first_name = st.text_input("First Name*", placeholder="Given name")
            last_name = st.text_input("Last Name*", placeholder="Family name")
            date_of_birth = st.date_input("Date of Birth*", value=datetime.now()-timedelta(days=365*30), max_value=datetime.now())
            gender = st.selectbox("Gender", ["Male","Female","Other","Prefer not to say"])
        with col2:
            phone = st.text_input("Phone")
            email = st.text_input("Email")
            address = st.text_area("Address", height=60)
            id_number = st.text_input("ID / Passport")
        st.markdown("#### Emergency & Insurance")
        col_e = st.columns(2)
        with col_e[0]:
            emergency_contact = st.text_input("Emergency Contact")
        with col_e[1]:
            insurance_info = st.text_input("Insurance Info")
        submit_button = st.form_submit_button("Register New Patient")
        if submit_button:
            if not all([first_name, last_name, date_of_birth]):
                st.error("Please enter First Name, Last Name and Date of Birth.")
            else:
                try:
                    if not patient_id:
                        patient_id = f"PAT{int(datetime.now().timestamp())}"
                    c = conn.cursor()
                    c.execute('''
                        INSERT INTO patients (patient_id, first_name, last_name, date_of_birth, gender, phone, email, address, id_number, emergency_contact, insurance_info)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (patient_id, first_name, last_name, date_of_birth, gender, phone, email, address, id_number, emergency_contact, insurance_info))
                    conn.commit()
                    st.success(f"Patient {first_name} {last_name} registered. ID: {patient_id}")
                except sqlite3.IntegrityError:
                    st.error("Patient ID already exists.")
                except Exception as e:
                    st.error(f"Database error: {str(e)}")

# ---------------------
# PATIENT SEARCH
# ---------------------
def patient_search():
    st.subheader("Patient Search & Records")
    col_search = st.columns([2,1])
    with col_search[0]:
        search_term = st.text_input("Search Patients", placeholder="Patient ID, name, phone or ID#")
    with col_search[1]:
        search_type = st.selectbox("Search By", ["All Fields","Patient ID","Name","Phone"])
    if search_term:
        try:
            if search_type == "All Fields":
                patients = pd.read_sql('''
                    SELECT * FROM patients WHERE patient_id LIKE ? OR first_name LIKE ? OR last_name LIKE ? OR phone LIKE ? OR id_number LIKE ?
                    ORDER BY last_name, first_name
                ''', conn, params=(f'%{search_term}%',f'%{search_term}%',f'%{search_term}%',f'%{search_term}%',f'%{search_term}%'))
            elif search_type == "Patient ID":
                patients = pd.read_sql('SELECT * FROM patients WHERE patient_id LIKE ? ORDER BY patient_id', conn, params=(f'%{search_term}%',))
            elif search_type == "Name":
                patients = pd.read_sql('SELECT * FROM patients WHERE first_name LIKE ? OR last_name LIKE ? ORDER BY last_name, first_name', conn, params=(f'%{search_term}%',f'%{search_term}%'))
            else:
                patients = pd.read_sql('SELECT * FROM patients WHERE phone LIKE ? ORDER BY last_name, first_name', conn, params=(f'%{search_term}%',))
            if not patients.empty:
                st.success(f"Found {len(patients)} patient(s)")
                for _, patient in patients.iterrows():
                    with st.expander(f"{patient['patient_id']} - {patient['first_name']} {patient['last_name']}"):
                        c1, c2 = st.columns(2)
                        with c1:
                            st.write(f"**DOB:** {patient['date_of_birth']}")
                            st.write(f"**Gender:** {patient['gender']}")
                            st.write(f"**Phone:** {patient['phone']}")
                            if patient['email']:
                                st.write(f"**Email:** {patient['email']}")
                        with c2:
                            if patient['address']:
                                st.write(f"**Address:** {patient['address']}")
                            if patient['id_number']:
                                st.write(f"**ID:** {patient['id_number']}")
                            if patient['emergency_contact']:
                                st.write(f"**Emergency:** {patient['emergency_contact']}")
                        st.markdown("---")
                        actions = st.columns(4)
                        with actions[0]:
                            if st.button("Begin Examination", key=f"exam_{patient['id']}"):
                                st.session_state.selected_patient = patient['patient_id']
                                st.session_state.menu = "Examination Protocol"
                                st.session_state.exam_step = "medical_history"
                                st.rerun()
                        with actions[1]:
                            if st.button("View History", key=f"history_{patient['id']}"):
                                st.session_state.selected_patient = patient['patient_id']
                                st.session_state.menu = "Patient Search"
                                st.rerun()
                        with actions[2]:
                            if st.button("Contact Lenses", key=f"cl_{patient['id']}"):
                                st.session_state.selected_patient = patient['patient_id']
                                st.session_state.menu = "Contact Lenses"
                                st.rerun()
                        with actions[3]:
                            if st.button("Schedule", key=f"schedule_{patient['id']}"):
                                st.session_state.selected_patient = patient['patient_id']
                                st.session_state.menu = "Schedule Appointment"
                                st.rerun()
            else:
                st.info("No patients found.")
        except Exception as e:
            st.error(f"Search error: {str(e)}")

# ---------------------
# NAVIGATION + MAIN
# ---------------------
def main_navigation():
    st.sidebar.title("OphtalCAM EMR")
    st.sidebar.markdown("---")
    if 'menu' not in st.session_state:
        st.session_state.menu = "Dashboard"
    if 'exam_step' not in st.session_state:
        st.session_state.exam_step = None

    menu_options = ["Dashboard","Patient Registration","Patient Search","Examination Protocol","Contact Lenses","Schedule Appointment","Clinical Analytics","Patient Groups","System Settings"]
    menu = st.sidebar.selectbox("Navigation", menu_options, index=menu_options.index(st.session_state.menu) if st.session_state.menu in menu_options else 0)
    st.session_state.menu = menu

    # exam workflow on sidebar
    if st.session_state.exam_step:
        st.sidebar.markdown("---")
        st.sidebar.subheader("Examination Protocol")
        steps = [("medical_history","1. Medical History"),("refraction","2. Refraction"),("functional_tests","3. Functional Tests"),("anterior_segment","4. Anterior Segment"),("posterior_segment","5. Posterior Segment"),("contact_lenses","6. Contact Lenses"),("generate_report","7. Clinical Report")]
        for step, label in steps:
            if step == st.session_state.exam_step:
                st.sidebar.markdown(f"<div class='exam-step active'>{label}</div>", unsafe_allow_html=True)
            else:
                st.sidebar.markdown(f"<div class='exam-step'>{label}</div>", unsafe_allow_html=True)

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Clinician:** {st.session_state.get('username', '')}")
    st.sidebar.markdown(f"**Role:** {st.session_state.get('role', '')}")

    # render
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
            st.info("Select a patient from Dashboard or Patient Search to begin examination.")
        elif menu == "Contact Lenses":
            st.info("Contact lens module - open a patient to proceed.")
        elif menu == "Schedule Appointment":
            st.info("Appointment scheduling - work in progress.")
        elif menu == "Clinical Analytics":
            st.info("Clinical analytics - work in progress.")
        elif menu == "Patient Groups":
            st.info("Patient groups management - work in progress.")
        elif menu == "System Settings":
            st.info("System settings - work in progress.")

def contact_lenses():
    st.subheader("Contact Lens Fitting & Prescription")
    st.info("Contact lens module - implement fitting parameters here.")
    if st.button("Return to Dashboard"):
        st.session_state.menu = "Dashboard"
        st.session_state.selected_patient = None
        st.rerun()

def generate_report():
    st.subheader("Generate Clinical Report")
    st.info("Report generation - summary + custom notes.")
    if st.button("Return to Dashboard"):
        st.session_state.exam_step = None
        st.session_state.selected_patient = None
        st.session_state.menu = "Dashboard"
        st.rerun()

# ---------------------
# LOGIN PAGE (removed rocket emoji)
# ---------------------
def login_page():
    st.markdown("""
    <style>
    .login-container { max-width:600px; margin:0 auto; padding:1rem; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3,2])
    with col1:
        st.image("https://i.postimg.cc/PrRFzQLv/Logo-Transparency-01.png", width=360)
        st.markdown("<h3 style='text-align:center;'>Ophthalmology Electronic Medical Records</h3>", unsafe_allow_html=True)
    with col2:
        st.image("https://i.postimg.cc/qq656tks/Phantasmed-logo.png", width=220)

    st.markdown("---")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<h4 style='text-align:center;'>Secure Clinical Access</h4>", unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Access Clinical System")
            if login_button:
                if username and password:
                    user, message = authenticate_user(username, password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.username = user[0]
                        st.session_state.role = user[2]
                        st.success(f"Access granted. Welcome {user[0]}!")
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please enter username and password")
        st.markdown("<div style='text-align:center; margin-top:1rem;'><small><strong>Demo access:</strong><br>Username: <code>admin</code><br>Password: <code>admin123</code></small></div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; margin-top:1rem; padding:0.6rem; background:#f8f9fa; border-radius:6px;'><small>Security Notice: This system contains protected health information. Unauthorized access is prohibited.</small></div>", unsafe_allow_html=True)

# ---------------------
# MAIN
# ---------------------
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
    if 'exam_step' not in st.session_state:
        st.session_state.exam_step = None

    if not st.session_state.logged_in:
        login_page()
    else:
        col1, col2, col3 = st.columns([3,1,1])
        with col1:
            st.image("https://i.postimg.cc/PrRFzQLv/Logo-Transparency-01.png", width=300)
        with col3:
            st.write(f"**Clinician:** {st.session_state.username}")
            st.write(f"**Role:** {st.session_state.role}")
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





