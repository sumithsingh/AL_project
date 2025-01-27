import streamlit as st
import requests
from PIL import Image
import io

def main():
    st.set_page_config(page_title="Blood Cancer Detection System", layout="wide")
    
    # Initialize session state variables
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user_role = None
        st.session_state.user_token = None

    # Main application flow
    if not st.session_state.authenticated:
        show_login()
    else:
        show_main_interface()

def show_login():
    st.title("Blood Cancer Detection System")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            try:
                response = requests.post(
                    "http://localhost:8000/login",
                    data={"username": username, "password": password}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.authenticated = True
                    st.session_state.user_role = data["role"]
                    st.session_state.user_token = data["access_token"]
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            except Exception as e:
                st.error(f"Connection error: {str(e)}")

def show_main_interface():
    st.sidebar.title("Navigation")
    
    # Different navigation options based on user role
    if st.session_state.user_role == "doctor":
        page = st.sidebar.radio(
            "Select Page",
            ["Upload Analysis", "Patient Dashboard", "Chat Interface"]
        )
    else:
        page = st.sidebar.radio(
            "Select Page",
            ["Upload Analysis", "View Results", "Chat Interface"]
        )
    
    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.user_role = None
        st.session_state.user_token = None
        st.rerun()
    
    # Page routing
    if page == "Upload Analysis":
        show_upload_page()
    elif page == "Patient Dashboard":
        show_dashboard()
    elif page == "Chat Interface":
        show_chat_interface()
    elif page == "View Results":
        show_results()

def show_upload_page():
    st.title("Blood Cell Analysis")
    uploaded_file = st.file_uploader("Upload blood cell image", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_container_width=True)
        
        if st.button("Analyze Image"):
            files = {"file": uploaded_file.getvalue()}
            headers = {"Authorization": f"Bearer {st.session_state.user_token}"}
            
            with st.spinner("Analyzing image..."):
                try:
                    response = requests.post(
                        "http://localhost:8000/analyze",
                        files=files,
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        results = response.json()
                        display_results(results)
                    else:
                        st.error("Error analyzing image")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

def display_results(results):
    st.header("Analysis Results")
    
    # Cell type distribution
    st.subheader("Cell Type Distribution")
    cols = st.columns(len(results["cell_counts"]))
    for i, (cell_type, count) in enumerate(results["cell_counts"].items()):
        with cols[i]:
            st.metric(
                label=cell_type.replace("_", " ").title(),
                value=f"{count:.1f}%"
            )
    
    # Risk assessment
    st.subheader("Risk Assessment")
    risk_level = results["risk_assessment"]
    if "High" in risk_level:
        st.error(risk_level)
    elif "Moderate" in risk_level:
        st.warning(risk_level)
    else:
        st.success(risk_level)
    
    # Recommendations
    st.subheader("Recommendations")
    for rec in results["recommendations"]:
        st.write(f"• {rec}")

def show_dashboard():
    st.title("Doctor Dashboard")
    
    try:
        headers = {"Authorization": f"Bearer {st.session_state.user_token}"}
        response = requests.get(
            "http://localhost:8000/patients",
            headers=headers
        )
        
        if response.status_code == 200:
            patients = response.json()
            
            # Patient selector
            selected_patient = st.selectbox(
                "Select Patient",
                patients,
                format_func=lambda x: f"{x['username']} (ID: {x['id']})"
            )
            
            if selected_patient:
                show_patient_details(selected_patient)
        else:
            st.error("Error fetching patient list")
    except Exception as e:
        st.error(f"Error: {str(e)}")

def show_patient_details(patient):
    st.subheader(f"Patient: {patient['username']}")
    
    try:
        headers = {"Authorization": f"Bearer {st.session_state.user_token}"}
        response = requests.get(
            f"http://localhost:8000/patient/{patient['id']}/history",
            headers=headers
        )
        
        if response.status_code == 200:
            history = response.json()
            if not history:
                st.info("No test history available")
            else:
                for test in history:
                    with st.expander(f"Test - {test['date']}"):
                        display_results(test['results'])
        else:
            st.error("Error fetching patient history")
    except Exception as e:
        st.error(f"Error: {str(e)}")

def show_chat_interface():
    st.title("Medical Consultation Chat")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about your results..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        try:
            headers = {"Authorization": f"Bearer {st.session_state.user_token}"}
            response = requests.post(
                "http://localhost:8000/chat",
                json={"text": prompt},
                headers=headers
            )
            
            if response.status_code == 200:
                ai_message = response.json()["response"]
                st.session_state.messages.append(
                    {"role": "assistant", "content": ai_message}
                )
                with st.chat_message("assistant"):
                    st.markdown(ai_message)
            else:
                st.error("Error getting response")
        except Exception as e:
            st.error(f"Error: {str(e)}")

def show_results():
    st.title("Your Test Results")
    
    try:
        headers = {"Authorization": f"Bearer {st.session_state.user_token}"}
        response = requests.get(
            f"http://localhost:8000/patient/{st.session_state.user_id}/history",
            headers=headers
        )
        
        if response.status_code == 200:
            history = response.json()
            if not history:
                st.info("No test results available")
            else:
                for test in history:
                    with st.expander(f"Test Result - {test['date']}"):
                        display_results(test['results'])
        else:
            st.error("Error fetching results")
    except Exception as e:
        st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()