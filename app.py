import streamlit as st
import requests
import json
from datetime import date
import pandas as pd
import time
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# --------------------
# Backend API endpoint
# --------------------
BACKEND_URL = st.secrets["BACKEND_URL"]  # Change to your backend URL
API_KEY = st.secrets["API_KEY"]

st.set_page_config(page_title="Patient Risk Dashboard", layout="wide")

# Custom CSS for styling - FIXED CONTRAST ISSUES
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        color: #333333 !important;
    }
    .risk-high {
        border-left-color: #dc3545;
    }
    .risk-moderate {
        border-left-color: #ffc107;
    }
    .risk-low {
        border-left-color: #28a745;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #dee2e6;
    }
    .stMetric label {
        font-weight: bold;
        color: #495057 !important;
    }
    .stMetric div {
        font-size: 1.5rem;
        font-weight: bold;
        color: #212529 !important;
    }
    .welcome-container {
        text-align: center;
        padding: 40px;
        background-color: #f8f9fa;
        border-radius: 10px;
        color: #333333 !important;
        border: 1px solid #dee2e6;
    }
    .welcome-container h3 {
        color: #1f77b4 !important;
        margin-bottom: 15px;
    }
    .welcome-container p {
        color: #495057 !important;
        font-size: 1.1rem;
        line-height: 1.6;
    }
    /* Ensure all text has proper contrast */
    .stMarkdown, .stText, .stInfo, .stSuccess, .stWarning, .stError {
        color: #333333 !important;
    }
    /* Custom tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 8px 8px 0px 0px;
        padding: 10px 16px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1f77b4;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">💊 Patient Drug Risk Assessment</h1>', unsafe_allow_html=True)

# Initialize session state for analysis results
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'is_analyzing' not in st.session_state:
    st.session_state.is_analyzing = False
if 'patient_data' not in st.session_state:
    st.session_state.patient_data = {}

# --------------------
# SIDEBAR - Input Sections
# --------------------
with st.sidebar:
    st.header("🧍 Patient Information")
    
    with st.expander("Demographics", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input("Age", min_value=0, max_value=120, value=65)
            weight_kg = st.number_input("Weight (kg)", min_value=0.0, value=78.0)
        with col2:
            sex = st.selectbox("Sex", ["male", "female", "other"])
            height_cm = st.number_input("Height (cm)", min_value=0.0, value=175.0)
        
        ethnicity = st.text_input("Ethnicity", "Caucasian")
        pregnancy_status = st.selectbox("Pregnancy Status", [None, "pregnant", "not_pregnant"])

    with st.expander("Lifestyle", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            smoking_status = st.selectbox("Smoking Status", ["never", "former", "current"])
            pack_years = st.number_input("Pack Years", min_value=0, value=20)
        with col2:
            alcohol_use_status = st.selectbox("Alcohol Use", ["yes", "no"])
            alcohol_units_per_week = st.number_input("Alcohol Units/Week", min_value=0, value=5)
        alcohol_type = st.text_input("Alcohol Type", "wine")

    with st.expander("Vitals", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            bp_systolic = st.number_input("Systolic BP (mmHg)", min_value=0, value=138)
            heart_rate = st.number_input("Heart Rate (bpm)", min_value=0, value=68)
        with col2:
            bp_diastolic = st.number_input("Diastolic BP (mmHg)", min_value=0, value=82)
            vitals_last_measured = st.date_input("Last Measured", value=date(2025, 8, 8))

    with st.expander("Primary Diagnosis", expanded=True):
        primary_description = st.text_input("Description", "Atherosclerotic heart disease of native coronary artery without angina pectoris")
        col1, col2 = st.columns(2)
        with col1:
            primary_severity = st.selectbox("Severity", ["mild", "moderate", "severe", "controlled"], index=1)
        with col2:
            primary_onset_date = st.date_input("Onset Date", value=date(2022, 4, 15))

    with st.expander("Comorbidities", expanded=False):
        comorbidities = []
        num_comorbidities = st.number_input("Number of comorbidities", min_value=0, value=3, key="comorbidities_num")
        for i in range(num_comorbidities):
            st.subheader(f"Comorbidity {i+1}")
            desc = st.text_input(f"Description {i+1}", 
                                value=["Type 2 diabetes mellitus without complications", 
                                      "Chronic kidney disease, stage 3", 
                                      "Essential (primary) hypertension"][i] if i < 3 else "",
                                key=f"com_desc_{i}")
            col1, col2 = st.columns(2)
            with col1:
                severity = st.selectbox(f"Severity {i+1}", ["mild", "moderate", "severe", "controlled"], 
                                       index=[0, 1, 3][i] if i < 3 else 0, key=f"com_sev_{i}")
            with col2:
                date_diagnosed = st.date_input(f"Date Diagnosed {i+1}", 
                                              value=[date(2019, 11, 1), date(2023, 1, 15), date(2018, 5, 20)][i] if i < 3 else date.today(),
                                              key=f"com_date_{i}")
            comorbidities.append({
                "description": desc, 
                "severity": severity,
                "date_diagnosed": str(date_diagnosed)
            })

    with st.expander("Medical History", expanded=False):
        medical_history = []
        num_history = st.number_input("Number of medical history items", min_value=0, value=1, key="history_num")
        for i in range(num_history):
            desc = st.text_input(f"History Description {i+1}", 
                                value="Percutaneous Coronary Intervention (PCI) with stent" if i == 0 else "",
                                key=f"hist_desc_{i}")
            hist_date = st.date_input(f"Date {i+1}", 
                                     value=date(2022, 4, 20) if i == 0 else date.today(),
                                     key=f"hist_date_{i}")
            medical_history.append({
                "description": desc,
                "date": str(hist_date)
            })

    with st.expander("Family History", expanded=False):
        family_history = []
        num_family = st.number_input("Number of family history items", min_value=0, value=1, key="family_num")
        for i in range(num_family):
            col1, col2 = st.columns(2)
            with col1:
                relation = st.text_input(f"Relation {i+1}", "father", key=f"fam_rel_{i}")
            with col2:
                condition = st.text_input(f"Condition {i+1}", "Myocardial Infarction", key=f"fam_cond_{i}")
            age_diagnosis = st.number_input(f"Age at Diagnosis {i+1}", min_value=0, value=58, key=f"fam_age_{i}")
            family_history.append({
                "relation": relation,
                "condition": condition,
                "age_at_diagnosis": age_diagnosis
            })

    with st.expander("Current Medications", expanded=False):
        current_medications = []
        num_meds = st.number_input("Number of medications", min_value=0, value=4, key="meds_num")
        for i in range(num_meds):
            st.subheader(f"Medication {i+1}")
            name = st.text_input(f"Name {i+1}", 
                                value=["Metformin", "Aspirin", "Lisinopril", "Omeprazole"][i] if i < 4 else "",
                                key=f"med_name_{i}")
            col1, col2 = st.columns(2)
            with col1:
                dose = st.number_input(f"Dose (mg) {i+1}", min_value=0.0, 
                                      value=[500.0, 81.0, 10.0, 20.0][i] if i < 4 else 0.0,
                                      key=f"med_dose_{i}")
            with col2:
                freq = st.number_input(f"Frequency per day {i+1}", min_value=0, 
                                      value=[2, 1, 1, 1][i] if i < 4 else 1,
                                      key=f"med_freq_{i}")
            route = st.selectbox(f"Route {i+1}", ["oral", "iv", "im"], key=f"med_route_{i}")
            start_date = st.date_input(f"Start Date {i+1}", 
                                      value=[date(2021, 8, 1), date(2020, 5, 15), date(2020, 5, 15), date(2021, 10, 10)][i] if i < 4 else date.today(),
                                      key=f"med_start_{i}")
            current_medications.append({
                "name": name,
                "dose_mg": dose,
                "frequency_per_day": freq,
                "route": route,
                "start_date": str(start_date)
            })

    with st.expander("Proposed Drug", expanded=True):
        prop_name = st.text_input("Proposed Drug Name", "Rosuvastatin")
        col1, col2 = st.columns(2)
        with col1:
            prop_dose = st.number_input("Proposed Dose (mg)", min_value=0.0, value=10.0)
        with col2:
            prop_freq = st.number_input("Proposed Frequency per day", min_value=0, value=1)
        prop_route = st.selectbox("Proposed Route", ["oral", "iv", "im"])
        prop_start = st.date_input("Proposed Start Date", value=date(2025, 8, 10))

    with st.expander("Lab Results", expanded=False):
        st.subheader("Lipid Panel")
        col1, col2 = st.columns(2)
        with col1:
            total_chol = st.number_input("Total Cholesterol (mg/dL)", min_value=0, value=245)
            ldl = st.number_input("LDL Cholesterol (mg/dL)", min_value=0, value=165)
        with col2:
            hdl = st.number_input("HDL Cholesterol (mg/dL)", min_value=0, value=38)
            trig = st.number_input("Triglycerides (mg/dL)", min_value=0, value=210)
        lipid_date = st.date_input("Lipid Panel Date", value=date(2025, 8, 1))

        st.subheader("Metabolic Panel")
        col1, col2 = st.columns(2)
        with col1:
            egfr = st.number_input("eGFR (mL/min)", min_value=0, value=45)
            creat = st.number_input("Creatinine (µmol/L)", min_value=0, value=150)
        with col2:
            alt = st.number_input("ALT (U/L)", min_value=0, value=35)
            ast = st.number_input("AST (U/L)", min_value=0, value=40)
        
        col1, col2 = st.columns(2)
        with col1:
            albumin = st.number_input("Albumin (g/dL)", min_value=0.0, value=4.0)
        with col2:
            bilirubin = st.number_input("Bilirubin Total (mg/dL)", min_value=0.0, value=0.8)

        st.subheader("Hematology")
        col1, col2 = st.columns(2)
        with col1:
            hgb = st.number_input("Hemoglobin (g/dL)", min_value=0.0, value=14.2)
        with col2:
            platelets = st.number_input("Platelets (×10⁹/L)", min_value=0, value=210)

        st.subheader("Endocrine")
        col1, col2 = st.columns(2)
        with col1:
            hba1c = st.number_input("HbA1c (%)", min_value=0.0, value=6.8)
        with col2:
            tsh = st.number_input("TSH (mIU/L)", min_value=0.0, value=2.5)

    with st.expander("Allergies", expanded=False):
        allergies = []
        num_allergies = st.number_input("Number of allergies", min_value=0, value=1, key="allergies_num")
        for i in range(num_allergies):
            col1, col2 = st.columns(2)
            with col1:
                substance = st.text_input(f"Allergen {i+1}", "Penicillin", key=f"allergy_sub_{i}")
            with col2:
                reaction = st.text_input(f"Reaction {i+1}", "rash", key=f"allergy_reac_{i}")
            allergies.append({"substance": substance, "reaction": reaction})

    with st.expander("Lifestyle Details", expanded=False):
        diet = st.text_input("Diet", "moderate in saturated fat")
        exercise = st.text_input("Exercise Frequency", "2-3 days per week")

    # Store patient data for visualization
    st.session_state.patient_data = {
        "age": age,
        "sex": sex,
        "weight_kg": weight_kg,
        "height_cm": height_cm,
        "bp_systolic": bp_systolic,
        "bp_diastolic": bp_diastolic,
        "heart_rate": heart_rate,
        "total_chol": total_chol,
        "ldl": ldl,
        "hdl": hdl,
        "trig": trig,
        "egfr": egfr,
        "hba1c": hba1c,
        "comorbidities": comorbidities,
        "current_medications": current_medications
    }

    # Submit Button in Sidebar
    if st.button("🔍 Analyze Risk", type="primary", use_container_width=True):
        st.session_state.is_analyzing = True
        st.session_state.analysis_results = None

        payload = {
            "patient_info": {
                "age": age,
                "sex": sex,
                "ethnicity": ethnicity,
                "weight_kg": weight_kg,
                "height_cm": height_cm,
                "pregnancy_status": pregnancy_status,
                "smoking_status": smoking_status,
                "pack_years": pack_years,
                "alcohol_use": {
                    "status": alcohol_use_status,
                    "units_per_week": alcohol_units_per_week,
                    "type": alcohol_type
                }
            },
            "vitals": {
                "blood_pressure_mmHg": {
                    "systolic": bp_systolic,
                    "diastolic": bp_diastolic
                },
                "heart_rate_bpm": heart_rate,
                "last_measured": str(vitals_last_measured)
            },
            "primary_diagnosis": {
                "description": primary_description,
                "severity": primary_severity,
                "onset_date": str(primary_onset_date)
            },
            "comorbidities": comorbidities,
            "medical_history": medical_history,
            "family_history": family_history,
            "current_medications": current_medications,
            "proposed_drug": {
                "name": prop_name,
                "dose_mg": prop_dose,
                "frequency_per_day": prop_freq,
                "route": prop_route,
                "start_date": str(prop_start)
            },
            "lab_results": {
                "lipid_panel": {
                    "total_cholesterol_mg_dL": total_chol,
                    "LDL_cholesterol_mg_dL": ldl,
                    "HDL_cholesterol_mg_dL": hdl,
                    "triglycerides_mg_dL": trig,
                    "drawn_date": str(lipid_date)
                },
                "metabolic_panel": {
                    "eGFR_ml_min": egfr,
                    "creatinine_umol_L": creat,
                    "ALT_U_L": alt,
                    "AST_U_L": ast,
                    "albumin_g_dL": albumin,
                    "bilirubin_total_mg_dL": bilirubin
                },
                "hematology": {
                    "hemoglobin_g_dL": hgb,
                    "platelets_x10_9_L": platelets
                },
                "endocrine": {
                    "HbA1c_percent": hba1c,
                    "TSH_mIU_L": tsh
                }
            },
            "allergies": allergies,
            "lifestyle": {
                "diet": diet,
                "exercise_frequency": exercise
            }
        }

        try:
            # Show progress spinner
            with st.spinner("🧠 Analyzing patient data and calculating risks..."):
                # Simulate some processing time for better UX
                time.sleep(1)
                
                response = requests.post(BACKEND_URL, 
                                     headers={"Authorization": f"Bearer {API_KEY}"},
                                     json=payload)
            
            response.raise_for_status()
            result = response.json()
            st.session_state.analysis_results = result
            st.session_state.is_analyzing = False
            st.rerun()

        except Exception as e:
            st.error(f"Error: {e}")
            st.session_state.is_analyzing = False

# --------------------
# VISUALIZATION FUNCTIONS
# --------------------
def create_patient_summary_charts(patient_data):
    """Create charts for patient summary"""
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Blood Pressure', 'Lipid Profile', 'Kidney Function', 'Medications'),
        specs=[[{"type": "indicator"}, {"type": "bar"}],
               [{"type": "indicator"}, {"type": "pie"}]]
    )
    
    # Blood Pressure indicator
    fig.add_trace(go.Indicator(
        mode = "number+gauge", 
        value = patient_data["bp_systolic"],
        number = {"suffix": "/" + str(patient_data["bp_diastolic"]) + " mmHg"},
        domain = {'x': [0.25, 0.75], 'y': [0.7, 0.9]},
        gauge = {
            'shape': "bullet",
            'axis': {'range': [80, 200]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [80, 120], 'color': "lightgreen"},
                {'range': [120, 140], 'color': "yellow"},
                {'range': [140, 200], 'color': "red"}
            ]
        }
    ), row=1, col=1)
    
    # Lipid Profile bar chart
    lipids = ['Total Cholesterol', 'LDL', 'HDL', 'Triglycerides']
    values = [patient_data["total_chol"], patient_data["ldl"], patient_data["hdl"], patient_data["trig"]]
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    fig.add_trace(go.Bar(
        x=lipids,
        y=values,
        marker_color=colors,
        text=values,
        textposition='auto',
    ), row=1, col=2)
    
    # Kidney Function indicator
    fig.add_trace(go.Indicator(
        mode = "number+gauge", 
        value = patient_data["egfr"],
        number = {"suffix": " mL/min"},
        domain = {'x': [0.25, 0.75], 'y': [0.1, 0.3]},
        gauge = {
            'shape': "bullet",
            'axis': {'range': [0, 120]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [90, 120], 'color': "lightgreen"},
                {'range': [60, 90], 'color': "yellow"},
                {'range': [30, 60], 'color': "orange"},
                {'range': [0, 30], 'color': "red"}
            ]
        }
    ), row=2, col=1)
    
    # Medications pie chart
    med_names = [med["name"] for med in patient_data["current_medications"]]
    med_counts = [1] * len(med_names)  # Simple count for pie chart
    
    fig.add_trace(go.Pie(
        labels=med_names,
        values=med_counts,
        hole=.4,
        textinfo='label+percent',
        insidetextorientation='radial'
    ), row=2, col=2)
    
    fig.update_layout(height=600, showlegend=False, title_text="Patient Health Summary", title_x=0.5)
    return fig

def create_risk_breakdown_chart(risk_breakdown):
    """Create a radar chart for risk breakdown"""
    categories = [risk['category'] for risk in risk_breakdown['systemic_risks']]
    values = [risk['risk_level_num'] for risk in risk_breakdown['systemic_risks']]
    
    fig = go.Figure(data=go.Scatterpolar(
        r=values + [values[0]],  # Close the circle
        theta=categories + [categories[0]],  # Close the circle
        fill='toself',
        line=dict(color='#1f77b4'),
        name="Risk Levels"
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )),
        showlegend=False,
        title="Risk Breakdown by Category",
        title_x=0.5
    )
    
    return fig

def create_comorbidity_impact_chart(comorbidity_impact):
    """Create a bar chart for comorbidity impact"""
    comorbidities = [comorbidity['comorbidity'] for comorbidity in comorbidity_impact]
    impacts = [comorbidity['impact_level_num'] for comorbidity in comorbidity_impact]
    
    # Color based on impact level
    colors = []
    for impact in impacts:
        if impact >= 7:
            colors.append('#dc3545')  # High risk - red
        elif impact >= 4:
            colors.append('#ffc107')  # Medium risk - yellow
        else:
            colors.append('#28a745')  # Low risk - green
    
    fig = go.Figure(data=[go.Bar(
        x=comorbidities,
        y=impacts,
        marker_color=colors,
        text=impacts,
        textposition='auto',
    )])
    
    fig.update_layout(
        title="Comorbidity Impact on Drug Risk",
        xaxis_title="Comorbidities",
        yaxis_title="Impact Level",
        yaxis=dict(range=[0, 10]),
        title_x=0.5
    )
    
    return fig

def create_alternative_drugs_chart(alternative_drugs):
    """Create a comparison chart for alternative drugs"""
    drugs = [drug['name'] for drug in alternative_drugs]
    efficacy = [drug['efficacy_score'] for drug in alternative_drugs]
    safety = [drug['safety_score'] for drug in alternative_drugs]
    
    fig = go.Figure(data=[
        go.Bar(name='Efficacy', x=drugs, y=efficacy, marker_color='#1f77b4'),
        go.Bar(name='Safety', x=drugs, y=safety, marker_color='#2ca02c')
    ])
    
    fig.update_layout(
        barmode='group',
        title="Alternative Drugs: Efficacy vs Safety",
        xaxis_title="Drugs",
        yaxis_title="Score",
        yaxis=dict(range=[0, 10]),
        title_x=0.5
    )
    
    return fig

# --------------------
# MAIN CONTENT - Results Display
# --------------------
if st.session_state.is_analyzing:
    # Show loading animation in main content area
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write("")  # Spacer
        st.write("")  # Spacer
        with st.container():
            st.markdown("<div style='text-align: center; color: #333333;'>", unsafe_allow_html=True)
            st.spinner("⚡ Analyzing risks...")
            st.progress(0, text="Processing patient data")
            st.write("**Please wait while we analyze the risks...**")
            st.write("This may take a few moments")
            st.markdown("</div>", unsafe_allow_html=True)
        st.write("")  # Spacer
        st.write("")  # Spacer

elif st.session_state.analysis_results:
    result = st.session_state.analysis_results
    
    # --------------------
    # Display Results in Main Area
    # --------------------
    st.subheader("👤 Patient Health Summary")
    summary_fig = create_patient_summary_charts(st.session_state.patient_data)
    st.plotly_chart(summary_fig, use_container_width=True)
    
    st.subheader("📊 Overall Risk Assessment")
    
    # Determine risk class for styling
    risk_score = result['overall_risk']['score_percent']
    if risk_score >= 70:
        risk_class = "risk-high"
        risk_color = "#dc3545"
    elif risk_score >= 30:
        risk_class = "risk-moderate"
        risk_color = "#ffc107"
    else:
        risk_class = "risk-low"
        risk_color = "#28a745"
    
    # Create metric cards with better styling
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Risk Score (%)", f"{risk_score}", help="Overall risk percentage")
    with col2:
        st.metric("Risk Category", result['overall_risk']['category'].title(), help="Risk classification")
    with col3:
        st.metric("Recommended Action", 
                 "Monitor Closely" if risk_score >= 70 else "Standard Monitoring" if risk_score >= 30 else "Low Monitoring",
                 help="Recommended clinical action")
    
    # Risk gauge chart
    gauge_fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = risk_score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Overall Risk Score", 'font': {'size': 24}},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': risk_color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 30], 'color': '#28a745'},
                {'range': [30, 70], 'color': '#ffc107'},
                {'range': [70, 100], 'color': '#dc3545'}],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': risk_score}}))
    
    gauge_fig.update_layout(height=300)
    st.plotly_chart(gauge_fig, use_container_width=True)
    
    # Interpretation in a styled card
    st.markdown(f"""
    <div class="metric-card {risk_class}">
        <h4 style='color: #333333;'>📋 Interpretation</h4>
        <p style='color: #333333;'>{result['overall_risk']['interpretation']}</p>
        <p style='color: #333333;'><strong>Detailed Analysis:</strong> {result['overall_risk']['description']}</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("📈 Risk Breakdown")
    
    tab1, tab2, tab3 = st.tabs(["Risk Radar", "Systemic Risks Table", "Comorbidity Impact"])
    
    with tab1:
        radar_fig = create_risk_breakdown_chart(result['risk_breakdown'])
        st.plotly_chart(radar_fig, use_container_width=True)
    
    with tab2:
        systemic_risks_df = pd.DataFrame(result['risk_breakdown']['systemic_risks'])
        st.dataframe(systemic_risks_df, use_container_width=True)
    
    with tab3:
        comorbidity_impact_df = pd.DataFrame(result['risk_breakdown']['comorbidity_impact'])
        comorbidity_fig = create_comorbidity_impact_chart(result['risk_breakdown']['comorbidity_impact'])
        st.plotly_chart(comorbidity_fig, use_container_width=True)
        st.dataframe(comorbidity_impact_df, use_container_width=True)

    st.subheader("💊 Drug Interactions")
    interactions_df = pd.DataFrame(result['drug_interactions'])
    st.dataframe(interactions_df, use_container_width=True)

    st.subheader("⚠ Special Population Warnings")
    warnings_df = pd.DataFrame(result['special_population_warnings'])
    st.dataframe(warnings_df, use_container_width=True)

    st.subheader("🔄 Alternative Drugs")
    alternatives_df = pd.DataFrame(result['alternative_drugs'])
    alternatives_fig = create_alternative_drugs_chart(result['alternative_drugs'])
    st.plotly_chart(alternatives_fig, use_container_width=True)
    st.dataframe(alternatives_df, use_container_width=True)

    st.subheader("📝 Clinical Summary")
    st.info(result['summary'])

    # Download button
    st.download_button(
        "📥 Download Full Risk Assessment Report",
        data=json.dumps(result, indent=2),
        file_name="risk_assessment_report.json",
        mime="application/json",
        use_container_width=True
    )

else:
    # Welcome/instructions when no analysis has been done yet - FIXED WHITE TEXT ISSUE
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write("")  # Spacer
        st.markdown("""
        <div class='welcome-container'>
            <h3>👋 Welcome to the Patient Risk Assessment Tool</h3>
            <p>Please fill out the patient information in the sidebar and click <strong>"Analyze Risk"</strong> to get started.</p>
            <p>This tool will help you assess medication risks based on patient-specific factors.</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")  # Spacer
        
        # Show sample visualizations to demonstrate capabilities
        st.subheader("📊 Sample Visualizations")
        
        # Sample risk gauge
        sample_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = 45,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Sample Risk Score", 'font': {'size': 20}},
            gauge = {
                'axis': {'range': [0, 100]},
                'bar': {'color': "#ffc107"},
                'steps': [
                    {'range': [0, 30], 'color': '#28a745'},
                    {'range': [30, 70], 'color': '#ffc107'},
                    {'range': [70, 100], 'color': '#dc3545'}]}))
        
        sample_gauge.update_layout(height=300)
        st.plotly_chart(sample_gauge, use_container_width=True)
        
        # Sample patient summary
        st.info("After submitting patient data, you'll see detailed health summary visualizations here.")