import streamlit as st
import sqlite3
import pandas as pd
import datetime
import hashlib
from datetime import datetime, timedelta
import plotly.express as px

# Page configuration
st.set_page_config(
    page_title="OphtalCAM EMR",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Database setup with persistent storage for Streamlit Cloud
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
            notes TEXT,
            status TEXT DEFAULT 'Scheduled',
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')
    
    # Medical records table
    c.execute('''
        CREATE TABLE IF NOT EXISTS medical_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            visit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            diagnosis_group TEXT,
            sphere_right REAL,
            cylinder_right REAL,
            axis_right INTEGER,
            sphere_left REAL,
            cylinder_left REAL,
            axis_left INTEGER,
            addition_right REAL,
            addition_left REAL,
            intraocular_pressure_right REAL,
            intraocular_pressure_left REAL,
            corneal_thickness_right REAL,
            corneal_thickness_left REAL,
            contact_lens_prescribed BOOLEAN,
            contact_lens_type TEXT,
            notes TEXT,
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

# Custom CSS for styling
def load_css():
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #1f77b4 0%, #2c91d1 100%);
        padding: 2rem;
        border-radius: 0.5rem;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .stButton button {
        background-color: #1f77b4;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.25rem;
        font-weight: 500;
    }
    .stButton button:hover {
        background-color: #1668a0;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# Display header with logo
def display_header():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("https://i.postimg.cc/qq656tks/Phantasmed-logo.png", width=200)
        st.markdown("<h1 style='text-align: center; color: #1f77b4;'>OphtalCAM EMR</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #666;'>by PhantasMED</h3>", unsafe_allow_html=True)
    st.markdown("---")

# Login page
def login_page():
    st.markdown("<div class='main-header'><h2>👁️ OphtalCAM Login</h2></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Enter your username")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
            login_button = st.form_submit_button("🚀 Login", use_container_width=True)
            
            if login_button:
                if username and password:
                    user, message = authenticate_user(username, password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.username = user[0]
                        st.session_state.role = user[2]
                        st.success(f"🎉 Welcome {user[0]}!")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("⚠️ Please enter both username and password")
        
        # Demo credentials info
        st.markdown("---")
        st.info("""
        **Demo Credentials:**
        - **Username:** `admin`
        - **Password:** `admin123`
        """)

# Admin dashboard
def admin_dashboard():
    st.sidebar.title("Admin Panel")
    menu = st.sidebar.selectbox("Menu", ["Dashboard", "User Management", "Analytics"])
    
    if menu == "Dashboard":
        st.subheader("Admin Dashboard")
        
        # Quick stats
        col1, col2, col3, col4 = st.columns(4)
        
        conn = init_db()
        
        # Total patients
        total_patients = pd.read_sql("SELECT COUNT(*) as count FROM patients", conn).iloc[0]['count']
        
        # Total appointments
        total_appointments = pd.read_sql("SELECT COUNT(*) as count FROM appointments", conn).iloc[0]['count']
        
        # Today's appointments
        today = datetime.now().date()
        today_appointments = pd.read_sql(
            "SELECT COUNT(*) as count FROM appointments WHERE DATE(appointment_date) = ?", 
            conn, params=(today,)
        ).iloc[0]['count']
        
        # Total users
        total_users = pd.read_sql("SELECT COUNT(*) as count FROM users", conn).iloc[0]['count']
        
        with col1:
            st.metric("Total Patients", total_patients)
        with col2:
            st.metric("Total Appointments", total_appointments)
        with col3:
            st.metric("Today's Appointments", today_appointments)
        with col4:
            st.metric("System Users", total_users)
        
    elif menu == "User Management":
        st.subheader("User Management")
        
        with st.form("create_user_form"):
            st.write("Create New User")
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            user_role = st.selectbox("Role", ["user", "doctor", "admin"])
            expiry_days = st.number_input("Account Expiry (days)", min_value=1, value=365)
            
            create_button = st.form_submit_button("Create User")
            
            if create_button:
                if new_username and new_password:
                    if create_user(new_username, new_password, user_role, expiry_days):
                        st.success(f"User {new_username} created successfully!")
                    else:
                        st.error("Username already exists!")
                else:
                    st.error("Please fill all fields")
        
        # Display existing users
        st.subheader("Existing Users")
        conn = init_db()
        users_df = pd.read_sql("SELECT username, role, created_date, expiry_date FROM users", conn)
        
        if not users_df.empty:
            st.dataframe(users_df)
        else:
            st.info("No users found")
            
    elif menu == "Analytics":
        st.subheader("System Analytics")
        
        conn = init_db()
        
        # Diagnosis groups distribution
        diagnosis_data = pd.read_sql(
            "SELECT diagnosis_group, COUNT(*) as count FROM medical_records GROUP BY diagnosis_group", 
            conn
        )
        
        if not diagnosis_data.empty:
            fig = px.pie(diagnosis_data, values='count', names='diagnosis_group', 
                         title='Distribution by Diagnosis Groups')
            st.plotly_chart(fig)

# Main application
def main_app():
    st.sidebar.title("OphtalCAM Navigation")
    menu = st.sidebar.selectbox("Menu", [
        "Dashboard", 
        "Patient Registration", 
        "Appointment Scheduling", 
        "Medical Records", 
        "Patient Search",
        "Analytics"
    ])
    
    if menu == "Dashboard":
        show_dashboard()
    elif menu == "Patient Registration":
        patient_registration()
    elif menu == "Appointment Scheduling":
        appointment_scheduling()
    elif menu == "Medical Records":
        medical_records()
    elif menu == "Patient Search":
        patient_search()
    elif menu == "Analytics":
        show_analytics()

def show_dashboard():
    st.subheader("Clinical Dashboard")
    
    # Today's appointments
    conn = init_db()
    today = datetime.now().date()
    
    today_appointments = pd.read_sql(
        """SELECT a.appointment_date, p.first_name, p.last_name, a.type 
           FROM appointments a 
           JOIN patients p ON a.patient_id = p.id 
           WHERE DATE(a.appointment_date) = ? 
           ORDER BY a.appointment_date""", 
        conn, params=(today,)
    )
    
    if not today_appointments.empty:
        st.write("Today's Appointments:")
        st.dataframe(today_appointments)
    else:
        st.info("No appointments scheduled for today")

def patient_registration():
    st.subheader("Patient Registration")
    
    with st.form("patient_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            first_name = st.text_input("First Name*")
            last_name = st.text_input("Last Name*")
            date_of_birth = st.date_input("Date of Birth", max_value=datetime.now().date())
            gender = st.selectbox("Gender", ["", "Male", "Female", "Other"])
        
        with col2:
            phone = st.text_input("Phone")
            email = st.text_input("Email")
            address = st.text_area("Address")
        
        submit_button = st.form_submit_button("Register Patient")
        
        if submit_button:
            if first_name and last_name:
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
                    st.success(f"Patient registered successfully! Patient ID: {patient_id}")
                except Exception as e:
                    st.error(f"Error registering patient: {str(e)}")
            else:
                st.error("Please fill required fields (First Name and Last Name)")

def appointment_scheduling():
    st.subheader("Appointment Scheduling")
    
    conn = init_db()
    patients = pd.read_sql("SELECT id, patient_id, first_name, last_name FROM patients", conn)
    
    if patients.empty:
        st.warning("No patients registered. Please register patients first.")
        return
    
    with st.form("appointment_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            patient_options = [f"{row['patient_id']} - {row['first_name']} {row['last_name']}" for _, row in patients.iterrows()]
            selected_patient = st.selectbox("Select Patient*", [""] + patient_options)
            
            appointment_date = st.date_input("Appointment Date*", min_value=datetime.now().date())
            appointment_time = st.time_input("Appointment Time*")
        
        with col2:
            duration = st.number_input("Duration (minutes)*", min_value=15, max_value=180, value=30, step=15)
            appointment_type = st.selectbox("Appointment Type*", 
                                          ["Routine Checkup", "Consultation", "Surgery", "Follow-up", "Emergency"])
            notes = st.text_area("Notes")
        
        submit_button = st.form_submit_button("Schedule Appointment")
        
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
                        st.success("Appointment scheduled successfully!")
                    except Exception as e:
                        st.error(f"Error scheduling appointment: {str(e)}")
                else:
                    st.error("Patient not found in database")
            else:
                st.error("Please fill all required fields")

def medical_records():
    st.subheader("Medical Records")
    
    conn = init_db()
    patients = pd.read_sql("SELECT id, patient_id, first_name, last_name FROM patients", conn)
    
    if patients.empty:
        st.warning("No patients registered. Please register patients first.")
        return
    
    patient_options = [f"{row['patient_id']} - {row['first_name']} {row['last_name']}" for _, row in patients.iterrows()]
    selected_patient = st.selectbox("Select Patient", patient_options)
    
    if selected_patient:
        patient_id_str = selected_patient.split(" - ")[0]
        
        with st.form("medical_record_form"):
            st.write("Ophthalmic Examination")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Right Eye")
                sphere_right = st.number_input("Sphere (Right)", value=0.0, step=0.25)
                cylinder_right = st.number_input("Cylinder (Right)", value=0.0, step=0.25)
                axis_right = st.number_input("Axis (Right)", min_value=0, max_value=180, value=0)
                addition_right = st.number_input("Addition (Right)", value=0.0, step=0.25)
                intraocular_pressure_right = st.number_input("IOP (Right)", value=0.0, step=0.1)
                corneal_thickness_right = st.number_input("Corneal Thickness (Right)", value=0.0)
            
            with col2:
                st.subheader("Left Eye")
                sphere_left = st.number_input("Sphere (Left)", value=0.0, step=0.25)
                cylinder_left = st.number_input("Cylinder (Left)", value=0.0, step=0.25)
                axis_left = st.number_input("Axis (Left)", min_value=0, max_value=180, value=0)
                addition_left = st.number_input("Addition (Left)", value=0.0, step=0.25)
                intraocular_pressure_left = st.number_input("IOP (Left)", value=0.0, step=0.1)
                corneal_thickness_left = st.number_input("Corneal Thickness (Left)", value=0.0)
            
            st.subheader("Diagnosis and Treatment")
            diagnosis_group = st.selectbox("Diagnosis Group", [
                "", "Kornealne ektazije", "Katarakta", "Bolesti stražnjeg segmenta", 
                "Glaukom", "Myopia Control", "Refrakcijske anomalije", "Ostalo"
            ])
            
            contact_lens_prescribed = st.checkbox("Contact Lens Prescribed")
            contact_lens_type = ""
            if contact_lens_prescribed:
                contact_lens_type = st.selectbox("Contact Lens Type", [
                    "Soft", "Rigid Gas Permeable", "Scleral", "Hybrid", "Custom"
                ])
            
            notes = st.text_area("Clinical Notes")
            
            submit_button = st.form_submit_button("Save Medical Record")
            
            if submit_button:
                c = conn.cursor()
                
                # Get patient database ID
                c.execute("SELECT id FROM patients WHERE patient_id = ?", (patient_id_str,))
                result = c.fetchone()
                
                if result:
                    patient_db_id = result[0]
                    
                    try:
                        c.execute('''
                            INSERT INTO medical_records 
                            (patient_id, diagnosis_group, sphere_right, cylinder_right, axis_right,
                             sphere_left, cylinder_left, axis_left, addition_right, addition_left,
                             intraocular_pressure_right, intraocular_pressure_left,
                             corneal_thickness_right, corneal_thickness_left,
                             contact_lens_prescribed, contact_lens_type, notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (patient_db_id, diagnosis_group, sphere_right, cylinder_right, axis_right,
                              sphere_left, cylinder_left, axis_left, addition_right, addition_left,
                              intraocular_pressure_right, intraocular_pressure_left,
                              corneal_thickness_right, corneal_thickness_left,
                              contact_lens_prescribed, contact_lens_type, notes))
                        
                        conn.commit()
                        st.success("Medical record saved successfully!")
                    except Exception as e:
                        st.error(f"Error saving medical record: {str(e)}")
                else:
                    st.error("Patient not found")

def patient_search():
    st.subheader("Patient Search and Analysis")
    
    search_option = st.radio("Search by", ["Patient Information", "Medical Criteria"])
    
    if search_option == "Patient Information":
        conn = init_db()
        
        search_term = st.text_input("Search by Name or Patient ID")
        
        if search_term:
            patients = pd.read_sql(
                """SELECT * FROM patients 
                   WHERE first_name LIKE ? OR last_name LIKE ? OR patient_id LIKE ?""", 
                conn, params=(f"%{search_term}%", f"%{search_term}%", f"%{search_term}%")
            )
            
            if not patients.empty:
                st.dataframe(patients)
            else:
                st.info("No patients found matching search criteria")
    
    else:  # Medical Criteria search
        conn = init_db()
        
        col1, col2 = st.columns(2)
        
        with col1:
            min_sphere = st.number_input("Min Sphere", value=-10.0, step=0.25)
            max_sphere = st.number_input("Max Sphere", value=10.0, step=0.25)
            
            diagnosis_group = st.selectbox("Diagnosis Group Filter", [
                "", "Kornealne ektazije", "Katarakta", "Bolesti stražnjeg segmenta", 
                "Glaukom", "Myopia Control", "Refrakcijske anomalije", "Ostalo"
            ])
        
        with col2:
            contact_lens_prescribed = st.selectbox("Contact Lens Prescribed", ["", "Yes", "No"])
            min_iop = st.number_input("Min IOP", value=0.0, step=0.1)
            max_iop = st.number_input("Max IOP", value=30.0, step=0.1)
        
        if st.button("Search Medical Records"):
            # Build query
            query = """
                SELECT p.patient_id, p.first_name, p.last_name, 
                       mr.sphere_right, mr.sphere_left, mr.diagnosis_group,
                       mr.intraocular_pressure_right, mr.intraocular_pressure_left,
                       mr.contact_lens_prescribed
                FROM medical_records mr
                JOIN patients p ON mr.patient_id = p.id
                WHERE 1=1
            """
            params = []
            
            if min_sphere or max_sphere:
                query += " AND (mr.sphere_right BETWEEN ? AND ? OR mr.sphere_left BETWEEN ? AND ?)"
                params.extend([min_sphere, max_sphere, min_sphere, max_sphere])
            
            if diagnosis_group:
                query += " AND mr.diagnosis_group = ?"
                params.append(diagnosis_group)
            
            if contact_lens_prescribed == "Yes":
                query += " AND mr.contact_lens_prescribed = 1"
            elif contact_lens_prescribed == "No":
                query += " AND mr.contact_lens_prescribed = 0"
            
            if min_iop or max_iop:
                query += " AND (mr.intraocular_pressure_right BETWEEN ? AND ? OR mr.intraocular_pressure_left BETWEEN ? AND ?)"
                params.extend([min_iop, max_iop, min_iop, max_iop])
            
            results = pd.read_sql(query, conn, params=params)
            
            if not results.empty:
                st.write(f"Found {len(results)} records")
                st.dataframe(results)
            else:
                st.info("No medical records found matching criteria")

def show_analytics():
    st.subheader("Clinical Analytics")
    
    conn = init_db()
    
    # Diagnosis distribution
    diagnosis_stats = pd.read_sql(
        "SELECT diagnosis_group, COUNT(*) as count FROM medical_records GROUP BY diagnosis_group", 
        conn
    )
    
    if not diagnosis_stats.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.pie(diagnosis_stats, values='count', names='diagnosis_group', 
                        title='Diagnosis Group Distribution')
            st.plotly_chart(fig)
        
        with col2:
            fig = px.bar(diagnosis_stats, x='diagnosis_group', y='count',
                        title='Diagnosis Group Counts')
            st.plotly_chart(fig)
    
    # Myopia analysis
    myopia_data = pd.read_sql("""
        SELECT 
            CASE 
                WHEN sphere_right < 0 OR sphere_left < 0 THEN 'Myopia'
                ELSE 'Other'
            END as condition,
            COUNT(*) as count
        FROM medical_records 
        GROUP BY condition
    """, conn)
    
    if not myopia_data.empty:
        st.subheader("Myopia Analysis")
        col1, col2, col3 = st.columns(3)
        
        total_records = myopia_data['count'].sum()
        myopia_count = myopia_data[myopia_data['condition'] == 'Myopia']['count'].sum() if not myopia_data[myopia_data['condition'] == 'Myopia'].empty else 0
        myopia_percentage = (myopia_count / total_records * 100) if total_records > 0 else 0
        
        with col1:
            st.metric("Total Records", total_records)
        with col2:
            st.metric("Myopia Cases", myopia_count)
        with col3:
            st.metric("Myopia Prevalence", f"{myopia_percentage:.1f}%")

# Main application flow
def main():
    load_css()
    display_header()
    
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
        # Logout button
        col1, col2, col3 = st.columns([2, 1, 1])
        with col3:
            if st.button("🚪 Logout"):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.session_state.role = None
                st.rerun()
        
        # Show user info
        st.sidebar.markdown(f"**Logged in as:** {st.session_state.username}")
        st.sidebar.markdown(f"**Role:** {st.session_state.role}")
        
        # Show appropriate dashboard based on role
        if st.session_state.role == 'admin':
            admin_dashboard()
        else:
            main_app()

if __name__ == "__main__":
    main()