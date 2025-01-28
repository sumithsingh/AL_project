import streamlit as st
import requests
from PIL import Image
import io
import json

class BloodCancerApp:
    def __init__(self):
        st.set_page_config(
            page_title="Blood Cancer Detection System",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        self.initialize_session()
        self.API_URL = "http://localhost:8000"  # Backend API URL

    def initialize_session(self):
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
            st.session_state.user_type = None
            st.session_state.user_token = None
            st.session_state.language = "English"
            st.session_state.show_assistant = False
            st.session_state.chat_history = []

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
            </style>
        """, unsafe_allow_html=True)

    def show_auth_page(self):
        st.title("Blood Cancer Detection System")
        
        # Toggle between login and signup
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
                if data["role"] == user_type:  # Verify user type matches
                    st.session_state.authenticated = True
                    st.session_state.user_type = user_type
                    st.session_state.user_token = data["access_token"]
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
        
        # Sidebar navigation
        with st.sidebar:
            st.title("Navigation")
            selected_page = st.radio(
                "Choose a page",
                ["Chat with AI Assistant", "Upload Tests", "View Reports", "Book Appointment"]
            )
            
            if st.button("Logout"):
                self.logout()
        
        # Main content area
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
        
        # Chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Type your message here..."):
            # Add user message to chat history
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            # Get AI response
            try:
                response = requests.post(
                    f"{self.API_URL}/chat",
                    headers={"Authorization": f"Bearer {st.session_state.user_token}"},
                    json={"text": prompt, "language": st.session_state.language}
                )
                
                if response.status_code == 200:
                    ai_message = response.json()["response"]
                    st.session_state.chat_history.append({"role": "assistant", "content": ai_message})
                else:
                    st.error("Failed to get response from assistant")
            except Exception as e:
                st.error(f"Error: {str(e)}")
            
            st.rerun()

    def show_upload_page(self):
        st.header("Upload Blood Test Images")
        
        uploaded_files = st.file_uploader(
            "Choose blood cell images",
            type=['png', 'jpg', 'jpeg'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            for file in uploaded_files:
                st.image(file, caption=file.name)
            
            if st.button("Analyze Images"):
                with st.spinner("Analyzing images..."):
                    self.process_images(uploaded_files)

    def process_images(self, files):
        try:
            for file in files:
                files_data = {"file": (file.name, file.getvalue(), "image/jpeg")}
                response = requests.post(
                    f"{self.API_URL}/analyze",
                    files=files_data,
                    headers={"Authorization": f"Bearer {st.session_state.user_token}"}
                )
                
                if response.status_code == 200:
                    results = response.json()
                    self.display_results(results, file.name)
                else:
                    st.error(f"Error analyzing {file.name}")
        except Exception as e:
            st.error(f"Error: {str(e)}")

    def display_results(self, results, filename):
        st.subheader(f"Analysis Results - {filename}")
        
        # Display cell counts
        st.write("Cell Type Distribution")
        cols = st.columns(len(results["cell_counts"]))
        for i, (cell_type, count) in enumerate(results["cell_counts"].items()):
            with cols[i]:
                st.metric(
                    label=cell_type.replace("_", " ").title(),
                    value=f"{count:.1f}%"
                )
        
        # Display risk assessment
        st.write("Risk Assessment")
        risk_level = results["risk_assessment"]
        if "High" in risk_level:
            st.error(risk_level)
        elif "Moderate" in risk_level:
            st.warning(risk_level)
        else:
            st.success(risk_level)
        
        # Display recommendations
        st.write("Recommendations")
        for rec in results["recommendations"]:
            st.write(f"• {rec}")

    def show_doctor_interface(self):
        st.title("Doctor Dashboard")
        
        # Sidebar navigation
        with st.sidebar:
            st.title("Navigation")
            selected_page = st.radio(
                "Choose a page",
                ["Patient List", "Search Patient", "Upload Analysis", "Reports"]
            )
            
            if st.button("Logout"):
                self.logout()
        
        # Main content area
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
                    with st.expander(f"Patient: {patient['name']} (ID: {patient['id']})"):
                        st.write(f"Email: {patient['email']}")
                        st.write(f"Status: {'Active' if patient['is_active'] else 'Inactive'}")
                        if st.button(f"View Details #{patient['id']}", key=f"view_{patient['id']}"):
                            self.show_patient_details(patient['id'])
            else:
                st.error("Failed to fetch patient list")
        except Exception as e:
            st.error(f"Error: {str(e)}")

    def show_patient_details(self, patient_id):
        try:
            response = requests.get(
                f"{self.API_URL}/patient/{patient_id}/history",
                headers={"Authorization": f"Bearer {st.session_state.user_token}"}
            )
            
            if response.status_code == 200:
                history = response.json()
                for record in history:
                    with st.expander(f"Analysis from {record['date']}"):
                        self.display_results(record['results'], "")
            else:
                st.error("Failed to fetch patient history")
        except Exception as e:
            st.error(f"Error: {str(e)}")

    def show_patient_search(self):
        st.header("Search Patient")
        
        patient_id = st.text_input("Enter Patient ID")
        if st.button("Search"):
            if patient_id:
                self.show_patient_details(patient_id)
            else:
                st.warning("Please enter a patient ID")

    def show_reports_page(self):
        st.header("Medical Reports")
        st.info("This feature will be available soon.")

    def show_appointment_page(self):
        st.header("Book Appointment")
        st.info("This feature will be available soon.")

    def logout(self):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

if __name__ == "__main__":
    app = BloodCancerApp()
    app.main()