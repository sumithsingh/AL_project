import streamlit as st
import requests
from PIL import Image
import io
import json
from datetime import datetime

class BloodCancerApp:
    def __init__(self):
        st.set_page_config(
            page_title="Blood Cancer Detection System",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        self.initialize_session()
        self.API_URL = "http://localhost:8000"

    def initialize_session(self):
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
            st.session_state.user_type = None
            st.session_state.user_token = None
            st.session_state.language = "English"
            st.session_state.show_assistant = False
            st.session_state.chat_history = []
            st.session_state.user_id = None

    def main(self):
        self.set_custom_css()
        
        if not st.session_state.authenticated:
            self.show_auth_page()
        else:
            if st.session_state.user_type == "patient":
                self.show_patient_interface()
            else:
                self.show_doctor_interface()

    def set_custom_css(self):
        st.markdown("""
            <style>
            .stButton button {
                width: 100%;
                border-radius: 20px;
                background-color: #2A3B8F;
                color: white;
            }
            .chat-container {
                background: white;
                border-radius: 10px;
                padding: 20px;
                margin-top: 10px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }
            .assistant-message {
                background: #E3F2FD;
                padding: 10px 15px;
                border-radius: 15px;
                margin: 5px 0;
            }
            .user-message {
                background: #F5F5F5;
                padding: 10px 15px;
                border-radius: 15px;
                margin: 5px 0;
                text-align: right;
            }
            .upload-section {
                border: 2px dashed #1E88E5;
                border-radius: 10px;
                padding: 20px;
                text-align: center;
            }
            .results-container {
                margin-top: 20px;
                padding: 20px;
                border-radius: 10px;
                background: white;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .metric-container {
                padding: 10px;
                border-radius: 8px;
                background: #f8f9fa;
                margin: 5px 0;
            }
            .emergency-alert {
                background-color: #ffebee;
                color: #c62828;
                padding: 1rem;
                border-radius: 0.5rem;
                margin: 1rem 0;
                border: 1px solid #ef5350;
            }
            .relevant-info {
                background-color: #e3f2fd;
                padding: 1rem;
                border-radius: 0.5rem;
                margin: 0.5rem 0;
            }
            .chat-meta {
                font-size: 0.8rem;
                color: #666;
                margin-top: 0.25rem;
            }
            </style>
        """, unsafe_allow_html=True)

    def show_auth_page(self):
        st.title("Blood Cancer Detection System")
        
        auth_action = st.radio("Choose action", ["Login", "Sign Up"])
        
        col1, col2 = st.columns(2)
        
        with col1:
            user_type = st.radio("Select user type", ["Patient", "Doctor"])
        
        with col2:
            with st.form(f"{auth_action}_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                email = st.text_input("Email") if auth_action == "Sign Up" else None
                
                submitted = st.form_submit_button(auth_action)
                
                if submitted:
                    if auth_action == "Login":
                        self.handle_login(username, password, user_type.lower())
                    else:
                        self.handle_signup(username, password, email, user_type.lower())

    def handle_login(self, username, password, user_type):
        try:
            response = requests.post(
                f"{self.API_URL}/login",
                data={"username": username, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["role"] == user_type:
                    st.session_state.authenticated = True
                    st.session_state.user_type = user_type
                    st.session_state.user_token = data["access_token"]
                    st.session_state.user_id = data["user_id"]
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid user type")
            else:
                st.error("Invalid credentials")
        except Exception as e:
            st.error(f"Connection error: {str(e)}")

    def handle_signup(self, username, password, email, user_type):
        try:
            response = requests.post(
                f"{self.API_URL}/register",
                json={
                    "username": username,
                    "password": password,
                    "email": email,
                    "role": user_type
                }
            )
            
            if response.status_code == 200:
                st.success("Account created successfully! Please login.")
            else:
                st.error("Registration failed")
        except Exception as e:
            st.error(f"Connection error: {str(e)}")

    def show_patient_interface(self):
        st.title("Patient Dashboard")
        
        with st.sidebar:
            st.title("Navigation")
            selected_page = st.radio(
                "Choose a page",
                ["Chat with AI Assistant", "Upload Tests", "View Reports", "Book Appointment"]
            )
            
            # Language selection
            st.session_state.language = st.selectbox(
                "Select Language",
                ["English", "Spanish", "French"]
            )
            
            if st.button("Logout"):
                self.logout()
        
        if selected_page == "Chat with AI Assistant":
            self.show_chat_interface()
        elif selected_page == "Upload Tests":
            self.show_upload_page()
        elif selected_page == "View Reports":
            self.show_reports_page()
        elif selected_page == "Book Appointment":
            self.show_appointment_page()

    def show_chat_interface(self):
        st.header("Chat with AI Assistant")
        
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                
                # Display relevant information if available
                if message.get("relevant_info"):
                    with st.expander("View Related Medical Information"):
                        for info in message["relevant_info"]:
                            st.markdown(f"""
                                <div class='relevant-info'>
                                    <strong>{info['category']}</strong>: {info['information']}
                                </div>
                            """, unsafe_allow_html=True)
                
                # Display emergency warning if necessary
                if message.get("is_emergency"):
                    st.markdown("""
                        <div class='emergency-alert'>
                            ⚠️ This appears to be a medical emergency. Please seek immediate medical attention!
                        </div>
                    """, unsafe_allow_html=True)
        
        # Chat input
        if prompt := st.chat_input("Type your message here..."):
            st.session_state.chat_history.append({
                "role": "user",
                "content": prompt
            })
            
            try:
                with st.spinner("Getting response..."):
                    response = requests.post(
                        f"{self.API_URL}/chat",
                        headers={"Authorization": f"Bearer {st.session_state.user_token}"},
                        json={
                            "text": prompt,
                            "language": st.session_state.language
                        }
                    )
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": response_data["response"],
                            "relevant_info": response_data.get("relevant_info", []),
                            "is_emergency": response_data.get("is_emergency", False)
                        })
                    else:
                        st.error("Failed to get response from assistant")
                        
            except Exception as e:
                st.error(f"Error: {str(e)}")
            
            st.rerun()

    def show_upload_page(self):
        st.header("Upload Blood Test Images")
        
        with st.container():
            uploaded_files = st.file_uploader(
                "Choose blood cell images",
                type=['png', 'jpg', 'jpeg'],
                accept_multiple_files=True
            )
            
            if uploaded_files:
                st.write(f"Number of files uploaded: {len(uploaded_files)}")
                
                cols = st.columns(3)
                for idx, file in enumerate(uploaded_files):
                    with cols[idx % 3]:
                        st.image(file, caption=file.name, use_column_width=True)
                
                if st.button("Analyze Images"):
                    self.analyze_images(uploaded_files)

    def analyze_images(self, files):
        with st.spinner("Analyzing images..."):
            results = []
            progress_bar = st.progress(0)
            
            for i, file in enumerate(files):
                try:
                    files_data = {"file": (file.name, file.getvalue(), "image/jpeg")}
                    response = requests.post(
                        f"{self.API_URL}/analyze",
                        files=files_data,
                        headers={"Authorization": f"Bearer {st.session_state.user_token}"}
                    )
                    
                    if response.status_code == 200:
                        results.append({
                            "filename": file.name,
                            "analysis": response.json()
                        })
                    else:
                        st.error(f"Error analyzing {file.name}")
                    
                    progress = (i + 1) / len(files)
                    progress_bar.progress(progress)
                    
                except Exception as e:
                    st.error(f"Error processing {file.name}: {str(e)}")
            
            if results:
                self.display_analysis_results(results)

    def display_analysis_results(self, results):
        st.subheader("Analysis Results")
        
        for result in results:
            with st.expander(f"Results for {result['filename']}", expanded=True):
                analysis = result['analysis']
                
                # Cell distribution
                st.write("### Cell Type Distribution")
                cell_counts = analysis.get('cell_counts', {})
                if cell_counts:
                    cell_cols = st.columns(len(cell_counts))
                    for i, (cell_type, count) in enumerate(cell_counts.items()):
                        with cell_cols[i]:
                            st.metric(
                                label=cell_type.replace("_", " ").title(),
                                value=f"{count:.1f}%"
                            )
                
                # Risk assessment
                st.write("### Risk Assessment")
                risk_level = analysis.get('risk_assessment', '')
                if "High" in risk_level:
                    st.error(risk_level)
                elif "Moderate" in risk_level:
                    st.warning(risk_level)
                else:
                    st.success(risk_level)
                
                # Recommendations
                st.write("### Recommendations")
                for rec in analysis.get('recommendations', []):
                    st.write(f"• {rec}")
                
                # Additional details
                if details := analysis.get('details'):
                    st.write("### Additional Details")
                    cols = st.columns(2)
                    with cols[0]:
                        st.write(f"Analysis Date: {details.get('analysis_date', 'N/A')}")
                    with cols[1]:
                        st.write(f"Confidence Score: {details.get('confidence_score', 0):.1f}%")

    def show_doctor_interface(self):
        st.title("Doctor Dashboard")
        
        with st.sidebar:
            st.title("Navigation")
            selected_page = st.radio(
                "Choose a page",
                ["Patient List", "Search Patient", "Upload Analysis", "Reports"]
            )
            
            if st.button("Logout"):
                self.logout()
        
        if selected_page == "Patient List":
            self.show_patient_list()
        elif selected_page == "Search Patient":
            self.show_patient_search()
        elif selected_page == "Upload Analysis":
            self.show_upload_page()
        elif selected_page == "Reports":
            self.show_reports_page()

    def show_patient_list(self):
        st.header("Patient List")
        
        try:
            response = requests.get(
                f"{self.API_URL}/patients",
                headers={"Authorization": f"Bearer {st.session_state.user_token}"}
            )
            
            if response.status_code == 200:
                patients = response.json()
                for patient in patients:
                    with st.expander(f"Patient: {patient['username']} (ID: {patient['id']})"):
                        st.write(f"Email: {patient['email']}")
                        if st.button(f"View History #{patient['id']}", key=f"hist_{patient['id']}"):
                            self.show_patient_history(patient['id'])
            else:
                st.error("Failed to fetch patient list")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    

    def show_patient_history(self, patient_id):
        try:
            response = requests.get(
                f"{self.API_URL}/patient/{patient_id}/history",
                headers={"Authorization": f"Bearer {st.session_state.user_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                st.subheader(f"Patient History")
                
                for analysis in data:
                    with st.expander(f"Analysis from {analysis['date']}"):
                        self.display_analysis_results([{"filename": "Analysis", "analysis": analysis['results']}])
                        
                        # Add doctor notes
                        notes = st.text_area(
                            "Doctor Notes",
                            value=analysis.get('doctor_notes', ''),
                            key=f"notes_{analysis['id']}"
                        )
                        if st.button("Save Notes", key=f"save_{analysis['id']}"):
                            self.save_doctor_notes(patient_id, analysis['id'], notes)
            else:
                st.error("Failed to fetch patient history")
        except Exception as e:
            st.error(f"Error: {str(e)}")

    def save_doctor_notes(self, patient_id, analysis_id, notes):
        try:
            response = requests.post(
                f"{self.API_URL}/patient/{patient_id}/add-note",
                headers={"Authorization": f"Bearer {st.session_state.user_token}"},
                json={
                    "analysis_id": analysis_id,
                    "notes": notes
                }
            )
            
            if response.status_code == 200:
                st.success("Notes saved successfully")
            else:
                st.error("Failed to save notes")
        except Exception as e:
            st.error(f"Error: {str(e)}")

    def show_patient_search(self):
        st.header("Search Patient")
        
        patient_id = st.text_input("Enter Patient ID")
        if st.button("Search"):
            if patient_id:
                self.show_patient_history(patient_id)
            else:
                st.warning("Please enter a patient ID")

    def show_reports_page(self):
        st.header("Medical Reports")
        
        if st.session_state.user_type == "doctor":
            # Doctor view of reports
            try:
                response = requests.get(
                    f"{self.API_URL}/active-patients",
                    headers={"Authorization": f"Bearer {st.session_state.user_token}"}
                )
                
                if response.status_code == 200:
                    patients = response.json()
                    st.subheader("High Risk Patients")
                    
                    for patient in patients:
                        with st.expander(f"Patient: {patient['username']}"):
                            st.write(f"Email: {patient['email']}")
                            st.write(f"Last Login: {patient['last_login'] or 'Never'}")
                            if st.button(f"View Details #{patient['id']}", key=f"details_{patient['id']}"):
                                self.show_patient_history(patient['id'])
                else:
                    st.error("Failed to fetch high risk patients")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        else:
            # Patient view of reports
            try:
                response = requests.get(
                    f"{self.API_URL}/patient/{st.session_state.user_id}/history",
                    headers={"Authorization": f"Bearer {st.session_state.user_token}"}
                )
                
                if response.status_code == 200:
                    analyses = response.json()
                    for analysis in analyses:
                        with st.expander(f"Analysis Report - {analysis['date']}"):
                            self.display_analysis_results([{
                                "filename": "Analysis",
                                "analysis": analysis['results']
                            }])
                else:
                    st.error("Failed to fetch your reports")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    def show_appointment_page(self):
        st.header("Book Appointment")
        
        if st.session_state.user_type == "patient":
            try:
                # Get available doctors
                response = requests.get(
                    f"{self.API_URL}/doctors",
                    headers={"Authorization": f"Bearer {st.session_state.user_token}"}
                )
                
                if response.status_code == 200:
                    doctors = response.json()
                    
                    # Appointment booking form
                    with st.form("appointment_form"):
                        selected_doctor = st.selectbox(
                            "Select Doctor",
                            options=[(d['id'], d['username']) for d in doctors],
                            format_func=lambda x: x[1]
                        )
                        
                        appointment_date = st.date_input("Select Date")
                        appointment_time = st.time_input("Select Time")
                        notes = st.text_area("Notes (Optional)")
                        
                        if st.form_submit_button("Book Appointment"):
                            appointment_datetime = datetime.combine(
                                appointment_date,
                                appointment_time
                            )
                            
                            response = requests.post(
                                f"{self.API_URL}/appointment",
                                headers={"Authorization": f"Bearer {st.session_state.user_token}"},
                                json={
                                    "doctor_id": selected_doctor[0],
                                    "date": appointment_datetime.isoformat(),
                                    "notes": notes
                                }
                            )
                            
                            if response.status_code == 200:
                                st.success("Appointment booked successfully!")
                            else:
                                st.error("Failed to book appointment")
                
                # Display existing appointments
                response = requests.get(
                    f"{self.API_URL}/appointments",
                    headers={"Authorization": f"Bearer {st.session_state.user_token}"}
                )
                
                if response.status_code == 200:
                    appointments = response.json()
                    if appointments:
                        st.subheader("Your Appointments")
                        for apt in appointments:
                            with st.expander(f"Appointment on {apt['date']}"):
                                st.write(f"Status: {apt['status']}")
                                if apt.get('notes'):
                                    st.write(f"Notes: {apt['notes']}")
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
        else:
            # Doctor's view of appointments
            try:
                response = requests.get(
                    f"{self.API_URL}/appointments",
                    headers={"Authorization": f"Bearer {st.session_state.user_token}"}
                )
                
                if response.status_code == 200:
                    appointments = response.json()
                    if appointments:
                        st.subheader("Your Appointments")
                        for apt in appointments:
                            with st.expander(f"Appointment with {apt['patient_id']} on {apt['date']}"):
                                st.write(f"Status: {apt['status']}")
                                if apt.get('notes'):
                                    st.write(f"Notes: {apt['notes']}")
                                
                                # Add option to update appointment status
                                new_status = st.selectbox(
                                    "Update Status",
                                    options=["scheduled", "completed", "cancelled"],
                                    key=f"status_{apt['id']}"
                                )
                                if st.button("Update Status", key=f"update_{apt['id']}"):
                                    self.update_appointment_status(apt['id'], new_status)
            
            except Exception as e:
                st.error(f"Error: {str(e)}")

    def update_appointment_status(self, appointment_id: int, status: str):
        try:
            response = requests.put(
                f"{self.API_URL}/appointment/{appointment_id}/status",
                headers={"Authorization": f"Bearer {st.session_state.user_token}"},
                json={"status": status}
            )
            
            if response.status_code == 200:
                st.success("Appointment status updated successfully")
                st.rerun()
            else:
                st.error("Failed to update appointment status")
        except Exception as e:
            st.error(f"Error: {str(e)}")

    def logout(self):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

if __name__ == "__main__":
    app = BloodCancerApp()
    app.main()