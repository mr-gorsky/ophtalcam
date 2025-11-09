            # continuation of cycloplegic/subjective form
            with c4:
                cyclo_drops = st.number_input("Drops", min_value=1, max_value=10, value=1)
        else:
            cyclo_agent = ""
            cyclo_lot = ""
            cyclo_expiry = None
            cyclo_drops = None

        # Subjective fields (OD / OS) with VA + modifier
        sod, spacer, sos = st.columns([2,0.15,2])
        with sod:
            st.markdown("**Right eye (OD)**")
            subjective_od_sphere = st.number_input("Sphere OD", value=0.0, step=0.25, format="%.2f", key="subj_od_sph")
            subjective_od_cylinder = st.number_input("Cylinder OD", value=0.0, step=0.25, format="%.2f", key="subj_od_cyl")
            subjective_od_axis = st.number_input("Axis OD", min_value=0, max_value=180, value=0, key="subj_od_ax")
            subjective_od_va = st.text_input("Subjective VA OD", placeholder="e.g. 1.0 or 20/20")
            subjective_od_modifier = st.text_input("Modifier OD", placeholder="-2")
        with sos:
            st.markdown("**Left eye (OS)**")
            subjective_os_sphere = st.number_input("Sphere OS", value=0.0, step=0.25, format="%.2f", key="subj_os_sph")
            subjective_os_cylinder = st.number_input("Cylinder OS", value=0.0, step=0.25, format="%.2f", key="subj_os_cyl")
            subjective_os_axis = st.number_input("Axis OS", min_value=0, max_value=180, value=0, key="subj_os_ax")
            subjective_os_va = st.text_input("Subjective VA OS", placeholder="e.g. 1.0 or 20/20")
            subjective_os_modifier = st.text_input("Modifier OS", placeholder="-2")

        subjective_notes = st.text_area("Subjective notes", height=120)

        # Save subjective
        savesub = st.form_submit_button("Save subjective")
        if savesub:
            st.session_state.refraction.update({
                "cycloplegic_used": cyclo_used,
                "cycloplegic_agent": cyclo_agent,
                "cycloplegic_lot": cyclo_lot,
                "cycloplegic_expiry": cyclo_expiry,
                "cycloplegic_drops": cyclo_drops,
                "subjective_method": subj_method,
                "subjective_od_sphere": subjective_od_sphere,
                "subjective_od_cylinder": subjective_od_cylinder,
                "subjective_od_axis": subjective_od_axis,
                "subjective_od_va": subjective_od_va,
                "subjective_od_modifier": subjective_od_modifier,
                "subjective_os_sphere": subjective_os_sphere,
                "subjective_os_cylinder": subjective_os_cylinder,
                "subjective_os_axis": subjective_os_axis,
                "subjective_os_va": subjective_os_va,
                "subjective_os_modifier": subjective_os_modifier,
                "subjective_notes": subjective_notes
            })
            st.success("Subjective saved (session).")
            st.rerun()

    st.markdown("---")
    # Final prescription (aligned OD/OS)
    with st.form("refraction_final"):
        st.markdown("**Final Prescription / Binocular tests**")
        odc, spac, osc = st.columns([2,0.15,2])
        with odc:
            st.markdown("**Right (OD)**")
            final_od_sph = st.number_input("Final Sphere OD", value=0.0, step=0.25, format="%.2f", key="final_od_sph")
            final_od_cyl = st.number_input("Final Cylinder OD", value=0.0, step=0.25, format="%.2f", key="final_od_cyl")
            final_od_ax = st.number_input("Final Axis OD", min_value=0, max_value=180, value=0, key="final_od_ax")
        with osc:
            st.markdown("**Left (OS)**")
            final_os_sph = st.number_input("Final Sphere OS", value=0.0, step=0.25, format="%.2f", key="final_os_sph")
            final_os_cyl = st.number_input("Final Cylinder OS", value=0.0, step=0.25, format="%.2f", key="final_os_cyl")
            final_os_ax = st.number_input("Final Axis OS", min_value=0, max_value=180, value=0, key="final_os_ax")

        bin1, bin2 = st.columns([2,2])
        with bin1:
            final_bin_va = st.text_input("Final Binocular VA", placeholder="e.g. 1.0 or 20/20")
            final_bin_modifier = st.text_input("Final Binocular modifier", placeholder="-2")
            bvp = st.text_input("BVP")
            pinhole = st.text_input("Pinhole VA")
        with bin2:
            binocular_balance = st.selectbox("Binocular balance", ["Balanced","OD dominant","OS dominant","Unbalanced"])
            stereopsis = st.text_input("Stereopsis")
            npc_break = st.text_input("NPC Break")
            npc_recovery = st.text_input("NPC Recovery")
            binocular_tests_text = st.text_area("Binocular tests notes", height=100)

        prescription_notes = st.text_area("Prescription notes / rationale", height=120)

        savefinal = st.form_submit_button("Save & Finalize Refraction")
        if savefinal:
            try:
                # ensure patient internal id
                p_row = pd.read_sql("SELECT id FROM patients WHERE patient_id = ?", conn, params=(pinfo['patient_id'],)).iloc[0]
                pid = p_row['id']
                # prepare uploaded_files if any in session
                uploaded_files = st.session_state.refraction.get("uploaded_files", [])
                cur = conn.cursor()
                # Insert: columns list must match values tuple length
                cur.execute('''
                    INSERT INTO refraction_exams
                    (patient_id, habitual_type, habitual_od_va, habitual_od_modifier, habitual_os_va, habitual_os_modifier,
                     habitual_binocular_va, habitual_binocular_modifier, habitual_pd, habitual_notes, vision_notes,
                     uncorrected_od_va, uncorrected_od_modifier, uncorrected_os_va, uncorrected_os_modifier, uncorrected_binocular_va, uncorrected_binocular_modifier,
                     objective_method, objective_time, autorefractor_od_sphere, autorefractor_od_cylinder, autorefractor_od_axis,
                     autorefractor_os_sphere, autorefractor_os_cylinder, autorefractor_os_axis, objective_notes,
                     cycloplegic_used, cycloplegic_agent, cycloplegic_lot, cycloplegic_expiry, cycloplegic_drops,
                     subjective_method, subjective_od_sphere, subjective_od_cylinder, subjective_od_axis, subjective_od_va, subjective_od_modifier,
                     subjective_os_sphere, subjective_os_cylinder, subjective_os_axis, subjective_os_va, subjective_os_modifier, subjective_notes,
                     binocular_balance, stereopsis, near_point_convergence_break, near_point_convergence_recovery,
                     final_prescribed_od_sphere, final_prescribed_od_cylinder, final_prescribed_od_axis,
                     final_prescribed_os_sphere, final_prescribed_os_cylinder, final_prescribed_os_axis,
                     final_prescribed_binocular_va, final_prescribed_binocular_modifier, bvp, pinhole, prescription_notes,
                     binocular_tests, functional_tests, accommodation_tests, uploaded_files)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ''', (
                    pid,
                    st.session_state.refraction.get("habitual_type"),
                    st.session_state.refraction.get("habitual_od_va"),
                    st.session_state.refraction.get("habitual_od_modifier"),
                    st.session_state.refraction.get("habitual_os_va"),
                    st.session_state.refraction.get("habitual_os_modifier"),
                    st.session_state.refraction.get("habitual_binocular_va"),
                    st.session_state.refraction.get("habitual_binocular_modifier"),
                    st.session_state.refraction.get("habitual_pd"),
                    st.session_state.refraction.get("habitual_notes"),
                    st.session_state.refraction.get("vision_notes"),
                    st.session_state.refraction.get("uncorrected_od_va"),
                    st.session_state.refraction.get("uncorrected_od_modifier"),
                    st.session_state.refraction.get("uncorrected_os_va"),
                    st.session_state.refraction.get("uncorrected_os_modifier"),
                    st.session_state_
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
