# app.py
# OphtalCAM / Ophtal-EMR (Modern navbar + Appointments + Refraction + Contact lenses + Reports)
# Updated per Toni's specs: EU dates, DOB >= 1900, habitual correction, subjective VA modifiers, pupilography moved to anterior, OphtalCAM placeholders, horizontal navbar, auto-migration

import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import os
import json
import calendar
from datetime import datetime, date, timedelta, time

# Page config
st.set_page_config(page_title="EMR", page_icon="👁️", layout="wide", initial_sidebar_state="collapsed")

# -------------------------
# Database: init + universal auto-migration helpers
# -------------------------
DB_PATH = "ophtalcam.db"

@st.cache_resource
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

def ensure_tables_and_columns():
    """
    Create base tables if not exists, then ensure missing columns (auto-migration).
    This covers: users, patients, medical_history, refraction_exams, functional_tests,
    anterior_segment_exams, posterior_segment_exams, contact_lens_prescriptions, appointments, patient_groups, assignments
    """
    conn = get_conn()
    c = conn.cursor()

    # --- base tables (CREATE IF NOT EXISTS) ---
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

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

            -- Uncorrected
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

            -- Subjective + VA modifiers
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

            -- additional
            binocular_tests TEXT,
            functional_tests TEXT,
            accommodation_tests TEXT,
            uploaded_files TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS functional_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            test_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            motility TEXT,
            hirschberg TEXT,
            npc_break TEXT,
            npc_recovery TEXT,
            npa TEXT,
            pupils TEXT,
            confrontation_fields TEXT,
            other_notes TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')

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

    # Ensure default admin
    try:
        admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)", ("admin", admin_hash, "admin"))
    except:
        pass

    # Auto-migration helper
    def add_columns_if_missing(table_name, columns_dict):
        try:
            c.execute(f"PRAGMA table_info({table_name})")
            existing = [r[1] for r in c.fetchall()]
            for col, coltype in columns_dict.items():
                if col not in existing:
                    try:
                        c.execute(f"ALTER TABLE {table_name} ADD COLUMN {col} {coltype}")
                    except Exception as e:
                        # ignore failures but print to console
                        print(f"Could not add column {col} to {table_name}: {e}")
        except Exception as e:
            print(f"PRAGMA error for {table_name}: {e}")

    # Example: ensure older DBs get these columns (comprehensive lists)
    add_columns_if_missing("patients", {
        "id_number":"TEXT","emergency_contact":"TEXT","insurance_info":"TEXT","gender":"TEXT","phone":"TEXT","email":"TEXT","address":"TEXT"
    })
    add_columns_if_missing("medical_history", {"uploaded_reports":"TEXT","visit_date":"TIMESTAMP"})
    add_columns_if_missing("refraction_exams", {
        "habitual_type":"TEXT","habitual_od_va":"TEXT","habitual_od_modifier":"TEXT","habitual_os_va":"TEXT","habitual_os_modifier":"TEXT",
        "habitual_binocular_va":"TEXT","habitual_binocular_modifier":"TEXT","habitual_pd":"TEXT","habitual_notes":"TEXT","vision_notes":"TEXT",
        "uncorrected_od_va":"TEXT","uncorrected_od_modifier":"TEXT","uncorrected_os_va":"TEXT","uncorrected_os_modifier":"TEXT",
        "uncorrected_binocular_va":"TEXT","uncorrected_binocular_modifier":"TEXT",
        "objective_method":"TEXT","objective_time":"TEXT","objective_notes":"TEXT",
        "cycloplegic_used":"BOOLEAN","cycloplegic_agent":"TEXT","cycloplegic_lot":"TEXT","cycloplegic_expiry":"DATE","cycloplegic_drops":"INTEGER",
        "subjective_method":"TEXT","subjective_od_va":"TEXT","subjective_od_modifier":"TEXT","subjective_os_va":"TEXT","subjective_os_modifier":"TEXT",
        "final_prescribed_binocular_va":"TEXT","final_prescribed_binocular_modifier":"TEXT","uploaded_files":"TEXT"
    })
    add_columns_if_missing("functional_tests", {
        "motility":"TEXT","hirschberg":"TEXT","npc_break":"TEXT","npc_recovery":"TEXT","npa":"TEXT","pupils":"TEXT","confrontation_fields":"TEXT","other_notes":"TEXT"
    })
    add_columns_if_missing("anterior_segment_exams", {
        "pupillography_results":"TEXT","pupillography_notes":"TEXT","pupillography_files":"TEXT","uploaded_files":"TEXT"
    })
    add_columns_if_missing("posterior_segment_exams", {
        "fundus_exam_type":"TEXT","fundus_od":"TEXT","fundus_os":"TEXT","fundus_notes":"TEXT","oct_notes":"TEXT","uploaded_files":"TEXT"
    })
    add_columns_if_missing("contact_lens_prescriptions", {"uploaded_files":"TEXT","follow_up_date":"DATE"})
    add_columns_if_missing("appointments", {"duration_minutes":"INTEGER","appointment_type":"TEXT","notes":"TEXT","status":"TEXT"})

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
    for g,d in default_groups:
        try:
            c.execute("INSERT OR IGNORE INTO patient_groups (group_name, description) VALUES (?, ?)", (g,d))
        except:
            pass

    conn.commit()

# ensure DB ready
ensure_tables_and_columns()
conn = get_conn()

# -------------------------
# Utilities
# -------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed

def authenticate_user(username, password):
    c = conn.cursor()
    c.execute("SELECT username, password_hash, role FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    if row and verify_password(password, row[1]):
        return {"username": row[0], "role": row[2]}
    return None

def format_eu_date(d):
    if not d:
        return ""
    if isinstance(d, str):
        return d
    return d.strftime("%d.%m.%Y")

def parse_eu_date(s):
    # attempt to parse dd.mm.yyyy
    try:
        return datetime.strptime(s, "%d.%m.%Y").date()
    except:
        return None

# -------------------------
# CSS + Navbar HTML
# -------------------------
def load_styles():
    st.markdown("""
    <style>
    /* Basic layout */
    .topbar { display:flex; align-items:center; justify-content:space-between; padding:10px 18px; background: linear-gradient(90deg,#0f3b5f,#1e5c8a); color:white; }
    .logo-left { display:flex; align-items:center; gap:10px; }
    .logo-left img { height:44px; }
    .brand { font-weight:700; font-size:18px; margin-left:6px; }
    .nav { display:flex; gap:8px; align-items:center; }
    .nav a { color: #f1f5f9; padding:8px 14px; border-radius:8px; text-decoration:none; font-weight:600; }
    .nav a.active { background: rgba(255,255,255,0.12); }
    .right-head { display:flex; gap:10px; align-items:center; }
    .user-chip { background: rgba(255,255,255,0.08); padding:6px 10px; border-radius:8px; }
    .content { padding:18px; }
    .small-muted { color:#6b7280; font-size:12px; }
    .card { background:white; padding:12px; border-radius:8px; box-shadow:0 1px 6px rgba(16,24,40,0.06); }
    .btn-opcam { background:#eef2ff; color:#1e40af; border-radius:8px; padding:6px 10px; border:1px solid #c7d2fe; }
    </style>
    """, unsafe_allow_html=True)

def navbar(selected="Dashboard"):
    # Render top navbar (HTML) and set page in session_state via JS-less links using query params or st.experimental_set_query_params
    pages = ["Dashboard","Appointments","Patients","Examinations","Contact Lenses","Reports","Settings"]
    # Build nav HTML with anchors that add query param ?page=Name
    query = st.experimental_get_query_params()
    cur = query.get("page", [selected])[0] if query else selected
    nav_html = f"""
    <div class='topbar'>
      <div class='logo-left'>
        <img src="https://i.postimg.cc/PrRFzQLv/Logo-Transparency-01.png" alt="logo"/>
        <div class='brand'>EMR</div>
      </div>
      <div class='nav'>
    """
    for p in pages:
        cls = "active" if p == cur else ""
        nav_html += f"<a class='{cls}' href='?page={p}'>{p}</a>"
    nav_html += "</div><div class='right-head'>"
    # user display
    if st.session_state.get("logged_in"):
        nav_html += f"<div class='user-chip'>{st.session_state.get('username','Clinician')}</div>"
        nav_html += f"<a style='color:white' href='?action=logout'>Logout</a>"
    else:
        nav_html += "<div class='user-chip'>Not signed in</div>"
    nav_html += "</div></div>"
    st.markdown(nav_html, unsafe_allow_html=True)

    # react to query params for page change or logout
    params = st.experimental_get_query_params()
    if "action" in params and params["action"][0] == "logout":
        # logout
        st.session_state.logged_in = False
        st.session_state.username = None
        st.experimental_set_query_params()
        st.experimental_rerun()
    page = params.get("page", [selected])[0]
    return page

# -------------------------
# Pages / Modules
# -------------------------

# --- Dashboard ---
def get_patient_stats():
    try:
        total_patients = pd.read_sql("SELECT COUNT(*) as cnt FROM patients", conn).iloc[0]['cnt']
    except:
        total_patients = 0
    try:
        total_appts = pd.read_sql("SELECT COUNT(*) as cnt FROM appointments", conn).iloc[0]['cnt']
    except:
        total_appts = 0
    try:
        total_cl = pd.read_sql("SELECT COUNT(*) as cnt FROM contact_lens_prescriptions", conn).iloc[0]['cnt']
    except:
        total_cl = 0
    return total_patients, total_appts, total_cl

def dashboard_page():
    st.markdown("<div class='content'>", unsafe_allow_html=True)
    st.markdown("<h2>Dashboard</h2>", unsafe_allow_html=True)
    t1,t2,t3 = st.columns(3)
    total_patients, total_appts, total_cl = get_patient_stats()
    t1.markdown(f"<div class='card'><strong>{total_patients}</strong><div class='small-muted'>Registered patients</div></div>", unsafe_allow_html=True)
    t2.markdown(f"<div class='card'><strong>{total_appts}</strong><div class='small-muted'>Total appointments</div></div>", unsafe_allow_html=True)
    t3.markdown(f"<div class='card'><strong>{total_cl}</strong><div class='small-muted'>Contact lens records</div></div>", unsafe_allow_html=True)

    st.markdown("<h4 style='margin-top:18px'>Today's Schedule</h4>", unsafe_allow_html=True)
    # filter: Today / Week / Month
    view = st.selectbox("View", ["Today","This Week","This Month"], index=0, key="dashboard_view")
    now = datetime.now()
    if view == "Today":
        start = datetime(now.year, now.month, now.day)
        end = start + timedelta(days=1)
    elif view == "This Week":
        start = datetime(now.year, now.month, now.day) - timedelta(days=now.weekday())
        end = start + timedelta(days=7)
    else:
        start = datetime(now.year, now.month, 1)
        # naive month end
        if now.month == 12:
            end = datetime(now.year+1,1,1)
        else:
            end = datetime(now.year, now.month+1, 1)

    try:
        appts = pd.read_sql("SELECT a.*, p.first_name, p.last_name, p.patient_id FROM appointments a JOIN patients p ON a.patient_id = p.id WHERE a.appointment_date >= ? AND a.appointment_date < ? ORDER BY a.appointment_date", conn, params=(start, end))
    except Exception as e:
        st.error(f"Database error loading appointments: {e}")
        appts = pd.DataFrame()

    if appts.empty:
        st.info("No appointments in selected period.")
    else:
        for _, row in appts.iterrows():
            col1, col2, col3 = st.columns([1,4,1])
            col1.markdown(f"<div class='card'><strong>{pd.to_datetime(row['appointment_date']).strftime('%d.%m %H:%M')}</strong></div>", unsafe_allow_html=True)
            col2.markdown(f"<div class='card'><strong>{row['first_name']} {row['last_name']} ({row['patient_id']})</strong><div class='small-muted'>{row['appointment_type'] or 'Exam'}</div></div>", unsafe_allow_html=True)
            with col3:
                if st.button("Begin", key=f"begin_{row['id']}"):
                    st.experimental_set_query_params(page="Examinations")
                    st.session_state.selected_patient = row['patient_id']
                    st.session_state.exam_step = "medical_history"
                    st.experimental_rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# --- Appointments tab ---
def appointments_page():
    st.markdown("<div class='content'>", unsafe_allow_html=True)
    st.markdown("<h2>Appointments</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns([2,1])
    with col1:
        st.markdown("### Create new appointment")
        with st.form("new_appointment_form"):
            # choose patient by search or create inline simple selector
            q = st.text_input("Search patient (ID, name, phone) - leave blank to create new")
            selected_pid = None
            matches = []
            if q:
                try:
                    matches = pd.read_sql("SELECT id, patient_id, first_name, last_name FROM patients WHERE patient_id LIKE ? OR first_name LIKE ? OR last_name LIKE ? OR phone LIKE ? LIMIT 20", conn, params=(f'%{q}%',f'%{q}%',f'%{q}%',f'%{q}%'))
                except:
                    matches = []
            if matches and len(matches)>0:
                options = [f"{r['patient_id']} - {r['first_name']} {r['last_name']}" for _, r in matches.iterrows()]
                sel = st.selectbox("Select patient from results", options)
                idx = options.index(sel)
                selected_pid = matches.iloc[idx]['patient_id']
            else:
                st.info("No matching patient or leave blank to register new patient below")
            # quick create minimal new patient inline
            if not selected_pid:
                st.markdown("**Or register new patient (minimal)**")
                np_first = st.text_input("First name (new)")
                np_last = st.text_input("Last name (new)")
                np_dob = st.date_input("Date of birth (new)", value=date(1990,1,1), min_value=date(1900,1,1), max_value=date.today(), format="%d.%m.%Y")
                np_gender = st.selectbox("Gender (new)", ["Male","Female","Other","Prefer not to say"])
            appt_date = st.date_input("Appointment date", value=date.today())
            appt_time = st.time_input("Appointment time", value=time(hour=9, minute=0))
            appt_dt = datetime.combine(appt_date, appt_time)
            appt_type = st.selectbox("Appointment type", ["Full exam","Control","Contact lens fitting","OCT","Fundus photo","Other"])
            appt_notes = st.text_area("Notes", height=80)
            submit = st.form_submit_button("Save appointment")
            if submit:
                try:
                    cursor = conn.cursor()
                    if not selected_pid:
                        # create patient
                        if not np_first or not np_last:
                            st.error("Please enter new patient first & last name")
                        else:
                            new_pid = f"PAT{int(datetime.now().timestamp())}"
                            cursor.execute('INSERT INTO patients (patient_id, first_name, last_name, date_of_birth, gender) VALUES (?,?,?,?,?)',
                                           (new_pid, np_first, np_last, np_dob, np_gender))
                            conn.commit()
                            selected_pid = new_pid
                    # get internal patient id
                    p = pd.read_sql("SELECT id FROM patients WHERE patient_id = ?", conn, params=(selected_pid,)).iloc[0]
                    cursor.execute('INSERT INTO appointments (patient_id, appointment_date, appointment_type, notes, status) VALUES (?, ?, ?, ?, ?)',
                                   (p['id'], appt_dt, appt_type, appt_notes, "Scheduled"))
                    conn.commit()
                    st.success("Appointment saved.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Database error saving appointment: {e}")

    with col2:
        st.markdown("### Upcoming")
        try:
            upcoming = pd.read_sql("SELECT a.*, p.first_name, p.last_name, p.patient_id FROM appointments a JOIN patients p ON a.patient_id = p.id WHERE a.appointment_date >= ? ORDER BY a.appointment_date LIMIT 20", conn, params=(datetime.now(),))
        except Exception as e:
            st.error(f"Error loading upcoming: {e}")
            upcoming = pd.DataFrame()
        if upcoming.empty:
            st.info("No upcoming appointments.")
        else:
            for _, row in upcoming.iterrows():
                st.markdown(f"**{pd.to_datetime(row['appointment_date']).strftime('%d.%m %H:%M')}** — {row['first_name']} {row['last_name']} ({row['patient_id']})")
                colA, colB, colC = st.columns([1,1,1])
                with colA:
                    if st.button("View", key=f"view_appt_{row['id']}"):
                        st.experimental_set_query_params(page="Appointments", appt=str(row['id']))
                        st.experimental_rerun()
                with colB:
                    if st.button("Mark done", key=f"done_appt_{row['id']}"):
                        try:
                            cur = conn.cursor()
                            cur.execute("UPDATE appointments SET status = 'Completed' WHERE id = ?", (row['id'],))
                            conn.commit()
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Could not update: {e}")
                with colC:
                    if st.button("Cancel", key=f"cancel_appt_{row['id']}"):
                        try:
                            cur = conn.cursor()
                            cur.execute("UPDATE appointments SET status = 'Cancelled' WHERE id = ?", (row['id'],))
                            conn.commit()
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Could not cancel: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

# --- Patients: registration & search (separate page) ---
def patients_page():
    st.markdown("<div class='content'>", unsafe_allow_html=True)
    st.markdown("<h2>Patients</h2>", unsafe_allow_html=True)
    tab = st.tabs(["Register","Search & Records"])
    # Register
    with tab[0]:
        with st.form("reg_form_full"):
            c1, c2 = st.columns(2)
            with c1:
                patient_id = st.text_input("Patient ID (optional)")
                first_name = st.text_input("First name *")
                last_name = st.text_input("Last name *")
                dob = st.date_input("Date of birth *", value=date(1990,1,1), min_value=date(1900,1,1), max_value=date.today(), format="%d.%m.%Y")
                gender = st.selectbox("Gender", ["Male","Female","Other","Prefer not to say"])
            with c2:
                phone = st.text_input("Phone")
                email = st.text_input("Email")
                address = st.text_area("Address", height=80)
                id_number = st.text_input("ID / Passport")
            with st.expander("Emergency & Insurance"):
                emergency_contact = st.text_input("Emergency contact")
                insurance_info = st.text_input("Insurance")
            submit = st.form_submit_button("Register patient")
            if submit:
                if not first_name or not last_name or not dob:
                    st.error("First name, last name and DOB required")
                else:
                    try:
                        if not patient_id:
                            patient_id = f"PAT{int(datetime.now().timestamp())}"
                        cur = conn.cursor()
                        cur.execute('INSERT INTO patients (patient_id, first_name, last_name, date_of_birth, gender, phone, email, address, id_number, emergency_contact, insurance_info) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                                   (patient_id, first_name, last_name, dob, gender, phone, email, address, id_number, emergency_contact, insurance_info))
                        conn.commit()
                        st.success(f"Patient {first_name} {last_name} registered. ID: {patient_id}")
                    except Exception as e:
                        st.error(f"Database error: {e}")

    # Search & records
    with tab[1]:
        q = st.text_input("Search patients (ID, name, phone, id#)")
        st.write("")
        if q:
            try:
                df = pd.read_sql("SELECT * FROM patients WHERE patient_id LIKE ? OR first_name LIKE ? OR last_name LIKE ? OR phone LIKE ? OR id_number LIKE ? ORDER BY last_name, first_name", conn, params=(f'%{q}%',f'%{q}%',f'%{q}%',f'%{q}%',f'%{q}%'))
            except Exception as e:
                st.error(f"Search DB error: {e}")
                df = pd.DataFrame()
            if df.empty:
                st.info("No results")
            else:
                for _, r in df.iterrows():
                    exp = st.expander(f"{r['patient_id']} — {r['first_name']} {r['last_name']}")
                    with exp:
                        st.write(f"**DOB:** {format_eu_date(r['date_of_birth'])}")
                        st.write(f"**Phone:** {r.get('phone','')}")
                        st.write(f"**Address:** {r.get('address','')}")
                        cols = st.columns(4)
                        with cols[0]:
                            if st.button("Begin exam", key=f"beginpt_{r['id']}"):
                                st.experimental_set_query_params(page="Examinations")
                                st.session_state.selected_patient = r['patient_id']
                                st.session_state.exam_step = "medical_history"
                                st.experimental_rerun()
                        with cols[1]:
                            if st.button("Contact lenses", key=f"pt_cl_{r['id']}"):
                                st.experimental_set_query_params(page="Contact Lenses")
                                st.session_state.selected_patient = r['patient_id']
                                st.experimental_rerun()
                        with cols[2]:
                            if st.button("Appointments", key=f"pt_ap_{r['id']}"):
                                st.experimental_set_query_params(page="Appointments")
                                st.session_state.selected_patient = r['patient_id']
                                st.experimental_rerun()
                        with cols[3]:
                            if st.button("Generate report", key=f"pt_rep_{r['id']}"):
                                st.experimental_set_query_params(page="Reports")
                                st.session_state.selected_patient = r['patient_id']
                                st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- Examinations page: workflow with steps --- (medical_history -> refraction -> functional -> anterior -> posterior -> contact_lenses -> reports)
def examinations_page():
    st.markdown("<div class='content'>", unsafe_allow_html=True)
    st.markdown("<h2>Examinations</h2>", unsafe_allow_html=True)

    if 'selected_patient' not in st.session_state or not st.session_state.selected_patient:
        st.info("Select a patient from Patients or Dashboard to begin an examination.")
        return

    pid = st.session_state.selected_patient
    # load patient basic
    try:
        p = pd.read_sql("SELECT * FROM patients WHERE patient_id = ?", conn, params=(pid,)).iloc[0]
    except:
        st.error("Patient not found.")
        return

    st.markdown(f"### {p['first_name']} {p['last_name']} — {p['patient_id']}")
    # steps bar
    steps = ["medical_history","refraction","functional_tests","anterior_segment","posterior_segment","contact_lenses","reports"]
    if 'exam_step' not in st.session_state or not st.session_state.exam_step:
        st.session_state.exam_step = "medical_history"

    # small nav for steps
    step_cols = st.columns(len(steps))
    for i, s in enumerate(steps):
        label = s.replace("_"," ").title()
        if s == st.session_state.exam_step:
            step_cols[i].button(label, key=f"step_active_{s}")
        else:
            if step_cols[i].button(label, key=f"step_goto_{s}"):
                st.session_state.exam_step = s
                st.experimental_rerun()

    # Render current step
    if st.session_state.exam_step == "medical_history":
        render_medical_history_for_patient(p)
    elif st.session_state.exam_step == "refraction":
        render_refraction_for_patient(p)
    elif st.session_state.exam_step == "functional_tests":
        render_functional_for_patient(p)
    elif st.session_state.exam_step == "anterior_segment":
        render_anterior_for_patient(p)
    elif st.session_state.exam_step == "posterior_segment":
        render_posterior_for_patient(p)
    elif st.session_state.exam_step == "contact_lenses":
        st.experimental_set_query_params(page="Contact Lenses")
        st.experimental_rerun()
    elif st.session_state.exam_step == "reports":
        st.experimental_set_query_params(page="Reports")
        st.experimental_rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# --- Medical history renderer (for a single patient) ---
def render_medical_history_for_patient(pinfo):
    st.markdown("#### Medical History")
    with st.form("mh_form_patient"):
        col1, col2 = st.columns(2)
        with col1:
            general_health = st.text_area("General health", height=120)
            current_medications = st.text_area("Current medications", height=100)
            allergies = st.text_area("Allergies", height=80)
        with col2:
            headaches = st.text_area("Headaches / Migraines", height=120)
            family_history = st.text_area("Family history", height=100)
            ocular_history = st.text_area("Ocular history", height=80)
        uploaded = st.file_uploader("Upload previous reports", type=['pdf','jpg','png'], accept_multiple_files=True)
        submitted = st.form_submit_button("Save medical history")
        if submitted:
            try:
                files = []
                if uploaded:
                    os.makedirs("uploads", exist_ok=True)
                    for f in uploaded:
                        path = os.path.join("uploads", f"{datetime.now().timestamp()}_{f.name}")
                        with open(path, "wb") as fp:
                            fp.write(f.getbuffer())
                        files.append(path)
                cur = conn.cursor()
                cur.execute('INSERT INTO medical_history (patient_id, general_health, current_medications, allergies, headaches_history, family_history, ocular_history, uploaded_reports) VALUES (?,?,?,?,?,?,?,?)',
                            (pinfo['id'], general_health, current_medications, allergies, headaches, family_history, ocular_history, json.dumps(files)))
                conn.commit()
                st.success("Medical history saved.")
                st.session_state.exam_step = "refraction"
                st.experimental_rerun()
            except Exception as e:
                st.error(f"DB error saving medical history: {e}")

# --- Refraction renderer (for a single patient) ---
def render_refraction_for_patient(pinfo):
    st.markdown("#### Refraction & Vision")
    if 'refraction' not in st.session_state:
        st.session_state.refraction = {}

    # Habitual + uncorrected (free text VA fields + small modifier)
    with st.form("refraction_vision"):
        left, right = st.columns([2,2])
        with left:
            st.markdown("**Habitual Correction**")
            habitual_type = st.selectbox("Type", ["None","Spectacles","Soft Contact Lenses","RGP","Scleral","Ortho-K","Other"], key="habit_h_type")
            hcols = st.columns([1,1,1])
            with hcols[0]:
                habitual_od_va = st.text_input("Habitual VA OD", placeholder="e.g. 1.0 or 20/20")
                habitual_od_modifier = st.text_input("Modifier OD", placeholder="-2")
            with hcols[1]:
                habitual_os_va = st.text_input("Habitual VA OS", placeholder="e.g. 1.0 or 20/20")
                habitual_os_modifier = st.text_input("Modifier OS", placeholder="-2")
            with hcols[2]:
                habitual_binocular_va = st.text_input("Habitual Binocular VA", placeholder="1.0 or 20/20")
                habitual_binocular_modifier = st.text_input("Modifier OU", placeholder="-2")
            habitual_pd = st.text_input("PD (mm)", placeholder="e.g. 62")
            habitual_notes = st.text_area("Notes (habitual)", height=80)
        with right:
            st.markdown("**Uncorrected Vision**")
            ucols = st.columns([1,1])
            with ucols[0]:
                uncorrected_od_va = st.text_input("Uncorrected VA OD")
                uncorrected_od_modifier = st.text_input("Unc. modifier OD", placeholder="-2")
            with ucols[1]:
                uncorrected_os_va = st.text_input("Uncorrected VA OS")
                uncorrected_os_modifier = st.text_input("Unc. modifier OS", placeholder="-2")
            uncorrected_bin_va = st.text_input("Uncorrected binocular VA")
            uncorrected_bin_modifier = st.text_input("Unc binocular modifier", placeholder="-2")
            vision_notes = st.text_area("Vision notes", height=120)

        savev = st.form_submit_button("Save vision")
        if savev:
            st.session_state.refraction.update({
                'habitual_type': habitual_type,
                'habitual_od_va': habitual_od_va,
                'habitual_od_modifier': habitual_od_modifier,
                'habitual_os_va': habitual_os_va,
                'habitual_os_modifier': habitual_os_modifier,
                'habitual_binocular_va': habitual_binocular_va,
                'habitual_binocular_modifier': habitual_binocular_modifier,
                'habitual_pd': habitual_pd,
                'habitual_notes': habitual_notes,
                'uncorrected_od_va': uncorrected_od_va,
                'uncorrected_od_modifier': uncorrected_od_modifier,
                'uncorrected_os_va': uncorrected_os_va,
                'uncorrected_os_modifier': uncorrected_os_modifier,
                'uncorrected_binocular_va': uncorrected_bin_va,
                'uncorrected_binocular_modifier': uncorrected_bin_modifier,
                'vision_notes': vision_notes
            })
            st.success("Vision saved (session).")
            st.experimental_rerun()

    st.markdown("---")
    # Objective
    with st.form("refraction_objective"):
        st.markdown("**Objective refraction**")
        topc, topr = st.columns([2,1])
        with topc:
            objective_method = st.selectbox("Method", ["Autorefractor","Retinoscopy","Other"], key="obj_method")
        with topr:
            objective_time = st.time_input("Time", value=datetime.now().time())
        odc, spacer, osc = st.columns([2,0.15,2])
        with odc:
            st.markdown("Right eye (OD)")
            autorefractor_od_sphere = st.number_input("Sphere OD", value=0.0, step=0.25, format="%.2f", key="od_sph")
            autorefractor_od_cylinder = st.number_input("Cylinder OD", value=0.0, step=0.25, format="%.2f", key="od_cyl")
            autorefractor_od_axis = st.number_input("Axis OD", value=0, min_value=0, max_value=180, key="od_ax")
        with osc:
            st.markdown("Left eye (OS)")
            autorefractor_os_sphere = st.number_input("Sphere OS", value=0.0, step=0.25, format="%.2f", key="os_sph")
            autorefractor_os_cylinder = st.number_input("Cylinder OS", value=0.0, step=0.25, format="%.2f", key="os_cyl")
            autorefractor_os_axis = st.number_input("Axis OS", value=0, min_value=0, max_value=180, key="os_ax")
        objective_notes = st.text_area("Objective notes", height=100)
        saveo = st.form_submit_button("Save objective")
        if saveo:
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
            st.success("Objective saved (session).")
            st.experimental_rerun()

    st.markdown("---")
    # Cycloplegic & subjective
    with st.form("refraction_subjective"):
        st.markdown("**Cycloplegic & Subjective**")
        subj_method = st.selectbox("Subjective method", ["Fogging","With Cycloplegic","Other"])
        cyclo_used = (subj_method == "With Cycloplegic")
        if cyclo_used:
            c1,c2,c3,c4 = st.columns([1,1,1,1])
            with c1:
                cyclo_agent = st.text_input("Agent", placeholder="Cyclopentolate 1%")
            with c2:
                cyclo_lot = st.text_input("Lot #")
            with c3:
                cyclo_expiry = st.date_input("Expiry", value=date.today())
            with c4:
                cyclo_drops = st.number_input("Drops",
0, step=1)
            st.markdown("##### Subjective Refraction")
            scols = st.columns([2,0.2,2])
            with scols[0]:
                st.markdown("Right Eye (OD)")
                subj_od_sphere = st.number_input("Sphere OD (subj)", value=0.0, step=0.25)
                subj_od_cylinder = st.number_input("Cylinder OD (subj)", value=0.0, step=0.25)
                subj_od_axis = st.number_input("Axis OD (subj)", value=0, min_value=0, max_value=180)
                subj_od_va = st.text_input("VA OD", placeholder="1.0")
                subj_od_mod = st.text_input("Modifier OD", placeholder="-2")
            with scols[2]:
                st.markdown("Left Eye (OS)")
                subj_os_sphere = st.number_input("Sphere OS (subj)", value=0.0, step=0.25)
                subj_os_cylinder = st.number_input("Cylinder OS (subj)", value=0.0, step=0.25)
                subj_os_axis = st.number_input("Axis OS (subj)", value=0, min_value=0, max_value=180)
                subj_os_va = st.text_input("VA OS", placeholder="1.0")
                subj_os_mod = st.text_input("Modifier OS", placeholder="-2")
            subj_notes = st.text_area("Subjective notes", height=100)
            save_subj = st.form_submit_button("Save subjective")
            if save_subj:
                st.session_state.refraction.update({
                    'subjective_method': subj_method,
                    'cycloplegic_used': cyclo_used,
                    'cycloplegic_agent': cyclo_agent if cyclo_used else None,
                    'cycloplegic_lot': cyclo_lot if cyclo_used else None,
                    'cycloplegic_expiry': cyclo_expiry if cyclo_used else None,
                    'cycloplegic_drops': cyclo_drops if cyclo_used else None,
                    'subjective_od_sphere': subj_od_sphere,
                    'subjective_od_cylinder': subj_od_cylinder,
                    'subjective_od_axis': subj_od_axis,
                    'subjective_od_va': subj_od_va,
                    'subjective_od_modifier': subj_od_mod,
                    'subjective_os_sphere': subj_os_sphere,
                    'subjective_os_cylinder': subj_os_cylinder,
                    'subjective_os_axis': subj_os_axis,
                    'subjective_os_va': subj_os_va,
                    'subjective_os_modifier': subj_os_mod,
                    'subjective_notes': subj_notes
                })
                st.success("Subjective saved (session).")
                st.experimental_rerun()

    st.markdown("---")
    # Final prescription
    with st.form("refraction_final"):
        st.markdown("**Final Prescription**")
        fcols = st.columns([2,0.2,2])
        with fcols[0]:
            st.markdown("Right Eye (OD)")
            final_od_sphere = st.number_input("Final Sphere OD", value=0.0, step=0.25)
            final_od_cylinder = st.number_input("Final Cylinder OD", value=0.0, step=0.25)
            final_od_axis = st.number_input("Final Axis OD", value=0, min_value=0, max_value=180)
        with fcols[2]:
            st.markdown("Left Eye (OS)")
            final_os_sphere = st.number_input("Final Sphere OS", value=0.0, step=0.25)
            final_os_cylinder = st.number_input("Final Cylinder OS", value=0.0, step=0.25)
            final_os_axis = st.number_input("Final Axis OS", value=0, min_value=0, max_value=180)
        bin_va = st.text_input("Binocular VA")
        bin_mod = st.text_input("Binocular modifier", placeholder="-2")
        bvp = st.text_input("BVP / Add / Comments")
        pinhole = st.text_input("Pinhole VA")
        presc_notes = st.text_area("Prescription notes", height=100)
        finalize = st.form_submit_button("Finalize prescription & save to DB")
        if finalize:
            try:
                ref = st.session_state.refraction
                cur = conn.cursor()
                cur.execute('''
                    INSERT INTO refraction_exams (
                        patient_id, exam_date,
                        habitual_type, habitual_od_va, habitual_od_modifier, habitual_os_va, habitual_os_modifier,
                        habitual_binocular_va, habitual_binocular_modifier, habitual_pd, habitual_notes, vision_notes,
                        uncorrected_od_va, uncorrected_od_modifier, uncorrected_os_va, uncorrected_os_modifier,
                        uncorrected_binocular_va, uncorrected_binocular_modifier,
                        objective_method, objective_time, autorefractor_od_sphere, autorefractor_od_cylinder, autorefractor_od_axis,
                        autorefractor_os_sphere, autorefractor_os_cylinder, autorefractor_os_axis, objective_notes,
                        subjective_method, cycloplegic_used, cycloplegic_agent, cycloplegic_lot, cycloplegic_expiry, cycloplegic_drops,
                        subjective_od_sphere, subjective_od_cylinder, subjective_od_axis, subjective_od_va, subjective_od_modifier,
                        subjective_os_sphere, subjective_os_cylinder, subjective_os_axis, subjective_os_va, subjective_os_modifier,
                        subjective_notes, final_prescribed_od_sphere, final_prescribed_od_cylinder, final_prescribed_od_axis,
                        final_prescribed_os_sphere, final_prescribed_os_cylinder, final_prescribed_os_axis,
                        final_prescribed_binocular_va, final_prescribed_binocular_modifier, bvp, pinhole, prescription_notes
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ''', (
                    pinfo['id'], datetime.now(),
                    ref.get('habitual_type'), ref.get('habitual_od_va'), ref.get('habitual_od_modifier'), ref.get('habitual_os_va'), ref.get('habitual_os_modifier'),
                    ref.get('habitual_binocular_va'), ref.get('habitual_binocular_modifier'), ref.get('habitual_pd'), ref.get('habitual_notes'), ref.get('vision_notes'),
                    ref.get('uncorrected_od_va'), ref.get('uncorrected_od_modifier'), ref.get('uncorrected_os_va'), ref.get('uncorrected_os_modifier'),
                    ref.get('uncorrected_binocular_va'), ref.get('uncorrected_binocular_modifier'),
                    ref.get('objective_method'), ref.get('objective_time'),
                    ref.get('autorefractor_od_sphere'), ref.get('autorefractor_od_cylinder'), ref.get('autorefractor_od_axis'),
                    ref.get('autorefractor_os_sphere'), ref.get('autorefractor_os_cylinder'), ref.get('autorefractor_os_axis'),
                    ref.get('objective_notes'),
                    ref.get('subjective_method'), ref.get('cycloplegic_used'), ref.get('cycloplegic_agent'), ref.get('cycloplegic_lot'), ref.get('cycloplegic_expiry'), ref.get('cycloplegic_drops'),
                    ref.get('subjective_od_sphere'), ref.get('subjective_od_cylinder'), ref.get('subjective_od_axis'), ref.get('subjective_od_va'), ref.get('subjective_od_modifier'),
                    ref.get('subjective_os_sphere'), ref.get('subjective_os_cylinder'), ref.get('subjective_os_axis'), ref.get('subjective_os_va'), ref.get('subjective_os_modifier'),
                    ref.get('subjective_notes'),
                    final_od_sphere, final_od_cylinder, final_od_axis,
                    final_os_sphere, final_os_cylinder, final_os_axis,
                    bin_va, bin_mod, bvp, pinhole, presc_notes
                ))
                conn.commit()
                st.success("Refraction saved to database.")
                st.session_state.exam_step = "functional_tests"
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Database error when saving refraction: {e}")

# --- Functional Tests ---
def render_functional_for_patient(pinfo):
    st.markdown("#### Functional & Binocular Tests")
    with st.form("functional_tests_form"):
        motility = st.text_area("Motility", height=80)
        st.button("🔹 Pokreni OphtalCAM device", key="motility_cam", disabled=True)
        hirschberg = st.text_input("Hirschberg test")
        st.button("🔹 Pokreni OphtalCAM device", key="hirsch_cam", disabled=True)
        npc_break = st.text_input("NPC Break (cm)")
        npc_recovery = st.text_input("NPC Recovery (cm)")
        st.button("🔹 Pokreni OphtalCAM device", key="npc_cam", disabled=True)
        npa = st.text_input("NPA (cm)")
        st.button("🔹 Pokreni OphtalCAM device", key="npa_cam", disabled=True)
        pupils = st.text_input("Pupils response")
        st.button("🔹 Pokreni OphtalCAM device", key="pupil_cam", disabled=True)
        conf_field = st.text_area("Confrontation visual fields", height=80)
        notes = st.text_area("Notes", height=80)
        submit = st.form_submit_button("Save functional tests")
        if submit:
            try:
                cur = conn.cursor()
                cur.execute('INSERT INTO functional_tests (patient_id, motility, hirschberg, npc_break, npc_recovery, npa, pupils, confrontation_fields, other_notes) VALUES (?,?,?,?,?,?,?,?,?)',
                            (pinfo['id'], motility, hirschberg, npc_break, npc_recovery, npa, pupils, conf_field, notes))
                conn.commit()
                st.success("Functional tests saved.")
                st.session_state.exam_step = "anterior_segment"
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Database error: {e}")

# --- Anterior Segment ---
def render_anterior_for_patient(pinfo):
    st.markdown("#### Anterior Segment Examination")
    with st.form("anterior_form"):
        st.markdown("**Biomicroscopy**")
        bioc = st.columns([2,2])
        with bioc[0]:
            bio_od = st.text_area("OD Findings", height=100)
        with bioc[1]:
            bio_os = st.text_area("OS Findings", height=100)
        st.button("🔹 Pokreni OphtalCAM device", key="bio_cam", disabled=True)
        bio_notes = st.text_area("Notes (biomicroscopy)", height=60)

        st.markdown("**Anterior Chamber**")
        acc = st.columns([2,2])
        with acc[0]:
            ac_depth_od = st.text_input("AC Depth OD")
            ac_volume_od = st.text_input("AC Volume OD")
            ic_angle_od = st.text_input("IridoCorneal angle OD")
        with acc[1]:
            ac_depth_os = st.text_input("AC Depth OS")
            ac_volume_os = st.text_input("AC Volume OS")
            ic_angle_os = st.text_input("IridoCorneal angle OS")
        st.button("🔹 Pokreni OphtalCAM device", key="ac_cam", disabled=True)

        pachy_od = st.number_input("Pachymetry OD (µm)", value=530)
        pachy_os = st.number_input("Pachymetry OS (µm)", value=530)
        tono_type = st.text_input("Tonometry type")
        tono_time = st.time_input("Tonometry time", value=datetime.now().time())
        tono_od = st.text_input("Tonometry OD")
        tono_os = st.text_input("Tonometry OS")
        tono_comp = st.text_input("Tonometry compensation")
        aber_notes = st.text_area("Aberrometry notes", height=80)
        topo_notes = st.text_area("Corneal topography notes", height=80)
        # Pupilography moved here
        st.markdown("**Pupilography**")
        pupil_res = st.text_area("Pupilography results", height=80)
        pupil_notes = st.text_area("Pupilography notes", height=80)
        pupil_files = st.file_uploader("Upload pupilography results", type=["jpg","png","pdf"], accept_multiple_files=True)
        st.button("🔹 Pokreni OphtalCAM device", key="pupilography_cam", disabled=True)

        notes = st.text_area("Additional anterior notes", height=80)
        savea = st.form_submit_button("Save anterior segment")
        if savea:
            try:
                files = []
                if pupil_files:
                    os.makedirs("uploads", exist_ok=True)
                    for f in pupil_files:
                        path = os.path.join("uploads", f"{datetime.now().timestamp()}_{f.name}")
                        with open(path,"wb") as fp: fp.write(f.getbuffer())
                        files.append(path)
                cur = conn.cursor()
                cur.execute('INSERT INTO anterior_segment_exams (patient_id, biomicroscopy_od, biomicroscopy_os, biomicroscopy_notes, anterior_chamber_depth_od, anterior_chamber_depth_os, anterior_chamber_volume_od, anterior_chamber_volume_os, iridocorneal_angle_od, iridocorneal_angle_os, pachymetry_od, pachymetry_os, tonometry_type, tonometry_time, tonometry_od, tonometry_os, tonometry_compensation, aberometry_notes, corneal_topography_notes, pupillography_results, pupillography_notes, pupillography_files, anterior_segment_notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                            (pinfo['id'], bio_od, bio_os, bio_notes, ac_depth_od, ac_depth_os, ac_volume_od, ac_volume_os, ic_angle_od, ic_angle_os, pachy_od, pachy_os, tono_type, tono_time.strftime("%H:%M"), tono_od, tono_os, tono_comp, aber_notes, topo_notes, pupil_res, pupil_notes, json.dumps(files), notes))
                conn.commit()
                st.success("Anterior segment saved.")
                st.session_state.exam_step = "posterior_segment"
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Database error: {e}")
# --- Posterior Segment ---
def render_posterior_for_patient(pinfo):
    st.markdown("#### Posterior Segment Examination")
    with st.form("posterior_form"):
        fundus_type = st.selectbox("Fundus exam type", ["Direct", "Indirect", "Slit lamp", "Photo upload"])
        fundus_od = st.text_area("Fundus OD", height=80)
        fundus_os = st.text_area("Fundus OS", height=80)
        fundus_notes = st.text_area("Fundus notes", height=80)
        st.button("🔹 Pokreni OphtalCAM device", key="fundus_cam", disabled=True)

        oct_files = st.file_uploader("Upload OCT / Fundus images", type=["jpg","png","pdf"], accept_multiple_files=True)
        oct_notes = st.text_area("OCT notes", height=80)
        post_notes = st.text_area("Additional posterior notes", height=80)
        st.button("🔹 Pokreni OphtalCAM device", key="posterior_cam", disabled=True)

        savep = st.form_submit_button("Save posterior segment")
        if savep:
            try:
                uploads = []
                if oct_files:
                    os.makedirs("uploads", exist_ok=True)
                    for f in oct_files:
                        p = os.path.join("uploads", f"{datetime.now().timestamp()}_{f.name}")
                        with open(p, "wb") as fp: fp.write(f.getbuffer())
                        uploads.append(p)
                cur = conn.cursor()
                cur.execute('INSERT INTO posterior_segment_exams (patient_id, fundus_exam_type, fundus_od, fundus_os, fundus_notes, oct_notes, posterior_segment_notes, uploaded_files) VALUES (?,?,?,?,?,?,?,?)',
                            (pinfo['id'], fundus_type, fundus_od, fundus_os, fundus_notes, oct_notes, post_notes, json.dumps(uploads)))
                conn.commit()
                st.success("Posterior segment saved.")
                st.session_state.exam_step = "contact_lenses"
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Database error: {e}")

# --- Contact Lenses ---
def render_contact_lens_for_patient(pinfo):
    st.markdown("#### Contact Lens Fitting & Follow-up")
    with st.form("cl_form"):
        lens_type = st.selectbox("Lens type", ["Soft", "RGP", "Scleral", "Hybrid", "Special"])
        brand = st.text_input("Brand / Model")
        bc = st.text_input("Base curve (BC)")
        dia = st.text_input("Diameter (DIA)")
        power = st.text_input("Power (PWR)")
        material = st.text_input("Material")
        wearing = st.text_input("Wearing schedule")
        care = st.text_input("Care system")
        notes = st.text_area("Fitting notes", height=80)
        cl_files = st.file_uploader("Upload fitting images / results", type=["jpg","png","pdf"], accept_multiple_files=True)
        savecl = st.form_submit_button("Save contact lens fitting")
        if savecl:
            try:
                uploads = []
                if cl_files:
                    os.makedirs("uploads", exist_ok=True)
                    for f in cl_files:
                        path = os.path.join("uploads", f"{datetime.now().timestamp()}_{f.name}")
                        with open(path, "wb") as fp: fp.write(f.getbuffer())
                        uploads.append(path)
                cur = conn.cursor()
                cur.execute('INSERT INTO contact_lens_fittings (patient_id, lens_type, brand, bc, dia, power, material, wearing_schedule, care_system, fitting_notes, uploaded_files) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                            (pinfo['id'], lens_type, brand, bc, dia, power, material, wearing, care, notes, json.dumps(uploads)))
                conn.commit()
                st.success("Contact lens record saved.")
                st.session_state.exam_step = "report"
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Database error: {e}")

# --- Reports ---
def render_report_for_patient(pinfo):
    st.markdown("#### Patient Report")
    st.info("This report includes basic data, refraction summary, and latest findings.")
    notes = st.text_area("Doctor's notes for report", height=120)
    if st.button("Generate printable report"):
        try:
            path = f"reports/{pinfo['last_name']}_{pinfo['first_name']}_{int(datetime.now().timestamp())}.txt"
            os.makedirs("reports", exist_ok=True)
            with open(path, "w", encoding="utf-8") as fp:
                fp.write(f"Patient: {pinfo['first_name']} {pinfo['last_name']}\nDOB: {pinfo['dob']}\n\nNotes:\n{notes}\n")
            st.success(f"Report generated and saved: {path}")
        except Exception as e:
            st.error(f"Error generating report: {e}")

# --- Appointments tab ---
def render_appointments():
    st.markdown("### Appointments")
    view = st.radio("View mode", ["Today", "This week", "This month"], horizontal=True)
    today = datetime.now().date()
    cur = conn.cursor()
    if view == "Today":
        cur.execute("SELECT a.id, p.first_name, p.last_name, a.appointment_date, a.appointment_type, a.status FROM appointments a JOIN patients p ON a.patient_id=p.id WHERE DATE(a.appointment_date)=DATE('now')")
    elif view == "This week":
        cur.execute("SELECT a.id, p.first_name, p.last_name, a.appointment_date, a.appointment_type, a.status FROM appointments a JOIN patients p ON a.patient_id=p.id WHERE a.appointment_date BETWEEN DATE('now','-7 days') AND DATE('now','+7 days')")
    else:
        cur.execute("SELECT a.id, p.first_name, p.last_name, a.appointment_date, a.appointment_type, a.status FROM appointments a JOIN patients p ON a.patient_id=p.id WHERE strftime('%Y-%m',a.appointment_date)=strftime('%Y-%m','now')")
    rows = cur.fetchall()
    if rows:
        for r in rows:
            st.markdown(f"🕑 {r[3]} — **{r[1]} {r[2]}** ({r[4]}) — *{r[5]}*")
    else:
        st.info("No appointments found for selected period.")

    st.markdown("---")
    with st.expander("➕ New Appointment"):
        cur.execute("SELECT id, first_name, last_name FROM patients ORDER BY last_name")
        pats = cur.fetchall()
        patmap = {f"{p[2]}, {p[1]}": p[0] for p in pats}
        pname = st.selectbox("Select patient", list(patmap.keys()) if pats else [])
        apptype = st.text_input("Appointment type")
        appdate = st.date_input("Date", value=today, min_value=date(1910,1,1))
        apptime = st.time_input("Time", value=datetime.now().time())
        notes = st.text_area("Notes", height=80)
        if st.button("Save appointment"):
            if pname:
                try:
                    cur.execute("INSERT INTO appointments (patient_id, appointment_date, appointment_type, notes) VALUES (?,?,?,?)",
                                (patmap[pname], datetime.combine(appdate, apptime), apptype, notes))
                    conn.commit()
                    st.success("Appointment saved.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error saving appointment: {e}")
            else:
                st.warning("Select a patient first.")

# --- Horizontal Navbar ---
def navbar():
    st.markdown("""
        <style>
        div[data-testid="stSidebar"] {display: none;}
        .navbar {
            background-color: #f0f2f6;
            padding: 0.7rem 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #ddd;
        }
        .nav-links {
            display: flex;
            gap: 1rem;
        }
        .nav-item {
            font-weight: 500;
            padding: 0.4rem 0.7rem;
            border-radius: 0.5rem;
        }
        .nav-item:hover {
            background-color: #e0e0e0;
            cursor: pointer;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="navbar">
            <div><img src="logo.png" alt="Logo" width="80"></div>
            <div class="nav-links">
                <span class="nav-item" onclick="window.location.href='/?nav=dashboard'">Dashboard</span>
                <span class="nav-item" onclick="window.location.href='/?nav=patients'">Patients</span>
                <span class="nav-item" onclick="window.location.href='/?nav=appointments'">Appointments</span>
                <span class="nav-item" onclick="window.location.href='/?nav=exams'">Examinations</span>
                <span class="nav-item" onclick="window.location.href='/?nav=contacts'">Contact Lenses</span>
                <span class="nav-item" onclick="window.location.href='/?nav=reports'">Reports</span>
            </div>
            <div style="font-size:0.9rem;">Phantasmed</div>
        </div>
    """, unsafe_allow_html=True)
# --- LOGIN SCREEN ---
def login_screen():
    st.markdown("""
        <style>
        .login-header {
            display:flex; justify-content:space-between; align-items:center;
            margin-bottom:1rem;
        }
        </style>
        <div class="login-header">
            <img src="logo.png" width="120">
            <div style="font-weight:600;font-size:1.2rem;">Phantasmed</div>
        </div>
    """, unsafe_allow_html=True)

    user = st.text_input("Username")
    pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if user == "admin" and pw == "admin":   # primjer – možeš kasnije povezati s DB
            st.session_state["logged_in"] = True
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")

# --- WRAPPER ---
def app_router():
    if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
        login_screen()
    else:
        main()

# --- Main App Navigation ---
def main():
    navbar()
    query_params = st.experimental_get_query_params()
    nav = query_params.get("nav", ["dashboard"])[0]

    if nav == "dashboard":
        st.markdown("### Dashboard")
        st.write("Today’s overview and quick stats will appear here soon.")
    elif nav == "patients":
        st.markdown("### Patients")
        st.write("Patient management module loaded.")
    elif nav == "appointments":
        render_appointments()
    elif nav == "exams":
        st.markdown("### Examinations")
        st.write("Examination workflow loaded.")
    elif nav == "contacts":
        st.markdown("### Contact Lenses")
        st.write("Contact lens records loaded.")
    elif nav == "reports":
        st.markdown("### Reports")
        st.write("Reporting and analytics module.")
    else:
        st.write("Unknown section.")

# --- Run App ---
if __name__ == "__main__":
    main()

