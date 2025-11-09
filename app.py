# app.py - OphtalCAM EMR (updated: EU date, habitual + subjective VA modifiers, pupillography moved to anterior, flow fixes)
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

    # Users
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
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

    # ensure missing patient cols
    try:
        c.execute("PRAGMA table_info(patients)")
        existing = [r[1] for r in c.fetchall()]
        needed = {"id_number":"TEXT","emergency_contact":"TEXT","insurance_info":"TEXT","gender":"TEXT","phone":"TEXT","email":"TEXT","address":"TEXT"}
        for col, ctype in needed.items():
            if col not in existing:
                try:
                    c.execute(f"ALTER TABLE patients ADD COLUMN {col} {ctype}")
                except Exception:
                    pass
    except Exception:
        pass

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
    # migration for medical_history
    try:
        c.execute("PRAGMA table_info(medical_history)")
        cols = [r[1] for r in c.fetchall()]
        if "uploaded_reports" not in cols:
            c.execute("ALTER TABLE medical_history ADD COLUMN uploaded_reports TEXT")
    except Exception:
        pass

    # Refraction exams - expanded to include habitual modifiers, subjective VA, etc.
    c.execute('''
        CREATE TABLE IF NOT EXISTS refraction_exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            exam_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            -- Habitual
            habitual_type TEXT,
            habitual_od_va TEXT,
            habitual_od_modifier TEXT,
            habitual_os_va TEXT,
            habitual_os_modifier TEXT,
            habitual_binocular_va TEXT,
            habitual_binocular_modifier TEXT,
            habitual_pd TEXT,
            habitual_notes TEXT,
            vision_notes TEXT,

            -- Uncorrected vision
            uncorrected_od_va TEXT,
            uncorrected_od_modifier TEXT,
            uncorrected_os_va TEXT,
            uncorrected_os_modifier TEXT,
            uncorrected_binocular_va TEXT,
            uncorrected_binocular_modifier TEXT,

            -- Objective
            objective_method TEXT,
            objective_time TEXT,
            autorefractor_od_sphere REAL,
            autorefractor_od_cylinder REAL,
            autorefractor_od_axis INTEGER,
            autorefractor_os_sphere REAL,
            autorefractor_os_cylinder REAL,
            autorefractor_os_axis INTEGER,
            objective_notes TEXT,

            -- Cycloplegic
            cycloplegic_used BOOLEAN,
            cycloplegic_agent TEXT,
            cycloplegic_lot TEXT,
            cycloplegic_expiry DATE,
            cycloplegic_drops INTEGER,
            cycloplegic_objective_od TEXT,
            cycloplegic_objective_os TEXT,

            -- Subjective (monocular) + VA
            subjective_method TEXT,
            subjective_od_sphere REAL,
            subjective_od_cylinder REAL,
            subjective_od_axis INTEGER,
            subjective_od_va TEXT,
            subjective_od_modifier TEXT,
            subjective_os_sphere REAL,
            subjective_os_cylinder REAL,
            subjective_os_axis INTEGER,
            subjective_os_va TEXT,
            subjective_os_modifier TEXT,
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
            final_prescribed_binocular_modifier TEXT,
            bvp TEXT,
            pinhole TEXT,
            prescription_notes TEXT,

            -- other
            binocular_tests TEXT,
            functional_tests TEXT,
            accommodation_tests TEXT,
            uploaded_files TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')

    # auto-migrate refraction_exams missing columns (comprehensive)
    try:
        c.execute("PRAGMA table_info(refraction_exams)")
        existing = [r[1] for r in c.fetchall()]
        new_cols = {
            # Habitual
            "habitual_type":"TEXT","habitual_od_va":"TEXT","habitual_od_modifier":"TEXT","habitual_os_va":"TEXT","habitual_os_modifier":"TEXT",
            "habitual_binocular_va":"TEXT","habitual_binocular_modifier":"TEXT","habitual_pd":"TEXT","habitual_notes":"TEXT","vision_notes":"TEXT",
            # Uncorrected
            "uncorrected_od_va":"TEXT","uncorrected_od_modifier":"TEXT","uncorrected_os_va":"TEXT","uncorrected_os_modifier":"TEXT",
            "uncorrected_binocular_va":"TEXT","uncorrected_binocular_modifier":"TEXT",
            # Objective
            "objective_method":"TEXT","objective_time":"TEXT","autorefractor_od_sphere":"REAL","autorefractor_od_cylinder":"REAL","autorefractor_od_axis":"INTEGER",
            "autorefractor_os_sphere":"REAL","autorefractor_os_cylinder":"REAL","autorefractor_os_axis":"INTEGER","objective_notes":"TEXT",
            # Cycloplegic
            "cycloplegic_used":"BOOLEAN","cycloplegic_agent":"TEXT","cycloplegic_lot":"TEXT","cycloplegic_expiry":"DATE","cycloplegic_drops":"INTEGER",
            # Subjective & VA
            "subjective_method":"TEXT","subjective_od_sphere":"REAL","subjective_od_cylinder":"REAL","subjective_od_axis":"INTEGER",
            "subjective_od_va":"TEXT","subjective_od_modifier":"TEXT","subjective_os_sphere":"REAL","subjective_os_cylinder":"REAL","subjective_os_axis":"INTEGER",
            "subjective_os_va":"TEXT","subjective_os_modifier":"TEXT","subjective_notes":"TEXT",
            # Final
            "binocular_balance":"TEXT","stereopsis":"TEXT","near_point_convergence_break":"TEXT","near_point_convergence_recovery":"TEXT",
            "final_prescribed_od_sphere":"REAL","final_prescribed_od_cylinder":"REAL","final_prescribed_od_axis":"INTEGER",
            "final_prescribed_os_sphere":"REAL","final_prescribed_os_cylinder":"REAL","final_prescribed_os_axis":"INTEGER",
            "final_prescribed_binocular_va":"TEXT","final_prescribed_binocular_modifier":"TEXT","bvp":"TEXT","pinhole":"TEXT","prescription_notes":"TEXT",
            # other
            "binocular_tests":"TEXT","functional_tests":"TEXT","accommodation_tests":"TEXT","uploaded_files":"TEXT"
        }
        for col, ctype in new_cols.items():
            if col not in existing:
                try:
                    c.execute(f"ALTER TABLE refraction_exams ADD COLUMN {col} {ctype}")
                except Exception:
                    pass
    except Exception:
        pass

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
            confrontation_fields TEXT,
            other_notes TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')
    # migration for functional_tests
    try:
        c.execute("PRAGMA table_info(functional_tests)")
        cols = [r[1] for r in c.fetchall()]
        needed = {"motility":"TEXT","hirschberg":"TEXT","cover_test_distance":"TEXT","cover_test_near":"TEXT","pupils":"TEXT","confrontation_fields":"TEXT","other_notes":"TEXT"}
        for col, ctype in needed.items():
            if col not in cols:
                try:
                    c.execute(f"ALTER TABLE functional_tests ADD COLUMN {col} {ctype}")
                except Exception:
                    pass
    except Exception:
        pass

    # Anterior segment (move pupillography here)
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
    # migration anterior
    try:
        c.execute("PRAGMA table_info(anterior_segment_exams)")
        cols = [r[1] for r in c.fetchall()]
        needed = {
            "biomicroscopy_od":"TEXT","biomicroscopy_os":"TEXT","biomicroscopy_notes":"TEXT",
            "anterior_chamber_depth_od":"TEXT","anterior_chamber_depth_os":"TEXT","anterior_chamber_volume_od":"TEXT","anterior_chamber_volume_os":"TEXT",
            "iridocorneal_angle_od":"TEXT","iridocorneal_angle_os":"TEXT","pachymetry_od":"REAL","pachymetry_os":"REAL",
            "tonometry_type":"TEXT","tonometry_time":"TEXT","tonometry_compensation":"TEXT","tonometry_od":"TEXT","tonometry_os":"TEXT",
            "aberometry_notes":"TEXT","corneal_topography_notes":"TEXT","anterior_segment_notes":"TEXT",
            "pupillography_results":"TEXT","pupillography_notes":"TEXT","pupillography_files":"TEXT","uploaded_files":"TEXT"
        }
        for col, ctype in needed.items():
            if col not in cols:
                try:
                    c.execute(f"ALTER TABLE anterior_segment_exams ADD COLUMN {col} {ctype}")
                except Exception:
                    pass
    except Exception:
        pass

    # Posterior segment (remove pupillography from here)
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
    try:
        c.execute("PRAGMA table_info(posterior_segment_exams)")
        cols = [r[1] for r in c.fetchall()]
        needed = {
            "fundus_exam_type":"TEXT","fundus_od":"TEXT","fundus_os":"TEXT","fundus_notes":"TEXT",
            "oct_macula_od":"TEXT","oct_macula_os":"TEXT","oct_rnfl_od":"TEXT","oct_rnfl_os":"TEXT","oct_notes":"TEXT",
            "posterior_segment_notes":"TEXT","uploaded_files":"TEXT"
        }
        for col, ctype in needed.items():
            if col not in cols:
                try:
                    c.execute(f"ALTER TABLE posterior_segment_exams ADD COLUMN {col} {ctype}")
                except Exception:
                    pass
    except Exception:
        pass

    # Contact lenses table
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
            scleral_diameter TEXT,
            wearing_schedule TEXT,
            care_solution TEXT,
            follow_up_date DATE,
            fitting_notes TEXT,
            uploaded_files TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')

    # Groups, appointments...
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

    # default admin + groups
    try:
        admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)", ("admin", admin_hash, "admin"))
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
        ("Neuro-ophthalmology", "Optic neuritis, Papilledema, Cranial nerve palsies")
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
        st.error(f"Error getting patient stats: {e}")
        return 0, 0, 0

# Simple CSS
def load_css():
    st.markdown("""
    <style>
    body { font-family: Arial, sans-serif; }
    .metric-card { background: linear-gradient(135deg,#1e3c72 0%,#2a5298 100%); color:white; padding:1rem; border-radius:8px; text-align:center; }
    .appointment-card { background:#f8f9fa; padding:0.8rem; border-radius:6px; border-left:4px solid #1e3c72; margin-bottom:0.5rem; }
    </style>
    """, unsafe_allow_html=True)

# -----------------------
# UI: Dashboard, Registration, Search etc.
# -----------------------
def show_dashboard():
    st.markdown("<h1 style='text-align:center;'>OphtalCAM Clinical Dashboard</h1>", unsafe_allow_html=True)
    col_filter = st.columns([2,1,1,1])
    with col_filter[0]:
        view_option = st.selectbox("Time View", ["Today","This Week","This Month"], key="view_filter")
    with col_filter[3]:
        if st.button("+ New Appointment", use_container_width=True, key="new_appt_btn"):
            st.session_state.menu = "Schedule Appointment"
            st.rerun()
    total_patients, today_exams, total_cl = get_patient_stats()
    col_metrics = st.columns(3)
    with col_metrics[0]:
        st.markdown(f"<div class='metric-card'><div style='font-size:18px'>{total_patients}</div><div>Registered Patients</div></div>", unsafe_allow_html=True)
    with col_metrics[1]:
        st.markdown(f"<div class='metric-card'><div style='font-size:18px'>{today_exams}</div><div>Scheduled Exams (today)</div></div>", unsafe_allow_html=True)
    with col_metrics[2]:
        st.markdown(f"<div class='metric-card'><div style='font-size:18px'>{total_cl}</div><div>Contact Lens Prescriptions</div></div>", unsafe_allow_html=True)

    col_main = st.columns([2,1])
    with col_main[0]:
        st.subheader("Today's Clinical Schedule")
        appts = get_todays_appointments()
        if not appts.empty:
            for _, apt in appts.iterrows():
                t = pd.to_datetime(apt['appointment_date']).strftime('%H:%M')
                st.markdown(f"<div class='appointment-card'><strong>{t}</strong> - {apt['first_name']} {apt['last_name']} ({apt['patient_id']})<br><small>{apt['appointment_type']} | {apt['status']}</small></div>", unsafe_allow_html=True)
                colb = st.columns(2)
                with colb[0]:
                    if st.button("Begin Examination", key=f"begin_{apt['id']}"):
                        st.session_state.selected_patient = apt['patient_id']
                        st.session_state.menu = "Examination Protocol"
                        st.session_state.exam_step = "medical_history"
                        st.rerun()
                with colb[1]:
                    if st.button("Patient Details", key=f"det_{apt['id']}"):
                        st.session_state.selected_patient = apt['patient_id']
                        st.session_state.menu = "Patient Search"
                        st.rerun()
        else:
            st.info("No appointments for today.")
    with col_main[1]:
        st.subheader("Mini Calendar")
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
                if day==0:
                    cols[i].write("")
                else:
                    if day==today.day:
                        cols[i].markdown(f"<div style='background:#1e3c72;color:white;border-radius:50%;text-align:center;padding:4px'><strong>{day}</strong></div>", unsafe_allow_html=True)
                    else:
                        cols[i].write(str(day))
        st.markdown("---")
        if st.button("New Patient Registration", use_container_width=True, key="new_patient_btn"):
            st.session_state.menu = "Patient Registration"
            st.rerun()
        if st.button("Patient Search & Records", use_container_width=True, key="search_patient_btn"):
            st.session_state.menu = "Patient Search"
            st.rerun()

def medical_history():
    st.subheader("Comprehensive Medical History")
    if 'selected_patient' not in st.session_state or not st.session_state.selected_patient:
        st.error("No patient selected.")
        return
    pid = st.session_state.selected_patient
    try:
        pinfo = pd.read_sql("SELECT * FROM patients WHERE patient_id = ?", conn, params=(pid,)).iloc[0]
        st.markdown(f"### {pinfo['first_name']} {pinfo['last_name']} (ID: {pinfo['patient_id']})")
    except Exception:
        st.error("Patient not found.")
        return
    with st.form("mh_form"):
        st.markdown("#### General Health")
        g1, g2 = st.columns(2)
        with g1:
            general_health = st.text_area("General health", height=100, key="gen_health")
            current_medications = st.text_area("Current medications", height=80, key="curr_meds")
            allergies = st.text_area("Allergies", height=80, key="allergies")
        with g2:
            headaches = st.text_area("Headaches / Migraines", height=100, key="headaches")
            family_history = st.text_area("Family medical history", height=100, key="family_hist")
            ocular_history = st.text_area("Ocular history", height=80, key="ocular_hist")
        st.markdown("#### Social / Lifestyle")
        s1, s2 = st.columns(2)
        with s1:
            smoking = st.selectbox("Smoking status", ["Non-smoker","Former","Current","Unknown"], key="smoking")
            alcohol = st.selectbox("Alcohol", ["None","Occasional","Moderate","Heavy"], key="alcohol")
        with s2:
            occupation = st.text_input("Occupation", key="occupation")
            hobbies = st.text_area("Hobbies", height=60, key="hobbies")
        uploaded = st.file_uploader("Upload previous reports (pdf/jpg/png)", type=['pdf','jpg','png'], accept_multiple_files=True, key="mh_uploads")
        submit = st.form_submit_button("Save Medical History & Continue")
        if submit:
            try:
                files = []
                if uploaded:
                    os.makedirs("uploads", exist_ok=True)
                    for f in uploaded:
                        # Sanitize filename
                        safe_name = "".join(c for c in f.name if c.isalnum() or c in "._- ")
                        path = os.path.join("uploads", f"{datetime.now().timestamp()}_{safe_name}")
                        with open(path, "wb") as fp:
                            fp.write(f.getbuffer())
                        files.append(path)
                c = conn.cursor()
                c.execute('''
                    INSERT INTO medical_history
                    (patient_id, general_health, current_medications, allergies, headaches_history, family_history,
                     ocular_history, smoking_status, alcohol_consumption, occupation, hobbies, uploaded_reports)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (pinfo['id'], general_health, current_medications, allergies, headaches, family_history, 
                     ocular_history, smoking, alcohol, occupation, hobbies, json.dumps(files)))
                conn.commit()
                st.success("Medical history saved.")
                st.session_state.exam_step = "refraction"
                st.rerun()
            except Exception as e:
                st.error(f"Database error: {str(e)}")

# Refraction examination with requested layout changes
def refraction_examination():
    st.subheader("Comprehensive Refraction & Vision Examination")
    if 'selected_patient' not in st.session_state or not st.session_state.selected_patient:
        st.error("No patient selected.")
        return
    pid_code = st.session_state.selected_patient
    try:
        pinfo = pd.read_sql("SELECT * FROM patients WHERE patient_id = ?", conn, params=(pid_code,)).iloc[0]
        st.markdown(f"### {pinfo['first_name']} {pinfo['last_name']} (ID: {pinfo['patient_id']})")
    except Exception:
        st.error("Patient not found.")
        return

    if 'refraction' not in st.session_state:
        st.session_state.refraction = {}

    # 1) Vision Examination - Habitual & Uncorrected (Habitual prominent)
    st.markdown("#### 1) Vision Examination — Habitual & Uncorrected")
    with st.form("vision_form"):
        c1, c2 = st.columns([2,2])
        with c1:
            st.markdown("**Habitual Correction**")
            habitual_type = st.selectbox("Type of Habitual Correction", ["None","Spectacles","Soft Contact Lenses","RGP","Scleral","Ortho-K","Other"], index=0, key="habit_type")
            # aligned OD / OS for habit VA with small modifier
            hcol_od, spacer, hcol_os = st.columns([2,0.2,2])
            with hcol_od:
                habitual_od_va = st.text_input("Habitual VA OD", placeholder="e.g., 1.0 or 20/20", key="habit_od_va")
            with hcol_os:
                habitual_os_va = st.text_input("Habitual VA OS", placeholder="e.g., 1.0 or 20/20", key="habit_os_va")
            # modifiers row
            hmod_od, _, hmod_os = st.columns([1,0.2,1])
            with hmod_od:
                habitual_od_modifier = st.text_input("Modifier OD", placeholder="-2", help="Optional small note, e.g. -2", key="habit_od_mod")
            with hmod_os:
                habitual_os_modifier = st.text_input("Modifier OS", placeholder="-2", key="habit_os_mod")
            # binocular
            habitual_bin_va = st.text_input("Habitual Binocular VA", placeholder="1.0 or 20/20", key="habit_bin_va")
            habitual_bin_modifier = st.text_input("Binocular modifier", placeholder="-2", key="habit_bin_mod")
            habitual_pd = st.text_input("PD (mm)", key="habit_pd")
        with c2:
            st.markdown("**Uncorrected Vision**")
            uncorrected_od_va = st.text_input("Uncorrected VA OD", placeholder="e.g., 1.0 or 20/200", key="uncorr_od_va")
            uncorrected_od_modifier = st.text_input("Modifier OD", placeholder="-2", key="uncorr_od_mod")
            uncorrected_os_va = st.text_input("Uncorrected VA OS", placeholder="e.g., 1.0 or 20/200", key="uncorr_os_va")
            uncorrected_os_modifier = st.text_input("Modifier OS", placeholder="-2", key="uncorr_os_mod")
            uncorrected_bin_va = st.text_input("Uncorrected Binocular VA", placeholder="1.0", key="uncorr_bin_va")
            uncorrected_bin_modifier = st.text_input("Uncorrected binocular modifier", placeholder="-2", key="uncorr_bin_mod")
            vision_notes = st.text_area("Vision notes", height=140, key="vision_notes")
        savev = st.form_submit_button("Save Vision Section")
        if savev:
            st.session_state.refraction.update({
                'habitual_type': habitual_type,
                'habitual_od_va': habitual_od_va,
                'habitual_od_modifier': habitual_od_modifier,
                'habitual_os_va': habitual_os_va,
                'habitual_os_modifier': habitual_os_modifier,
                'habitual_binocular_va': habitual_bin_va,
                'habitual_binocular_modifier': habitual_bin_modifier,
                'habitual_pd': habitual_pd,
                'uncorrected_od_va': uncorrected_od_va,
                'uncorrected_od_modifier': uncorrected_od_modifier,
                'uncorrected_os_va': uncorrected_os_va,
                'uncorrected_os_modifier': uncorrected_os_modifier,
                'uncorrected_binocular_va': uncorrected_bin_va,
                'uncorrected_binocular_modifier': uncorrected_bin_modifier,
                'vision_notes': vision_notes
            })
            st.success("Vision section saved locally.")
            st.rerun()

    st.markdown("---")
    # 2) Objective refraction (method + time inline, OD/OS aligned)
    st.markdown("#### 2) Objective Refraction (Autorefractor / Retinoscopy)")
    with st.form("objective_form"):
        top1, top2 = st.columns([2,2])
        with top1:
            objective_method = st.selectbox("Objective Method", ["Autorefractor","Retinoscopy","Other"], index=0, key="obj_method")
        with top2:
            objective_time = st.time_input("Time of measurement", value=datetime.now().time(), key="obj_time")
        od_col, spacer, os_col = st.columns([2,0.2,2])
        with od_col:
            st.markdown("**Right Eye (OD)**")
            autorefractor_od_sphere = st.number_input("Sphere OD", value=0.0, step=0.25, format="%.2f", key="obj_od_sph")
            autorefractor_od_cylinder = st.number_input("Cylinder OD", value=0.0, step=0.25, format="%.2f", key="obj_od_cyl")
            autorefractor_od_axis = st.number_input("Axis OD", min_value=0, max_value=180, value=0, key="obj_od_ax")
        with os_col:
            st.markdown("**Left Eye (OS)**")
            autorefractor_os_sphere = st.number_input("Sphere OS", value=0.0, step=0.25, format="%.2f", key="obj_os_sph")
            autorefractor_os_cylinder = st.number_input("Cylinder OS", value=0.0, step=0.25, format="%.2f", key="obj_os_cyl")
            autorefractor_os_axis = st.number_input("Axis OS", min_value=0, max_value=180, value=0, key="obj_os_ax")
        objective_notes = st.text_area("Objective notes", height=120, key="obj_notes")
        save_obj = st.form_submit_button("Save Objective Section")
        if save_obj:
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
            st.success("Objective section saved locally.")
            st.rerun()

    st.markdown("---")
    # 3) Cycloplegic & Subjective (aligned, smaller boxes for cycloplegic data)
    st.markdown("#### 3) Cycloplegic (if used) & Subjective Monocular Refraction")
    with st.form("subjective_form"):
        subj_method = st.selectbox("Subjective method", ["Fogging","With Cycloplegic","Other"], key="subj_method")
        cycloplegic_used = True if subj_method == "With Cycloplegic" else False
        if cycloplegic_used:
            c1,c2,c3,c4 = st.columns([1,1,1,1])
            with c1:
                cycloplegic_agent = st.text_input("Agent", placeholder="Cyclopentolate 1%", key="cyclo_agent")
            with c2:
                cycloplegic_lot = st.text_input("Lot #", placeholder="LOT123", key="cyclo_lot")
            with c3:
                cycloplegic_expiry = st.date_input("Expiry", value=date.today(), key="cyclo_expiry")
            with c4:
                cycloplegic_drops = st.number_input("Drops", min_value=1, max_value=10, value=1, key="cyclo_drops")
        else:
            cycloplegic_agent = ""
            cycloplegic_lot = ""
            cycloplegic_expiry = None
            cycloplegic_drops = None

        sod_col, _, sos_col = st.columns([2,0.2,2])
        with sod_col:
            st.markdown("**Right Eye (OD)**")
            subjective_od_sphere = st.number_input("Sphere OD", value=0.0, step=0.25, format="%.2f", key="subj_od_sph")
            subjective_od_cylinder = st.number_input("Cylinder OD", value=0.0, step=0.25, format="%.2f", key="subj_od_cyl")
            subjective_od_axis = st.number_input("Axis OD", min_value=0, max_value=180, value=0, key="subj_od_ax")
            subjective_od_va = st.text_input("Subjective VA OD", placeholder="e.g., 1.0 or 20/20", key="subj_od_va")
            subjective_od_modifier = st.text_input("Modifier OD", placeholder="-2", key="subj_od_mod")
        with sos_col:
            st.markdown("**Left Eye (OS)**")
            subjective_os_sphere = st.number_input("Sphere OS", value=0.0, step=0.25, format="%.2f", key="subj_os_sph")
            subjective_os_cylinder = st.number_input("Cylinder OS", value=0.0, step=0.25, format="%.2f", key="subj_os_cyl")
            subjective_os_axis = st.number_input("Axis OS", min_value=0, max_value=180, value=0, key="subj_os_ax")
            subjective_os_va = st.text_input("Subjective VA OS", placeholder="e.g., 1.0 or 20/20", key="subj_os_va")
            subjective_os_modifier = st.text_input("Modifier OS", placeholder="-2", key="subj_os_mod")
        subjective_notes = st.text_area("Subjective notes", height=120, key="subj_notes")
        save_subj = st.form_submit_button("Save Subjective Section")
        if save_subj:
            st.session_state.refraction.update({
                'subjective_method': subj_method,
                'cycloplegic_used': cycloplegic_used,
                'cycloplegic_agent': cycloplegic_agent,
                'cycloplegic_lot': cycloplegic_lot,
                'cycloplegic_expiry': cycloplegic_expiry,
                'cycloplegic_drops': cycloplegic_drops,
                'subjective_od_sphere': subjective_od_sphere,
                'subjective_od_cylinder': subjective_od_cylinder,
                'subjective_od_axis': subjective_od_axis,
                'subjective_od_va': subjective_od_va,
                'subjective_od_modifier': subjective_od_modifier,
                'subjective_os_sphere': subjective_os_sphere,
                'subjective_os_cylinder': subjective_os_cylinder,
                'subjective_os_axis': subjective_os_axis,
                'subjective_os_va': subjective_os_va,
                'subjective_os_modifier': subjective_os_modifier,
                'subjective_notes': subjective_notes
            })
            st.success("Subjective section saved locally.")
            st.rerun()

    st.markdown("---")
    # 4) Binocular & Final Prescription (aligned OD/OS)
    st.markdown("#### 4) Binocular Tests & Final Prescription")
    with st.form("final_form"):
        left_col, right_col = st.columns([2,2])
        with left_col:
            st.markdown("**Right Eye (OD) - Final**")
            final_od_sph = st.number_input("Final Sphere OD", value=0.0, step=0.25, format="%.2f", key="final_od_sph")
            final_od_cyl = st.number_input("Final Cylinder OD", value=0.0, step=0.25, format="%.2f", key="final_od_cyl")
            final_od_axis = st.number_input("Final Axis OD", min_value=0, max_value=180, value=0, key="final_od_ax")
        with right_col:
            st.markdown("**Left Eye (OS) - Final**")
            final_os_sph = st.number_input("Final Sphere OS", value=0.0, step=0.25, format="%.2f", key="final_os_sph")
            final_os_cyl = st.number_input("Final Cylinder OS", value=0.0, step=0.25, format="%.2f", key="final_os_cyl")
            final_os_axis = st.number_input("Final Axis OS", min_value=0, max_value=180, value=0, key="final_os_ax")
        # binocular and notes
        bin1, bin2 = st.columns([2,2])
        with bin1:
            final_bin_va = st.text_input("Final Binocular VA", placeholder="e.g., 1.0 or 20/20", key="final_bin_va")
            final_bin_modifier = st.text_input("Final Binocular modifier", placeholder="-2", key="final_bin_mod")
            bvp = st.text_input("BVP", key="bvp")
            pinhole = st.text_input("Pinhole VA", key="pinhole")
        with bin2:
            binocular_balance = st.selectbox("Binocular Balance", ["Balanced","OD dominant","OS dominant","Unbalanced"], key="bin_balance")
            stereopsis = st.text_input("Stereoacuity", key="stereopsis")
            npc_break = st.text_input("NPC Break", key="npc_break")
            npc_recovery = st.text_input("NPC Recovery", key="npc_recovery")
            binocular_tests = st.text_area("Binocular tests (phoria, cover test, Worth, etc.)", height=120, key="bin_tests")
        prescription_notes = st.text_area("Prescription notes / rationale", height=140, key="presc_notes")
        save_final = st.form_submit_button("Save & Finalize Refraction")
        if save_final:
            try:
                p = pd.read_sql("SELECT id FROM patients WHERE patient_id = ?", conn, params=(pid_code,)).iloc[0]
                pid = p['id']
                uploaded_files = st.session_state.refraction.get('uploaded_files', [])
                c = conn.cursor()
                c.execute('''
                    INSERT INTO refraction_exams
                    (patient_id, habitual_type, habitual_od_va, habitual_od_modifier, habitual_os_va, habitual_os_modifier,
                     habitual_binocular_va, habitual_binocular_modifier, habitual_pd, vision_notes,
                     uncorrected_od_va, uncorrected_od_modifier, uncorrected_os_va, uncorrected_os_modifier, uncorrected_binocular_va, uncorrected_binocular_modifier,
                     objective_method, objective_time,
                     autorefractor_od_sphere, autorefractor_od_cylinder, autorefractor_od_axis,
                     autorefractor_os_sphere, autorefractor_os_cylinder, autorefractor_os_axis, objective_notes,
                     cycloplegic_used, cycloplegic_agent, cycloplegic_lot, cycloplegic_expiry, cycloplegic_drops,
                     subjective_method, subjective_od_sphere, subjective_od_cylinder, subjective_od_axis, subjective_od_va, subjective_od_modifier,
                     subjective_os_sphere, subjective_os_cylinder, subjective_os_axis, subjective_os_va, subjective_os_modifier, subjective_notes,
                     binocular_balance, stereopsis, near_point_convergence_break, near_point_convergence_recovery,
                     final_prescribed_od_sphere, final_prescribed_od_cylinder, final_prescribed_od_axis,
                     final_prescribed_os_sphere, final_prescribed_os_cylinder, final_prescribed_os_axis,
                     final_prescribed_binocular_va, final_prescribed_binocular_modifier, bvp, pinhole, prescription_notes,
                     binocular_tests, uploaded_files)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ''', (
                    pid,
                    st.session_state.refraction.get('habitual_type'),
                    st.session_state.refraction.get('habitual_od_va'),
                    st.session_state.refraction.get('habitual_od_modifier'),
                    st.session_state.refraction.get('habitual_os_va'),
                    st.session_state.refraction.get('habitual_os_modifier'),
                    st.session_state.refraction.get('habitual_binocular_va'),
                    st.session_state.refraction.get('habitual_binocular_modifier'),
                    st.session_state.refraction.get('habitual_pd'),
                    st.session_state.refraction.get('vision_notes'),
                    st.session_state.refraction.get('uncorrected_od_va'),
                    st.session_state.refraction.get('uncorrected_od_modifier'),
                    st.session_state.refraction.get('uncorrected_os_va'),
                    st.session_state.refraction.get('uncorrected_os_modifier'),
                    st.session_state.refraction.get('uncorrected_binocular_va'),
                    st.session_state.refraction.get('uncorrected_binocular_modifier'),
                    st.session_state.refraction.get('objective_method'),
                    st.session_state.refraction.get('objective_time'),
                    st.session_state.refraction.get('autorefractor_od_sphere'),
                    st.session_state.refraction.get('autorefractor_od_cylinder'),
                    st.session_state.refraction.get('autorefractor_od_axis'),
                    st.session_state.refraction.get('autorefractor_os_sphere'),
                    st.session_state.refraction.get('autorefractor_os_cylinder'),
                    st.session_state.refraction.get('autorefractor_os_axis'),
                    st.session_state.refraction.get('objective_notes'),
                    st.session_state.refraction.get('cycloplegic_used'),
                    st.session_state.refraction.get('cycloplegic_agent'),
                    st.session_state.refraction.get('cycloplegic_lot'),
                    st.session_state.refraction.get('cycloplegic_expiry'),
                    st.session_state.refraction.get('cycloplegic_drops'),
                    st.session_state.refraction.get('subjective_method'),
                    st.session_state.refraction.get('subjective_od_sphere'),
                    st.session_state.refraction.get('subjective_od_cylinder'),
                    st.session_state.refraction.get('subjective_od_axis'),
                    st.session_state.refraction.get('subjective_od_va'),
                    st.session_state.refraction.get('subjective_od_modifier'),
                    st.session_state.refraction.get('subjective_os_sphere'),
                    st.session_state.refraction.get('subjective_os_cylinder'),
                    st.session_state.refraction.get('subjective_os_axis'),
                    st.session_state.refraction.get('subjective_os_va'),
                    st.session_state.refraction.get('subjective_os_modifier'),
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
                    final_bin_modifier,
                    bvp,
                    pinhole,
                    prescription_notes,
                    binocular_tests,
                    json.dumps(uploaded_files)
                ))
                conn.commit()
                st.success("Refraction saved to database.")
                # after finalizing refraction continue to functional tests
                st.session_state.refraction = {}
                st.session_state.exam_step = "functional_tests"
                st.rerun()
            except Exception as e:
                st.error(f"Database error when saving refraction: {str(e)}")

# Functional tests
def functional_tests():
    st.subheader("Functional Vision Tests")
    if 'selected_patient' not in st.session_state or not st.session_state.selected_patient:
        st.error("No patient selected.")
        return
    pid = st.session_state.selected_patient
    with st.form("functional_form"):
        motility = st.text_area("Ocular motility (notes)", height=120, key="motility")
        hirschberg = st.text_input("Hirschberg result", key="hirschberg")
        npc_break = st.text_input("NPC Break", key="func_npc_break")
        npc_recovery = st.text_input("NPC Recovery", key="func_npc_recovery")
        pupils = st.text_input("Pupils (size/reactivity)", key="pupils")
        rapd = st.selectbox("RAPD", ["None","Present","Unsure"], key="rapd")
        confrontation = st.text_area("Confrontation visual field", height=100, key="confrontation")
        func_notes = st.text_area("Functional notes", height=80, key="func_notes")
        savef = st.form_submit_button("Save Functional Tests")
        if savef:
            try:
                p = pd.read_sql("SELECT id FROM patients WHERE patient_id = ?", conn, params=(pid,)).iloc[0]
                c = conn.cursor()
                c.execute('''
                    INSERT INTO functional_tests (patient_id, motility, hirschberg, cover_test_distance, cover_test_near, pupils, confrontation_fields, other_notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (p['id'], motility, hirschberg, npc_break, npc_recovery, pupils, confrontation, func_notes))
                conn.commit()
                st.success("Functional tests saved.")
                st.session_state.exam_step = "anterior_segment"
                st.rerun()
            except Exception as e:
                st.error(f"Database error: {str(e)}")

# Anterior segment (with pupillography)
def anterior_segment_examination():
    st.subheader("Anterior Segment Examination & Biomicroscopy")
    if 'selected_patient' not in st.session_state or not st.session_state.selected_patient:
        st.error("No patient selected.")
        return
    pid = st.session_state.selected_patient
    with st.form("anterior_form"):
        c1,c2 = st.columns([2,2])
        with c1:
            biomicroscopy_od = st.text_area("Biomicroscopy OD", height=120, key="bio_od")
            biomicroscopy_os = st.text_area("Biomicroscopy OS", height=120, key="bio_os")
            biomicroscopy_notes = st.text_area("Biomicroscopy notes", height=80, key="bio_notes")
        with c2:
            acd_od = st.text_input("AC Depth OD", key="acd_od")
            acd_os = st.text_input("AC Depth OS", key="acd_os")
            acv_od = st.text_input("AC Volume OD", key="acv_od")
            acv_os = st.text_input("AC Volume OS", key="acv_os")
            iridocorneal_od = st.text_input("Iridocorneal Angle OD", key="ica_od")
            iridocorneal_os = st.text_input("Iridocorneal Angle OS", key="ica_os")
        st.markdown("#### Pupillography")
        pup_res = st.text_area("Pupillography results / pupillometry notes", height=80, key="pupil_res")
        pup_notes = st.text_area("Pupillography notes", height=60, key="pupil_notes")
        pup_files = st.file_uploader("Upload pupillography images/reports", type=['pdf','png','jpg','jpeg'], accept_multiple_files=True, key="pupil_files")
        files = st.file_uploader("Upload slit-lamp / pachymetry / topography", type=['pdf','png','jpg','jpeg'], accept_multiple_files=True, key="ant_files")
        savea = st.form_submit_button("Save Anterior Segment")
        if savea:
            try:
                p = pd.read_sql("SELECT id FROM patients WHERE patient_id = ?", conn, params=(pid,)).iloc[0]
                file_paths = []
                pup_paths = []
                if files:
                    os.makedirs("uploads", exist_ok=True)
                    for f in files:
                        safe_name = "".join(c for c in f.name if c.isalnum() or c in "._- ")
                        path = os.path.join("uploads", f"{datetime.now().timestamp()}_{safe_name}")
                        with open(path, "wb") as fp:
                            fp.write(f.getbuffer())
                        file_paths.append(path)
                if pup_files:
                    os.makedirs("uploads", exist_ok=True)
                    for f in pup_files:
                        safe_name = "".join(c for c in f.name if c.isalnum() or c in "._- ")
                        path = os.path.join("uploads", f"{datetime.now().timestamp()}_{safe_name}")
                        with open(path, "wb") as fp:
                            fp.write(f.getbuffer())
                        pup_paths.append(path)
                c = conn.cursor()
                c.execute('''
                    INSERT INTO anterior_segment_exams (patient_id, biomicroscopy_od, biomicroscopy_os, biomicroscopy_notes,
                        anterior_chamber_depth_od, anterior_chamber_depth_os, anterior_chamber_volume_od, anterior_chamber_volume_os,
                        iridocorneal_angle_od, iridocorneal_angle_os, pupillography_results, pupillography_notes, pupillography_files, uploaded_files)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (p['id'], biomicroscopy_od, biomicroscopy_os, biomicroscopy_notes,
                      acd_od, acd_os, acv_od, acv_os, iridocorneal_od, iridocorneal_os, pup_res, pup_notes, json.dumps(pup_paths), json.dumps(file_paths)))
                conn.commit()
                st.success("Anterior segment saved.")
                st.session_state.exam_step = "posterior_segment"
                st.rerun()
            except Exception as e:
                st.error(f"Database error: {str(e)}")

# Posterior segment - after save continue to Contact Lenses instead of Dashboard
def posterior_segment_examination():
    st.subheader("Posterior Segment Examination & Imaging")
    if 'selected_patient' not in st.session_state or not st.session_state.selected_patient:
        st.error("No patient selected.")
        return
    pid = st.session_state.selected_patient
    with st.form("posterior_form"):
        fundus_type = st.selectbox("Fundus exam type", ["Indirect ophthalmoscopy","Fundus camera","Widefield","Other"], key="fundus_type")
        fundus_od = st.text_area("Fundus OD findings", height=120, key="fundus_od")
        fundus_os = st.text_area("Fundus OS findings", height=120, key="fundus_os")
        fundus_notes = st.text_area("Fundus notes", height=80, key="fundus_notes")
        oct_uploads = st.file_uploader("Upload OCT / fundus images (pdf/png/jpg)", type=['pdf','png','jpg','jpeg'], accept_multiple_files=True, key="oct_files")
        savep = st.form_submit_button("Save Posterior Segment & Continue")
        if savep:
            try:
                p = pd.read_sql("SELECT id FROM patients WHERE patient_id = ?", conn, params=(pid,)).iloc[0]
                file_paths = []
                if oct_uploads:
                    os.makedirs("uploads", exist_ok=True)
                    for f in oct_uploads:
                        safe_name = "".join(c for c in f.name if c.isalnum() or c in "._- ")
                        path = os.path.join("uploads", f"{datetime.now().timestamp()}_{safe_name}")
                        with open(path, "wb") as fp:
                            fp.write(f.getbuffer())
                        file_paths.append(path)
                c = conn.cursor()
                c.execute('''
                    INSERT INTO posterior_segment_exams (patient_id, fundus_exam_type, fundus_od, fundus_os, fundus_notes, uploaded_files)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (p['id'], fundus_type, fundus_od, fundus_os, fundus_notes, json.dumps(file_paths)))
                conn.commit()
                st.success("Posterior segment saved.")
                # instead of exiting to Dashboard — continue to Contact Lenses for fittings / follow-ups
                st.session_state.exam_step = "contact_lenses"
                st.rerun()
            except Exception as e:
                st.error(f"Database error: {str(e)}")

# Contact lenses module
def contact_lenses():
    st.subheader("Contact Lens Fitting & Prescription")
    if 'selected_patient' not in st.session_state or not st.session_state.selected_patient:
        st.info("Select a patient to begin contact lens fitting.")
        return
    pid = st.session_state.selected_patient
    with st.form("cl_form"):
        lens_type = st.selectbox("Lens type", ["Soft","RGP","Scleral","Custom"], key="lens_type")
        soft_brand = st.text_input("Soft brand (if applicable)", key="soft_brand")
        soft_base_curve = st.number_input("Soft base curve", value=0.0, step=0.1, key="soft_bc")
        soft_diameter = st.number_input("Soft diameter", value=0.0, step=0.1, key="soft_diam")
        soft_power_od = st.number_input("Soft power OD", value=0.0, step=0.25, key="soft_power_od")
        soft_power_os = st.number_input("Soft power OS", value=0.0, step=0.25, key="soft_power_os")
        wearing_schedule = st.text_input("Wearing schedule", key="wearing_sched")
        care_solution = st.text_input("Care solution", key="care_sol")
        follow_up = st.date_input("Follow-up date", value=date.today() + timedelta(days=30), key="follow_up")
        fitting_notes = st.text_area("Fitting notes", height=120, key="fitting_notes")
        savecl = st.form_submit_button("Save Contact Lens Prescription")
        if savecl:
            try:
                p = pd.read_sql("SELECT id FROM patients WHERE patient_id = ?", conn, params=(pid,)).iloc[0]
                c = conn.cursor()
                c.execute('''
                    INSERT INTO contact_lens_prescriptions (patient_id, lens_type, soft_brand, soft_base_curve, soft_diameter, soft_power_od, soft_power_os, wearing_schedule, care_solution, follow_up_date, fitting_notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (p['id'], lens_type, soft_brand, soft_base_curve, soft_diameter, soft_power_od, soft_power_os, wearing_schedule, care_solution, follow_up, fitting_notes))
                conn.commit()
                st.success("Contact lens prescription saved.")
                # remain on contact lens module for more entries or go to generate report
            except Exception as e:
                st.error(f"Database error: {str(e)}")

# Generate report (summary)
def generate_report():
    st.subheader("Generate Clinical Report")
    if 'selected_patient' not in st.session_state or not st.session_state.selected_patient:
        st.info("Select a patient to generate report.")
        return
    pid_code = st.session_state.selected_patient
    # simple summary from last refraction and patient details
    try:
        p = pd.read_sql("SELECT * FROM patients WHERE patient_id = ?", conn, params=(pid_code,)).iloc[0]
        st.markdown(f"### Report for {p['first_name']} {p['last_name']} (ID: {p['patient_id']})")
        ref = pd.read_sql("SELECT * FROM refraction_exams WHERE patient_id = (SELECT id FROM patients WHERE patient_id = ?) ORDER BY exam_date DESC LIMIT 1", conn, params=(pid_code,))
        if not ref.empty:
            r = ref.iloc[0].to_dict()
            st.markdown("**Latest Refraction Summary**")
            st.write({
                "Habitual OD VA": r.get('habitual_od_va'), "Habitual OS VA": r.get('habitual_os_va'),
                "Final OD": f"{r.get('final_prescribed_od_sphere')} {r.get('final_prescribed_od_cylinder')} x {r.get('final_prescribed_od_axis')}",
                "Final OS": f"{r.get('final_prescribed_os_sphere')} {r.get('final_prescribed_os_cylinder')} x {r.get('final_prescribed_os_axis')}" 
            })
        else:
            st.info("No refraction record found.")
        note = st.text_area("Add custom note for report", key="report_note")
        if st.button("Download Summary as txt", key="download_report"):
            contents = f"Report for {p['first_name']} {p['last_name']} ({p['patient_id']})\n\nNotes:\n{note}\n"
            st.download_button("Download", contents, file_name=f"report_{p['patient_id']}.txt")
    except Exception as e:
        st.error(f"Error generating report: {str(e)}")

# Patient registration - EU date format + earliest date 1900-01-01
def patient_registration():
    st.subheader("New Patient Registration")
    with st.form("reg_form"):
        c1, c2 = st.columns(2)
        with c1:
            patient_id = st.text_input("Patient ID (optional)", key="reg_patient_id")
            first_name = st.text_input("First Name*", placeholder="Given name", key="reg_first_name")
            last_name = st.text_input("Last Name*", placeholder="Family name", key="reg_last_name")
            # EU date format shown via format param, and min allowed date set to 1900-01-01
            date_of_birth = st.date_input("Date of Birth*", value=date(1990,1,1), min_value=date(1900,1,1), max_value=date.today(), format="DD.MM.YYYY", key="reg_dob")
            gender = st.selectbox("Gender", ["Male","Female","Other","Prefer not to say"], key="reg_gender")
        with c2:
            phone = st.text_input("Phone", key="reg_phone")
            email = st.text_input("Email", key="reg_email")
            address = st.text_area("Address", height=60, key="reg_address")
            id_number = st.text_input("ID / Passport", key="reg_id")
        with st.expander("Emergency & Insurance"):
            emergency_contact = st.text_input("Emergency contact", key="reg_emergency")
            insurance_info = st.text_input("Insurance info", key="reg_insurance")
        submit = st.form_submit_button("Register New Patient")
        if submit:
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
                    st.success(f"Patient registered. ID: {patient_id}")
                except sqlite3.IntegrityError:
                    st.error("Patient ID already exists.")
                except Exception as e:
                    st.error(f"Database error: {str(e)}")

# Patient search
def patient_search():
    st.subheader("Patient Search & Records")
    s1, s2 = st.columns([2,1])
    with s1:
        q = st.text_input("Search patients", placeholder="ID, name, phone, id#", key="search_query")
    with s2:
        stype = st.selectbox("Search by", ["All Fields","Patient ID","Name","Phone"], key="search_type")
    if q:
        try:
            if stype=="All Fields":
                df = pd.read_sql('SELECT * FROM patients WHERE patient_id LIKE ? OR first_name LIKE ? OR last_name LIKE ? OR phone LIKE ? OR id_number LIKE ? ORDER BY last_name, first_name', conn, params=(f'%{q}%',f'%{q}%',f'%{q}%',f'%{q}%',f'%{q}%'))
            elif stype=="Patient ID":
                df = pd.read_sql('SELECT * FROM patients WHERE patient_id LIKE ? ORDER BY patient_id', conn, params=(f'%{q}%',))
            elif stype=="Name":
                df = pd.read_sql('SELECT * FROM patients WHERE first_name LIKE ? OR last_name LIKE ? ORDER BY last_name, first_name', conn, params=(f'%{q}%',f'%{q}%'))
            else:
                df = pd.read_sql('SELECT * FROM patients WHERE phone LIKE ? ORDER BY last_name, first_name', conn, params=(f'%{q}%',))
            if df.empty:
                st.info("No patients found.")
            else:
                st.success(f"Found {len(df)}")
                for _, row in df.iterrows():
                    with st.expander(f"{row['patient_id']} - {row['first_name']} {row['last_name']}"):
                        c1, c2 = st.columns(2)
                        with c1:
                            st.write(f"**DOB:** {row['date_of_birth']}")
                            st.write(f"**Phone:** {row['phone']}")
                        with c2:
                            st.write(f"**Address:** {row['address']}")
                            st.write(f"**ID:** {row['id_number']}")
                        a1,a2,a3,a4 = st.columns(4)
                        with a1:
                            if st.button("Begin Examination", key=f"beg_{row['id']}"):
                                st.session_state.selected_patient = row['patient_id']
                                st.session_state.menu = "Examination Protocol"
                                st.session_state.exam_step = "medical_history"
                                st.rerun()
                        with a2:
                            if st.button("View History", key=f"hist_{row['id']}"):
                                st.session_state.selected_patient = row['patient_id']
                                st.session_state.menu = "Patient Search"
                                st.rerun()
                        with a3:
                            if st.button("Contact Lenses", key=f"cl_{row['id']}"):
                                st.session_state.selected_patient = row['patient_id']
                                st.session_state.menu = "Contact Lenses"
                                st.rerun()
                        with a4:
                            if st.button("Schedule", key=f"sch_{row['id']}"):
                                st.session_state.selected_patient = row['patient_id']
                                st.session_state.menu = "Schedule Appointment"
                                st.rerun()
        except Exception as e:
            st.error(f"Search error: {str(e)}")

# Navigation and main
def main_navigation():
    st.sidebar.title("OphtalCAM EMR")
    st.sidebar.markdown("---")
    if 'menu' not in st.session_state:
        st.session_state.menu = "Dashboard"
    if 'exam_step' not in st.session_state:
        st.session_state.exam_step = None
    menu_options = ["Dashboard","Patient Registration","Patient Search","Examination Protocol","Contact Lenses","Schedule Appointment","Clinical Analytics","Patient Groups","System Settings"]
    menu = st.sidebar.selectbox("Navigation", menu_options, index=menu_options.index(st.session_state.menu) if st.session_state.menu in menu_options else 0, key="nav_select")
    st.session_state.menu = menu

    if st.session_state.exam_step:
        st.sidebar.markdown("---")
        st.sidebar.subheader("Examination Protocol")
        steps = [("medical_history","1. Medical History"),("refraction","2. Refraction"),("functional_tests","3. Functional Tests"),("anterior_segment","4. Anterior Segment"),("posterior_segment","5. Posterior Segment"),("contact_lenses","6. Contact Lenses"),("generate_report","7. Clinical Report")]
        for step, label in steps:
            if step == st.session_state.exam_step:
                st.sidebar.markdown(f"**{label}**")
            else:
                st.sidebar.markdown(label)
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Clinician:** {st.session_state.get('username','')}")
    st.sidebar.markdown(f"**Role:** {st.session_state.get('role','')}")
    # Render pages
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
            st.info("Select a patient to begin examination.")
        elif menu == "Contact Lenses":
            contact_lenses()
        else:
            st.info("Module under construction.")

# Login page (no rocket emoji)
def login_page():
    st.markdown("<h3 style='text-align:center;'>Clinical Management System</h3>", unsafe_allow_html=True)
    col1, col2 = st.columns([3,1])
    with col1:
        st.image("https://i.postimg.cc/PrRFzQLv/Logo-Transparency-01.png", width=320)
    with col2:
        st.image("https://i.postimg.cc/qq656tks/Phantasmed-logo.png", width=180)
    st.markdown("---")
    with st.form("login_form"):
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        login = st.form_submit_button("Access Clinical System")
        if login:
            if username and password:
                user, msg = authenticate_user(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = user[0]
                    st.session_state.role = user[2]
                    st.success(f"Access granted. Welcome {user[0]}!")
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.error("Enter username and password")
    st.markdown("<div style='text-align:center; margin-top:10px;'><small>Demo: admin / admin123</small></div>", unsafe_allow_html=True)

# Main
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
        top1, top2, top3 = st.columns([3,1,1])
        with top1:
            st.image("https://i.postimg.cc/PrRFzQLv/Logo-Transparency-01.png", width=300)
        with top3:
            st.write(f"**Clinician:** {st.session_state.username}")
            st.write(f"**Role:** {st.session_state.role}")
            if st.button("Logout", key="logout_btn"):
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
