import streamlit as st
import sqlite3
import pandas as pd
import datetime
import hashlib
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import calendar
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import io

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
            anamnesis TEXT,
            distance_vision_uncorrected_od TEXT,
            distance_vision_uncorrected_os TEXT,
            distance_vision_corrected_od TEXT,
            distance_vision_corrected_os TEXT,
            near_vision_od TEXT,
            near_vision_os TEXT,
            
            # REFRACTION - Added fields
            sphere_od REAL,
            cylinder_od REAL,
            axis_od INTEGER,
            sphere_os REAL,
            cylinder_os REAL,
            axis_os INTEGER,
            addition_od REAL,
            addition_os REAL,
            pd_od REAL,
            pd_os REAL,
            refraction_type TEXT,
            
            tonometry_od TEXT,
            tonometry_os TEXT,
            biomicroscopy_od TEXT,
            biomicroscopy_os TEXT,
            ophthalmoscopy_od TEXT,
            ophthalmoscopy_os TEXT,
            diagnosis TEXT,
            treatment TEXT,
            refraction_performed BOOLEAN DEFAULT 0,
            contact_lens_prescribed BOOLEAN DEFAULT 0,
            contact_lens_type TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')
    
    # Working hours table
    c.execute('''
        CREATE TABLE IF NOT EXISTS working_hours (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day_of_week INTEGER, -- 0=Monday, 6=Sunday
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
    
    # Insert default working hours (Mon-Fri 8:00-20:00)
    default_hours = [
        (0, '08:00', '20:00', 1), # Monday
        (1, '08:00', '20:00', 1), # Tuesday
        (2, '08:00', '20:00', 1), # Wednesday
        (3, '08:00', '20:00', 1), # Thursday
        (4, '08:00', '20:00', 1), # Friday
        (5, '08:00', '20:00', 1), # Saturday
        (6, '08:00', '20:00', 1)  # Sunday
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

def get_available_time_slots(date):
    """Get available time slots for a given date"""
    conn = init_db()
    
    # Check if it's a working day
    day_of_week = date.weekday()
    working_hours = pd.read_sql(
        "SELECT start_time, end_time, is_working_day FROM working_hours WHERE day_of_week = ?",
        conn, params=(day_of_week,)
    )
    
    if working_hours.empty or not working_hours.iloc[0]['is_working_day']:
        return []
    
    # Check if it's a holiday
    holidays = pd.read_sql(
        "SELECT holiday_date FROM holidays WHERE holiday_date = ?",
        conn, params=(date,)
    )
    
    if not holidays.empty:
        return []
    
    start_time = datetime.strptime(working_hours.iloc[0]['start_time'], '%H:%M').time()
    end_time = datetime.strptime(working_hours.iloc[0]['end_time'], '%H:%M').time()
    
    # Get booked appointments for the day
    appointments = pd.read_sql(
        "SELECT appointment_date FROM appointments WHERE DATE(appointment_date) = ?",
        conn, params=(date,)
    )
    
    booked_slots = []
    if not appointments.empty:
        booked_slots = [pd.to_datetime(apt).time() for apt in appointments['appointment_date']]
    
    # Generate available slots (every 30 minutes)
    available_slots = []
    current_time = datetime.combine(date, start_time)
    end_datetime = datetime.combine(date, end_time)
    
    while current_time <= end_datetime:
        if current_time.time() not in booked_slots:
            available_slots.append(current_time.time())
        current_time += timedelta(minutes=30)
    
    return available_slots

def generate_pdf_report(patient_data, examination_data):
    """Generate PDF report for patient"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=12
    )
    
    normal_style = styles['Normal']
    
    story = []
    
    # Header
    story.append(Paragraph("OPHTALCAM - OPHTHALMOLOGY CENTER", title_style))
    story.append(Paragraph("Examination Report", styles['Heading2']))
    story.append(Spacer(1, 20))
    
    # Patient information
    story.append(Paragraph("Patient Information:", heading_style))
    patient_info = [
        ["Name:", f"{patient_data['first_name']} {patient_data['last_name']}"],
        ["Date of Birth:", patient_data['date_of_birth']],
        ["Gender:", patient_data['gender']],
        ["Patient ID:", patient_data['patient_id']]
    ]
    
    patient_table = Table(patient_info, colWidths=[2*inch, 4*inch])
    patient_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 20))
    
    # Examination details
    story.append(Paragraph("Examination Results:", heading_style))
    
    # Vision
    story.append(Paragraph("Visual Acuity:", styles['Heading3']))
    vision_data = [
        ["", "OD (Right)", "OS (Left)"],
        ["Distance Uncorrected", examination_data['distance_vision_uncorrected_od'] or "-", 
         examination_data['distance_vision_uncorrected_os'] or "-"],
        ["Distance Corrected", examination_data['distance_vision_corrected_od'] or "-", 
         examination_data['distance_vision_corrected_os'] or "-"],
        ["Near Vision", examination_data['near_vision_od'] or "-", 
         examination_data['near_vision_os'] or "-"]
    ]
    
    vision_table = Table(vision_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
    vision_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(vision_table)
    story.append(Spacer(1, 12))
    
    # Refraction if available
    if examination_data.get('refraction_performed'):
        story.append(Paragraph("Refraction:", styles['Heading3']))
        refraction_data = [
            ["", "OD (Right)", "OS (Left)"],
            ["Sphere", f"{examination_data['sphere_od'] or '-'} D", f"{examination_data['sphere_os'] or '-'} D"],
            ["Cylinder", f"{examination_data['cylinder_od'] or '-'} D", f"{examination_data['cylinder_os'] or '-'} D"],
            ["Axis", f"{examination_data['axis_od'] or '-'}°", f"{examination_data['axis_os'] or '-'}°"],
            ["Addition", f"{examination_data['addition_od'] or '-'} D", f"{examination_data['addition_os'] or '-'} D"],
            ["PD", f"{examination_data['pd_od'] or '-'} mm", f"{examination_data['pd_os'] or '-'} mm"]
        ]
        
        refraction_table = Table(refraction_data, colWidths=[1.2*inch, 1.5*inch, 1.5*inch])
        refraction_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(refraction_table)
        story.append(Spacer(1, 12))
    
    # Tonometry
    story.append(Paragraph("Tonometry:", styles['Heading3']))
    tono_data = [
        ["OD (Right):", f"{examination_data['tonometry_od'] or '-'} mmHg"],
        ["OS (Left):", f"{examination_data['tonometry_os'] or '-'} mmHg"]
    ]
    
    for row in tono_data:
        story.append(Paragraph(f"{row[0]} {row[1]}", normal_style))
    
    story.append(Spacer(1, 12))
    
    # Diagnosis and treatment
    if examination_data['diagnosis']:
        story.append(Paragraph("Diagnosis:", styles['Heading3']))
        story.append(Paragraph(examination_data['diagnosis'], normal_style))
        story.append(Spacer(1, 12))
    
    if examination_data['treatment']:
        story.append(Paragraph("Recommended Treatment:", styles['Heading3']))
        story.append(Paragraph(examination_data['treatment'], normal_style))
    
    # Footer
    story.append(Spacer(1, 30))
    story.append(Paragraph(f"Examination Date: {examination_data['visit_date']}", normal_style))
    story.append(Paragraph("Physician: ___________________", normal_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

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
    .calendar-day {
        padding: 10px;
        border: 1px solid #e0e0e0;
        height: 120px;
        background-color: white;
    }
    .calendar-day.today {
        background-color: #e3f2fd;
        border: 2px solid #1f77b4;
    }
    .calendar-day.has-appointments {
        background-color: #fff3e0;
    }
    .calendar-day.non-working {
        background-color: #f5f5f5;
        color: #999;
    }
    .appointment-badge {
        background-color: #1f77b4;
        color: white;
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 0.8em;
        margin: 1px;
    }
    .metric-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# Login page
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

# Working Hours Management
def manage_working_hours():
    st.subheader("Working Hours Management")
    
    conn = init_db()
    
    # Display current working hours
    st.write("### Current Working Hours")
    working_hours = pd.read_sql("SELECT * FROM working_hours ORDER BY day_of_week", conn)
    
    if not working_hours.empty:
        # Map day numbers to names
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        working_hours['day_name'] = working_hours['day_of_week'].apply(lambda x: day_names[x])
        
        st.dataframe(working_hours[['day_name', 'start_time', 'end_time', 'is_working_day']])
    
    # Update working hours
    st.write("### Update Working Hours")
    
    with st.form("working_hours_form"):
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        
        with col1:
            day_of_week = st.selectbox("Day", [
                (0, "Monday"), (1, "Tuesday"), (2, "Wednesday"), 
                (3, "Thursday"), (4, "Friday"), (5, "Saturday"), (6, "Sunday")
            ], format_func=lambda x: x[1])
        
        with col2:
            start_time = st.time_input("Start Time", value=datetime.strptime("08:00", "%H:%M").time())
        
        with col3:
            end_time = st.time_input("End Time", value=datetime.strptime("20:00", "%H:%M").time())
        
        with col4:
            is_working_day = st.checkbox("Working Day", value=True)
        
        update_button = st.form_submit_button("Update Working Hours")
        
        if update_button:
            c = conn.cursor()
            day_num = day_of_week[0]
            
            try:
                c.execute('''
                    INSERT OR REPLACE INTO working_hours (day_of_week, start_time, end_time, is_working_day)
                    VALUES (?, ?, ?, ?)
                ''', (day_num, start_time.strftime('%H:%M'), end_time.strftime('%H:%M'), is_working_day))
                
                conn.commit()
                st.success(f"Working hours updated for {day_of_week[1]}!")
                st.rerun()
            except Exception as e:
                st.error(f"Error updating working hours: {str(e)}")
    
    # Holiday management
    st.write("### Manage Holidays")
    
    with st.form("holiday_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            holiday_date = st.date_input("Holiday Date", min_value=datetime.now().date())
        
        with col2:
            description = st.text_input("Description", placeholder="e.g., Christmas Day")
        
        add_holiday = st.form_submit_button("Add Holiday")
        
        if add_holiday:
            c = conn.cursor()
            
            try:
                c.execute('''
                    INSERT OR IGNORE INTO holidays (holiday_date, description)
                    VALUES (?, ?)
                ''', (holiday_date, description))
                
                conn.commit()
                st.success(f"Holiday added: {holiday_date}")
                st.rerun()
            except Exception as e:
                st.error(f"Error adding holiday: {str(e)}")
    
    # Display current holidays
    holidays = pd.read_sql("SELECT * FROM holidays ORDER BY holiday_date", conn)
    if not holidays.empty:
        st.write("### Current Holidays")
        st.dataframe(holidays)

# Updated Calendar with time slots
def show_calendar():
    st.subheader("Appointment Calendar")
    
    # Initialize session state for calendar if not exists
    if 'current_month' not in st.session_state:
        st.session_state.current_month = datetime.now().month
        st.session_state.current_year = datetime.now().year
    if 'selected_date' not in st.session_state:
        st.session_state.selected_date = None
    if 'selected_time' not in st.session_state:
        st.session_state.selected_time = None
    
    # Month navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("◀ Previous Month"):
            st.session_state.current_month -= 1
            if st.session_state.current_month == 0:
                st.session_state.current_month = 12
                st.session_state.current_year -= 1
            st.rerun()
    
    with col2:
        month_name = ["January", "February", "March", "April", "May", "June",
                     "July", "August", "September", "October", "November", "December"][st.session_state.current_month - 1]
        st.markdown(f"<h3 style='text-align: center;'>{month_name} {st.session_state.current_year}</h3>", unsafe_allow_html=True)
    
    with col3:
        if st.button("Next Month ▶"):
            st.session_state.current_month += 1
            if st.session_state.current_month == 13:
                st.session_state.current_month = 1
                st.session_state.current_year += 1
            st.rerun()
    
    # Get appointments for the month
    conn = init_db()
    start_date = datetime(st.session_state.current_year, st.session_state.current_month, 1)
    if st.session_state.current_month == 12:
        end_date = datetime(st.session_state.current_year + 1, 1, 1)
    else:
        end_date = datetime(st.session_state.current_year, st.session_state.current_month + 1, 1)
    
    appointments = pd.read_sql(
        """SELECT a.appointment_date, p.first_name, p.last_name, a.type 
           FROM appointments a 
           JOIN patients p ON a.patient_id = p.id 
           WHERE a.appointment_date >= ? AND a.appointment_date < ? 
           ORDER BY a.appointment_date""", 
        conn, params=(start_date, end_date)
    )
    
    # Create calendar
    cal = calendar.monthcalendar(st.session_state.current_year, st.session_state.current_month)
    
    # Calendar header
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    cols = st.columns(7)
    for i, day in enumerate(days):
        cols[i].write(f"**{day}**")
    
    # Calendar days
    today = datetime.now().date()
    
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day != 0:
                    current_date = datetime(st.session_state.current_year, st.session_state.current_month, day).date()
                    
                    # Check if working day
                    available_slots = get_available_time_slots(current_date)
                    is_working_day = len(available_slots) > 0
                    
                    day_appointments = appointments[
                        pd.to_datetime(appointments['appointment_date']).dt.date == current_date
                    ]
                    
                    # Day styling
                    day_class = "calendar-day"
                    if current_date == today:
                        day_class += " today"
                    if len(day_appointments) > 0:
                        day_class += " has-appointments"
                    if not is_working_day:
                        day_class += " non-working"
                    
                    st.markdown(f'<div class="{day_class}">', unsafe_allow_html=True)
                    st.write(f"**{day}**")
                    
                    # Show appointments for the day
                    for _, appt in day_appointments.iterrows():
                        appt_time = pd.to_datetime(appt['appointment_date']).strftime('%H:%M')
                        patient_name = f"{appt['first_name']} {appt['last_name'][0]}."
                        st.markdown(f'<div class="appointment-badge" title="{appt["type"]}">{appt_time} {patient_name}</div>', unsafe_allow_html=True)
                    
                    # Show day status
                    if not is_working_day:
                        st.markdown('<div style="color: #999; font-size: 0.8em;">Non-working</div>', unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Date selection
                    if is_working_day and st.button("Select", key=f"select_{day}", use_container_width=True):
                        st.session_state.selected_date = current_date
                        st.rerun()
                else:
                    st.markdown('<div style="height: 120px;"></div>', unsafe_allow_html=True)
    
    # Time slot selection
    if st.session_state.selected_date:
        st.markdown("---")
        st.subheader(f"Select Time Slot for {st.session_state.selected_date.strftime('%d.%m.%Y.')}")
        
        available_slots = get_available_time_slots(st.session_state.selected_date)
        
        if available_slots:
            # Display time slots in a grid
            cols = st.columns(6)
            for i, slot in enumerate(available_slots):
                col_idx = i % 6
                with cols[col_idx]:
                    if st.button(slot.strftime('%H:%M'), key=f"time_{i}", use_container_width=True):
                        st.session_state.selected_time = slot
                        st.rerun()
        else:
            st.warning("No available time slots for selected date.")
    
    # New appointment form
    if st.session_state.selected_date and st.session_state.selected_time:
        st.markdown("---")
        st.subheader("Schedule New Appointment")
        
        with st.form("appointment_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Patient selection
                patients_df = pd.read_sql("SELECT id, patient_id, first_name, last_name FROM patients", conn)
                if not patients_df.empty:
                    patient_options = [f"{row['patient_id']} - {row['first_name']} {row['last_name']}" for _, row in patients_df.iterrows()]
                    selected_patient = st.selectbox("Select Patient*", [""] + patient_options)
                else:
                    st.warning("No registered patients")
                    selected_patient = ""
                
                st.write(f"**Selected Time:** {st.session_state.selected_date.strftime('%d.%m.%Y.')} {st.session_state.selected_time.strftime('%H:%M')}")
            
            with col2:
                duration = st.selectbox("Duration*", [15, 30, 45, 60, 90, 120], index=1)
                appointment_type = st.selectbox("Appointment Type*", [
                    "Routine Checkup", "Consultation", "Follow-up", "Emergency", 
                    "Surgery", "Laser Treatment", "Diagnostics", "Refraction"
                ])
                notes = st.text_area("Notes")
            
            submit_button = st.form_submit_button("SCHEDULE APPOINTMENT")
            
            if submit_button:
                if selected_patient:
                    c = conn.cursor()
                    
                    # Extract patient ID
                    patient_id_str = selected_patient.split(" - ")[0]
                    
                    # Get patient database ID
                    c.execute("SELECT id FROM patients WHERE patient_id = ?", (patient_id_str,))
                    result = c.fetchone()
                    
                    if result:
                        patient_db_id = result[0]
                        
                        # Combine date and time
                        appointment_datetime = datetime.combine(st.session_state.selected_date, st.session_state.selected_time)
                        
                        try:
                            c.execute('''
                                INSERT INTO appointments 
                                (patient_id, appointment_date, duration_minutes, type, notes)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (patient_db_id, appointment_datetime, duration, appointment_type, notes))
                            
                            conn.commit()
                            st.success("Appointment successfully scheduled!")
                            
                            # Reset selection
                            st.session_state.selected_date = None
                            st.session_state.selected_time = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error scheduling appointment: {str(e)}")
                    else:
                        st.error("Patient not found in database")
                else:
                    st.error("Please select a patient")

# Updated Medical Examination with Refraction
def medical_examination():
    st.subheader("Ophthalmology Examination Protocol")
    
    # Patient selection
    conn = init_db()
    patients = pd.read_sql("SELECT id, patient_id, first_name, last_name FROM patients", conn)
    
    if patients.empty:
        st.warning("No registered patients. Please register a patient first.")
        return
    
    patient_options = [f"{row['patient_id']} - {row['first_name']} {row['last_name']}" for _, row in patients.iterrows()]
    selected_patient = st.selectbox("Select Patient*", [""] + patient_options)
    
    if not selected_patient:
        st.info("Select a patient to continue with examination")
        return

    # Session state for OphtalCAM buttons
    if 'tono_od_clicked' not in st.session_state:
        st.session_state.tono_od_clicked = False
    if 'tono_os_clicked' not in st.session_state:
        st.session_state.tono_os_clicked = False
    if 'bio_od_clicked' not in st.session_state:
        st.session_state.bio_od_clicked = False
    if 'bio_os_clicked' not in st.session_state:
        st.session_state.bio_os_clicked = False
    if 'oft_od_clicked' not in st.session_state:
        st.session_state.oft_od_clicked = False
    if 'oft_os_clicked' not in st.session_state:
        st.session_state.oft_os_clicked = False

    # OphtalCAM buttons OUTSIDE form
    st.markdown("### OphtalCAM Devices")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 OPHTHALCAM TONOMETRY", key="tono_global", use_container_width=True):
            st.session_state.tono_od_clicked = True
            st.session_state.tono_os_clicked = True
            st.info("Tonometry device will be activated in future version")
    
    with col2:
        if st.button("🔍 OPHTHALCAM BIOMICROSCOPY", key="bio_global", use_container_width=True):
            st.session_state.bio_od_clicked = True
            st.session_state.bio_os_clicked = True
            st.info("Biomicroscopy device will be activated in future version")
    
    with col3:
        if st.button("👁️ OPHTHALCAM OPHTHALMOSCOPY", key="oft_global", use_container_width=True):
            st.session_state.oft_od_clicked = True
            st.session_state.oft_os_clicked = True
            st.info("Ophthalmoscopy device will be activated in future version")

    st.markdown("---")

    # FORM for data entry
    with st.form("examination_form"):
        # 1. ANAMNESIS
        st.markdown('<div class="protocol-section">', unsafe_allow_html=True)
        st.subheader("Anamnesis")
        anamnesis = st.text_area("Anamnesis Description", placeholder="Enter anamnesis details...", height=100)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 2. VISUAL ACUITY
        st.markdown('<div class="protocol-section">', unsafe_allow_html=True)
        st.subheader("Visual Acuity")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**OD (Right Eye)**")
            distance_vision_uncorrected_od = st.text_input("Distance Uncorrected OD", placeholder="e.g., 0.8", key="vision_od_1")
            distance_vision_corrected_od = st.text_input("Distance Corrected OD", placeholder="e.g., 1.0", key="vision_od_2")
            near_vision_od = st.text_input("Near Vision OD", placeholder="e.g., 0.8", key="vision_od_3")
            
        with col2:
            st.write("**OS (Left Eye)**")
            distance_vision_uncorrected_os = st.text_input("Distance Uncorrected OS", placeholder="e.g., 0.6", key="vision_os_1")
            distance_vision_corrected_os = st.text_input("Distance Corrected OS", placeholder="e.g., 1.0", key="vision_os_2")
            near_vision_os = st.text_input("Near Vision OS", placeholder="e.g., 0.6", key="vision_os_3")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 3. REFRACTION
        st.markdown('<div class="protocol-section">', unsafe_allow_html=True)
        st.subheader("Refraction")
        
        refraction_performed = st.checkbox("Refraction Performed", key="refraction_check")
        
        if refraction_performed:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**OD (Right Eye)**")
                sphere_od = st.number_input("Sphere OD (D)", value=0.0, step=0.25, key="sphere_od")
                cylinder_od = st.number_input("Cylinder OD (D)", value=0.0, step=0.25, key="cylinder_od")
                axis_od = st.number_input("Axis OD (°)", min_value=0, max_value=180, value=0, key="axis_od")
                addition_od = st.number_input("Addition OD (D)", value=0.0, step=0.25, key="addition_od")
                pd_od = st.number_input("PD OD (mm)", value=0.0, step=0.5, key="pd_od")
            
            with col2:
                st.write("**OS (Left Eye)**")
                sphere_os = st.number_input("Sphere OS (D)", value=0.0, step=0.25, key="sphere_os")
                cylinder_os = st.number_input("Cylinder OS (D)", value=0.0, step=0.25, key="cylinder_os")
                axis_os = st.number_input("Axis OS (°)", min_value=0, max_value=180, value=0, key="axis_os")
                addition_os = st.number_input("Addition OS (D)", value=0.0, step=0.25, key="addition_os")
                pd_os = st.number_input("PD OS (mm)", value=0.0, step=0.5, key="pd_os")
            
            refraction_type = st.selectbox("Refraction Type", [
                "Subjective", "Objective", "Autorefractor", "Cycloplegic"
            ], key="refraction_type")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 4. TONOMETRY
        st.markdown('<div class="protocol-section">', unsafe_allow_html=True)
        st.subheader("Tonometry")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**OD (Right Eye)**")
            if st.session_state.tono_od_clicked:
                st.success("✅ Tonometry OD - device activated")
            tonometry_od = st.text_input("Value OD (mmHg)", placeholder="e.g., 16", key="tono_od")
            
        with col2:
            st.write("**OS (Left Eye)**")
            if st.session_state.tono_os_clicked:
                st.success("✅ Tonometry OS - device activated")
            tonometry_os = st.text_input("Value OS (mmHg)", placeholder="e.g., 17", key="tono_os")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 5. BIOMICROSCOPY
        st.markdown('<div class="protocol-section">', unsafe_allow_html=True)
        st.subheader("Biomicroscopy")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**OD (Right Eye)**")
            if st.session_state.bio_od_clicked:
                st.success("✅ Biomicroscopy OD - device activated")
            biomicroscopy_od = st.text_area("Findings OD", placeholder="Enter biomicroscopy findings for right eye...", height=100, key="bio_od")
            
        with col2:
            st.write("**OS (Left Eye)**")
            if st.session_state.bio_os_clicked:
                st.success("✅ Biomicroscopy OS - device activated")
            biomicroscopy_os = st.text_area("Findings OS", placeholder="Enter biomicroscopy findings for left eye...", height=100, key="bio_os")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 6. OPHTHALMOSCOPY
        st.markdown('<div class="protocol-section">', unsafe_allow_html=True)
        st.subheader("Ophthalmoscopy")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**OD (Right Eye)**")
            if st.session_state.oft_od_clicked:
                st.success("✅ Ophthalmoscopy OD - device activated")
            ophthalmoscopy_od = st.text_area("Findings OD", placeholder="Enter ophthalmoscopy findings for right eye...", height=100, key="oft_od")
            
        with col2:
            st.write("**OS (Left Eye)**")
            if st.session_state.oft_os_clicked:
                st.success("✅ Ophthalmoscopy OS - device activated")
            ophthalmoscopy_os = st.text_area("Findings OS", placeholder="Enter ophthalmoscopy findings for left eye...", height=100, key="oft_os")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 7. DIAGNOSIS AND TREATMENT
        st.markdown('<div class="protocol-section">', unsafe_allow_html=True)
        st.subheader("Diagnosis and Treatment")
        
        diagnosis = st.text_area("Diagnosis", placeholder="Enter diagnosis...", height=80, key="diagnosis")
        treatment = st.text_area("Recommended Treatment", placeholder="Enter recommended treatment...", height=80, key="treatment")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ADDITIONAL FIELDS FOR ANALYTICS
        st.markdown('<div class="protocol-section">', unsafe_allow_html=True)
        st.subheader("Additional Data for Statistics")
        
        contact_lens_prescribed = st.checkbox("Contact Lenses Prescribed", key="contact_lens")
        contact_lens_type = ""
        if contact_lens_prescribed:
            contact_lens_type = st.selectbox("Contact Lens Type", [
                "Soft Daily", "Soft Monthly", "Soft Yearly",
                "Rigid Gas Permeable", "Scleral", "Therapeutic",
                "Cosmetic", "Custom"
            ], key="lens_type")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SUBMIT BUTTON
        col1, col2 = st.columns(2)
        with col1:
            submit_button = st.form_submit_button("💾 SAVE EXAMINATION PROTOCOL", use_container_width=True)
        with col2:
            generate_report = st.form_submit_button("📄 GENERATE REPORT", use_container_width=True)
        
        if submit_button or generate_report:
            # Save to database
            patient_id_str = selected_patient.split(" - ")[0]
            c = conn.cursor()
            
            # Get patient database ID
            c.execute("SELECT id FROM patients WHERE patient_id = ?", (patient_id_str,))
            result = c.fetchone()
            
            if result:
                patient_db_id = result[0]
                
                try:
                    # Prepare data for insertion
                    examination_data = {
                        'patient_id': patient_db_id,
                        'anamnesis': anamnesis,
                        'distance_vision_uncorrected_od': distance_vision_uncorrected_od,
                        'distance_vision_uncorrected_os': distance_vision_uncorrected_os,
                        'distance_vision_corrected_od': distance_vision_corrected_od,
                        'distance_vision_corrected_os': distance_vision_corrected_os,
                        'near_vision_od': near_vision_od,
                        'near_vision_os': near_vision_os,
                        'tonometry_od': tonometry_od,
                        'tonometry_os': tonometry_os,
                        'biomicroscopy_od': biomicroscopy_od,
                        'biomicroscopy_os': biomicroscopy_os,
                        'ophthalmoscopy_od': ophthalmoscopy_od,
                        'ophthalmoscopy_os': ophthalmoscopy_os,
                        'diagnosis': diagnosis,
                        'treatment': treatment,
                        'refraction_performed': refraction_performed,
                        'contact_lens_prescribed': contact_lens_prescribed,
                        'contact_lens_type': contact_lens_type
                    }
                    
                    # Add refraction data if available
                    if refraction_performed:
                        examination_data.update({
                            'sphere_od': sphere_od,
                            'cylinder_od': cylinder_od,
                            'axis_od': axis_od,
                            'addition_od': addition_od,
                            'pd_od': pd_od,
                            'sphere_os': sphere_os,
                            'cylinder_os': cylinder_os,
                            'axis_os': axis_os,
                            'addition_os': addition_os,
                            'pd_os': pd_os,
                            'refraction_type': refraction_type
                        })
                    
                    # Insert into database
                    placeholders = ', '.join(['?' for _ in examination_data])
                    columns = ', '.join(examination_data.keys())
                    values = list(examination_data.values())
                    
                    c.execute(f'''
                        INSERT INTO medical_examinations ({columns})
                        VALUES ({placeholders})
                    ''', values)
                    
                    conn.commit()
                    
                    # Reset session state
                    st.session_state.tono_od_clicked = False
                    st.session_state.tono_os_clicked = False
                    st.session_state.bio_od_clicked = False
                    st.session_state.bio_os_clicked = False
                    st.session_state.oft_od_clicked = False
                    st.session_state.oft_os_clicked = False
                    
                    if submit_button:
                        st.success("✅ Examination protocol successfully saved!")
                        st.balloons()
                    
                    if generate_report:
                        # Generate PDF report
                        patient_data = pd.read_sql(
                            "SELECT * FROM patients WHERE id = ?", 
                            conn, params=(patient_db_id,)
                        ).iloc[0]
                        
                        examination_data['visit_date'] = datetime.now().strftime('%d.%m.%Y.')
                        pdf_buffer = generate_pdf_report(patient_data, examination_data)
                        
                        st.success("✅ Report successfully generated!")
                        st.download_button(
                            label="📥 Download PDF Report",
                            data=pdf_buffer,
                            file_name=f"report_{patient_data['patient_id']}_{datetime.now().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf"
                        )
                    
                except Exception as e:
                    st.error(f"❌ Error saving: {str(e)}")
            else:
                st.error("❌ Patient not found in database")

# Patient Registration
def patient_registration():
    st.subheader("Patient Registration")
    
    with st.form("patient_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            first_name = st.text_input("First Name*")
            last_name = st.text_input("Last Name*")
            date_of_birth = st.date_input("Date of Birth*", max_value=datetime.now().date())
            gender = st.selectbox("Gender*", ["", "Male", "Female", "Other"])
        
        with col2:
            phone = st.text_input("Phone")
            email = st.text_input("Email")
            address = st.text_area("Address")
        
        submit_button = st.form_submit_button("Register Patient")
        
        if submit_button:
            if first_name and last_name and date_of_birth and gender:
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
                    st.success(f"Patient successfully registered! Patient ID: {patient_id}")
                except Exception as e:
                    st.error(f"Error registering patient: {str(e)}")
            else:
                st.error("Please fill all required fields (marked with *)")

# Patient Search
def patient_search():
    st.subheader("Patient Search and Records Review")
    
    conn = init_db()
    
    search_term = st.text_input("Search patients (name or ID)")
    
    if search_term:
        patients = pd.read_sql(
            """SELECT * FROM patients 
               WHERE first_name LIKE ? OR last_name LIKE ? OR patient_id LIKE ?""", 
            conn, params=(f"%{search_term}%", f"%{search_term}%", f"%{search_term}%")
        )
        
        if not patients.empty:
            st.dataframe(patients)
            
            # Show medical history for selected patient
            selected_patient_id = st.selectbox("Select patient for details", 
                                             patients['patient_id'].tolist())
            
            if selected_patient_id:
                medical_history = pd.read_sql(
                    """SELECT * FROM medical_examinations me
                       JOIN patients p ON me.patient_id = p.id
                       WHERE p.patient_id = ?""", 
                    conn, params=(selected_patient_id,)
                )
                
                if not medical_history.empty:
                    st.subheader("Examination History")
                    st.dataframe(medical_history)
                else:
                    st.info("No examination records found for this patient")
        else:
            st.info("No patients found matching search criteria")

# Analytics Dashboard
def show_analytics():
    st.subheader("Examination Analytics")
    
    conn = init_db()
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now().replace(day=1))
    with col2:
        end_date = st.date_input("End Date", datetime.now())
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_patients = pd.read_sql("SELECT COUNT(*) as count FROM patients", conn).iloc[0]['count']
        st.markdown(f"""
        <div class="metric-card">
            <h3 style='margin: 0; color: #1f77b4;'>{total_patients}</h3>
            <p style='margin: 0;'>Total Patients</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        total_examinations = pd.read_sql("SELECT COUNT(*) as count FROM medical_examinations", conn).iloc[0]['count']
        st.markdown(f"""
        <div class="metric-card">
            <h3 style='margin: 0; color: #1f77b4;'>{total_examinations}</h3>
            <p style='margin: 0;'>Total Examinations</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        refractions_count = pd.read_sql(
            "SELECT COUNT(*) as count FROM medical_examinations WHERE refraction_performed = 1", 
            conn
        ).iloc[0]['count']
        st.markdown(f"""
        <div class="metric-card">
            <h3 style='margin: 0; color: #1f77b4;'>{refractions_count}</h3>
            <p style='margin: 0;'>Refractions Performed</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        contact_lens_count = pd.read_sql(
            "SELECT COUNT(*) as count FROM medical_examinations WHERE contact_lens_prescribed = 1", 
            conn
        ).iloc[0]['count']
        st.markdown(f"""
        <div class="metric-card">
            <h3 style='margin: 0; color: #1f77b4;'>{contact_lens_count}</h3>
            <p style='margin: 0;'>Contact Lenses Prescribed</p>
        </div>
        """, unsafe_allow_html=True)

# Dashboard
def show_dashboard():
    st.subheader("Clinical Dashboard")
    
    # Quick stats
    conn = init_db()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        today = datetime.now().date()
        today_appointments = pd.read_sql(
            "SELECT COUNT(*) as count FROM appointments WHERE DATE(appointment_date) = ?", 
            conn, params=(today,)
        ).iloc[0]['count']
        st.metric("Today's Appointments", today_appointments)
    
    with col2:
        total_patients = pd.read_sql("SELECT COUNT(*) as count FROM patients", conn).iloc[0]['count']
        st.metric("Patients in System", total_patients)
    
    with col3:
        upcoming_appointments = pd.read_sql(
            "SELECT COUNT(*) as count FROM appointments WHERE DATE(appointment_date) >= ?", 
            conn, params=(today,)
        ).iloc[0]['count']
        st.metric("Scheduled Appointments", upcoming_appointments)
    
    with col4:
        monthly_exams = pd.read_sql(
            "SELECT COUNT(*) as count FROM medical_examinations WHERE strftime('%Y-%m', visit_date) = strftime('%Y-%m', 'now')", 
            conn
        ).iloc[0]['count']
        st.metric("Exams This Month", monthly_exams)
    
    # Quick links
    st.subheader("Quick Access")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("New Examination Protocol", use_container_width=True):
            st.session_state.current_page = "Examination Protocol"
    
    with col2:
        if st.button("Appointment Calendar", use_container_width=True):
            st.session_state.current_page = "Calendar"
    
    with col3:
        if st.button("Analytics", use_container_width=True):
            st.session_state.current_page = "Analytics"

# Main navigation
def examination_protocol():
    st.sidebar.title("OphtalCAM Navigation")
    menu = st.sidebar.selectbox("Menu", [
        "Dashboard",
        "Patient Registration", 
        "Examination Protocol",
        "Calendar",
        "Working Hours",
        "Patient Search",
        "Analytics"
    ])
    
    if menu == "Dashboard":
        show_dashboard()
    elif menu == "Patient Registration":
        patient_registration()
    elif menu == "Examination Protocol":
        medical_examination()
    elif menu == "Calendar":
        show_calendar()
    elif menu == "Working Hours":
        manage_working_hours()
    elif menu == "Patient Search":
        patient_search()
    elif menu == "Analytics":
        show_analytics()

# Main application flow
def main():
    load_css()
    
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
        # Header with logos for main app
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.image("https://i.postimg.cc/PrRFzQLv/Logo-Transparency-01.png", width=300)
        
        with col2:
            st.image("https://i.postimg.cc/qq656tks/Phantasmed-logo.png", width=150)
        
        # Logout button
        col1, col2, col3 = st.columns([2, 1, 1])
        with col3:
            if st.button("Logout"):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.session_state.role = None
                st.rerun()
        
        st.markdown("---")
        
        # Show user info
        st.sidebar.markdown(f"**Logged in as:** {st.session_state.username}")
        st.sidebar.markdown(f"**Role:** {st.session_state.role}")
        
        # Show examination protocol
        examination_protocol()

if __name__ == "__main__":
    main()
