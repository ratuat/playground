import streamlit as st
import requests
import json
from datetime import date

# --------------------
# Backend API endpoint
# --------------------
BACKEND_URL = st.secrets["BACKEND_URL"]  # Change to your backend URL
API_KEY = st.secrets["API_KEY"]

st.set_page_config(page_title="Patient Risk Dashboard", layout="wide")

st.title("💊 Patient Drug Risk Assessment")

# --------------------
# Input Sections
# --------------------
st.header("🧍 Patient Information")
col1, col2, col3 = st.columns(3)
with col1:
    age = st.number_input("Age", min_value=0, max_value=120, value=65)
    weight_kg = st.number_input("Weight (kg)", min_value=0.0, value=78.0)
    height_cm = st.number_input("Height (cm)", min_value=0.0, value=175.0)
with col2:
    sex = st.selectbox("Sex", ["male", "female", "other"])
    pregnancy_status = st.selectbox("Pregnancy Status", [None, "pregnant", "not_pregnant"])
    smoking_status = st.selectbox("Smoking Status", ["never", "former", "current"])
with col3:
    alcohol_use_status = st.selectbox("Alcohol Use", ["yes", "no"])
    alcohol_units_per_week = st.number_input("Alcohol Units/Week", min_value=0, value=5)

# --------------------
# Primary Diagnosis
# --------------------
st.header("🩺 Primary Diagnosis")
primary_description = st.text_input("Description", "Atherosclerotic heart disease of native coronary artery without angina pectoris")
primary_severity = st.selectbox("Severity", ["mild", "moderate", "severe"], index=1)
primary_onset_date = st.date_input("Onset Date", value=date(2022, 4, 15))

# --------------------
# Comorbidities
# --------------------
st.header("📋 Comorbidities")
comorbidities = []
with st.expander("Add Comorbidities"):
    num_comorbidities = st.number_input("Number of comorbidities", min_value=0, value=2)
    for i in range(num_comorbidities):
        c1, c2 = st.columns(2)
        with c1:
            desc = st.text_input(f"Comorbidity {i+1} Description", key=f"com_desc_{i}")
        with c2:
            severity = st.selectbox(f"Severity {i+1}", ["mild", "moderate", "severe"], key=f"com_sev_{i}")
        comorbidities.append({"description": desc, "severity": severity})

# --------------------
# Current Medications
# --------------------
st.header("💊 Current Medications")
current_medications = []
with st.expander("Add Medications"):
    num_meds = st.number_input("Number of medications", min_value=0, value=2)
    for i in range(num_meds):
        name = st.text_input(f"Medication {i+1} Name", key=f"med_name_{i}")
        dose = st.number_input(f"Dose (mg) {i+1}", min_value=0.0, key=f"med_dose_{i}")
        freq = st.number_input(f"Frequency per day {i+1}", min_value=0, key=f"med_freq_{i}")
        route = st.selectbox(f"Route {i+1}", ["oral", "iv", "im"], key=f"med_route_{i}")
        start_date = st.date_input(f"Start Date {i+1}", value=date(2021, 8, 1), key=f"med_start_{i}")
        current_medications.append({
            "name": name,
            "dose_mg": dose,
            "frequency_per_day": freq,
            "route": route,
            "start_date": str(start_date)
        })

# --------------------
# Proposed Drug
# --------------------
st.header("💡 Proposed Drug")
prop_name = st.text_input("Proposed Drug Name", "Rosuvastatin")
prop_dose = st.number_input("Proposed Dose (mg)", min_value=0.0, value=10.0)
prop_freq = st.number_input("Proposed Frequency per day", min_value=0, value=1)
prop_route = st.selectbox("Proposed Route", ["oral", "iv", "im"])
prop_start = st.date_input("Proposed Start Date", value=date.today())

# --------------------
# Lab Results
# --------------------
st.header("🧪 Lab Results")
lab_results = {
    "eGFR": st.number_input("eGFR", min_value=0, value=45),
    "creatinine_umol_L": st.number_input("Creatinine (µmol/L)", min_value=0, value=150),
    "ALT_U_L": st.number_input("ALT (U/L)", min_value=0, value=35),
    "AST_U_L": st.number_input("AST (U/L)", min_value=0, value=40),
    "hemoglobin_g_dL": st.number_input("Hemoglobin (g/dL)", min_value=0.0, value=14.2),
    "platelets_x10_9_L": st.number_input("Platelets (×10⁹/L)", min_value=0, value=210)
}

# --------------------
# Allergies
# --------------------
st.header("⚠ Allergies")
allergies = []
with st.expander("Add Allergies"):
    num_allergies = st.number_input("Number of allergies", min_value=0, value=1)
    for i in range(num_allergies):
        substance = st.text_input(f"Allergen {i+1}", key=f"allergy_sub_{i}")
        reaction = st.text_input(f"Reaction {i+1}", key=f"allergy_reac_{i}")
        allergies.append({"substance": substance, "reaction": reaction})

# --------------------
# Submit Button
# --------------------
if st.button("🔍 Analyze Risk"):
    payload = {
        "patient_info": {
            "age": age,
            "sex": sex,
            "weight_kg": weight_kg,
            "height_cm": height_cm,
            "pregnancy_status": pregnancy_status,
            "smoking_status": smoking_status,
            "alcohol_use": {
                "status": alcohol_use_status,
                "units_per_week": alcohol_units_per_week
            }
        },
        "primary_diagnosis": {
            "description": primary_description,
            "severity": primary_severity,
            "onset_date": str(primary_onset_date)
        },
        "comorbidities": comorbidities,
        "current_medications": current_medications,
        "proposed_drug": {
            "name": prop_name,
            "dose_mg": prop_dose,
            "frequency_per_day": prop_freq,
            "route": prop_route,
            "start_date": str(prop_start)
        },
        "lab_results": lab_results,
        "allergies": allergies
    }

    try:
        response = requests.post(BACKEND_URL, 
                                 headers={"Authorization": f"Bearer {API_KEY}"},
                                 json=payload)
        
        
        response.raise_for_status()
        result = response.json()

        # --------------------
        # Display Results
        # --------------------
        st.subheader("📊 Overall Risk")
        st.metric("Risk Score (%)", result['overall_risk']['score_percent'])
        st.metric("Risk Category", result['overall_risk']['category'])
        st.write(result['overall_risk']['interpretation'])

        st.subheader("📈 Risk Breakdown")
        st.write("**Systemic Risks:**")
        st.table(result['risk_breakdown']['systemic_risks'])
        st.write("**Comorbidity Impact:**")
        st.table(result['risk_breakdown']['comorbidity_impact'])

        st.subheader("💊 Drug Interactions")
        st.table(result['drug_interactions'])

        st.subheader("⚠ Special Population Warnings")
        st.table(result['special_population_warnings'])

        st.subheader("🔄 Alternative Drugs")
        st.table(result['alternative_drugs'])

        st.subheader("📝 Summary")
        st.write(result['summary'])

        st.download_button(
            "📥 Download Results JSON",
            data=json.dumps(result, indent=2),
            file_name="risk_assessment.json",
            mime="application/json"
        )

    except Exception as e:
        st.error(f"Error: {e}")
