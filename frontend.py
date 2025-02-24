import logging
import tempfile
import streamlit as st
import requests
from PIL import Image
import io
import datetime

class BloodCancerApp:
    def __init__(self):
        # Set the API URL for your backend service
        self.API_URL = "http://localhost:8000"
        # Initialize session state
        self.initialize_session()
    
    def initialize_session(self):
        # Initialize session state variables if they are not already set
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user_type' not in st.session_state:
            st.session_state.user_type = None
        if 'user_token' not in st.session_state:
            st.session_state.user_token = None
        if 'language' not in st.session_state:
            st.session_state.language = "English"
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        if 'user_id' not in st.session_state:
            st.session_state.user_id = None
        if 'reports' not in st.session_state:
            st.session_state.reports = []
        if st.session_state.authenticated:
            self.fetch_reports()

    def main(self):
        # Set custom CSS for Streamlit components
        self.set_custom_css()
        
        # Show the login page or user-specific dashboard
        if not st.session_state.authenticated:
            self.show_auth_page()
        else:
            if st.session_state.user_type == "patient":
                self.show_patient_interface()
            else:
                self.show_doctor_interface()


    def show_auth_page(self):
        st.title("𝑯𝒆𝒎𝒂𝑩𝒓𝒊𝒅𝒈𝒆 𝑨𝑰-𝑫𝒓𝒊𝒗𝒆𝒏 𝑩𝒍𝒐𝒐𝒅 𝑪𝒂𝒏𝒄𝒆𝒓 𝑫𝒆𝒕𝒆𝒄𝒕𝒊𝒐𝒏 & 𝑪𝒂𝒓𝒆 ")
        
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
        st.title("𝙃𝙚𝙢𝙖𝘽𝙧𝙞𝙙𝙜𝙚 – 𝙋𝙖𝙩𝙞𝙚𝙣𝙩 𝙋𝙤𝙧𝙩𝙖𝙡")
        
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
    
    def set_custom_css(self):
        st.markdown("""
        <style>
        /* Make the entire background use our image */
        body, .stApp {
            background: url("https://img.freepik.com/free-psd/modern-abstract-deep-blue-gradient-background_84443-3754.jpg?t=st=1740431237~exp=1740434837~hmac=3d121e0c0d3f311d0a1fde5e7f6e15adbdd89b7ca631d512d0f11faf4c03e349&w=1800") no-repeat center center fixed;
            background-size: cover;
            
        }
        
        /* Optional: Add a dark overlay so text remains visible */
        .stApp {
            background-color: rgba(0,0,0,0.6);
            background-blend-mode: darken;
            color: #f8f9fa;
        }
        /* Brighten headings or text if needed */
        h1, h2, h3, h4 {
            color: #ffffff;
            text-shadow: 1px 1px 2px #000;
        }

                    
        /* Container for the chat area */
        .chat-container {
            margin-top: 20px;
            margin-bottom: 20px;
            background: none; /* No big white bar */
            padding: 0;
        }

        /* Clear floats for each message block */
        .bubble-container::after {
            content: "";
            clear: both;
            display: table;
        }

        /* Assistant bubble: light background, dark text, margin-left for avatar spacing */
        .assistant-bubble {
            background: #E3F2FD;   /* Light blue */
            color: #111;          /* Dark text for contrast */
            padding: 10px 15px;
            border-radius: 12px;
            margin: 5px 0;
            display: inline-block;
            max-width: 60%;
            float: left;
            margin-left: 70px;    /* Space so avatar isn't overlapped */
            position: relative;
        }

        /* User bubble: darker background, white text, aligned right */
        .user-bubble {
            background: #333;
            color: #FFF;
            padding: 10px 15px;
            border-radius: 12px;
            margin: 5px 0;
            display: inline-block;
            max-width: 60%;
            float: right;
            text-align: right;
            position: relative;
        }

        /* The doctor avatar: pinned left, round, no overlap, fully visible */
        .avatar {
            width: 60px;
            height: auto;
            float: left;
            margin-right: 5px;
            margin-bottom: 5px;
            object-fit: contain;
        }

        /* Timestamp styling inside each bubble, small & subtle */
        .bubble-timestamp {
            display: block;
            text-align: right;
            font-size: 0.75em;
            color: #777;
            margin-top: 5px;
        }

        </style>
        """, unsafe_allow_html=True)

    


    def show_chat_interface(self):
        """Chat interface with bubble styling + avatar, and optional auto-end logic."""
        st.header("Chat Support 24x7")

        # 1) Start a container for the entire chat area
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        # 2) Greet user if not greeted
        if "chatbot_greeted" not in st.session_state:
            st.session_state.chatbot_greeted = False
            
        if not st.session_state.chatbot_greeted:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "Hello! I'm Dr. Clara, your AI Assistant. How can I help you today?",
                "timestamp": datetime.datetime.now().strftime("%H:%M")
            })
            st.session_state.chatbot_greeted = True

        # 3) Display messages as HTML bubble containers
        for msg in st.session_state.chat_history:
            if msg["role"] == "assistant":
                # Assistant bubble with avatar
                st.markdown(f"""
                <div class="bubble-container">
                    <img src="https://img.freepik.com/free-psd/3d-render-female-doctor-wearing-glasses-white-coat-stethoscope-around-her-neck-she-has-dark-hair-friendly-expression_632498-32065.jpg?t=st=1738264700~exp=1738268300~hmac=892defdb73f2d4887415cae24cec26252f75844e5a755fd565baca778cde35c4&w=740" class="avatar" />
                    <div class="assistant-bubble">
                        {msg["content"]}
                        <div style="font-size: 0.75em; margin-top: 4px; text-align: right; color: #666;">
                            {msg.get("timestamp", "")}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # If there's emergency or relevant info, handle it
                if msg.get("is_emergency"):
                    st.error("⚠️ EMERGENCY: Seek immediate medical attention!")
                if msg.get("relevant_info"):
                    with st.expander("Related Medical Information", expanded=True):
                        for info in msg["relevant_info"]:
                            st.markdown(f"""
                            <div class='relevant-info'>
                                <strong>{info['category'].title()}</strong>: {info['text']}
                                <div class='chat-meta'>Relevance: {info['relevance_score']:.2f}</div>
                            </div>
                            """, unsafe_allow_html=True)

            elif msg["role"] == "user":
                st.markdown(f"""
                <div class="bubble-container">
                    <div class="user-bubble">
                        {msg["content"]}
                        <div style="font-size: 0.75em; margin-top: 4px; text-align: right; color: #aaa;">
                            {msg.get("timestamp", "")}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            # 4) Provide a chat input
        if user_input := st.chat_input("Type your message..."):
            self._handle_chat_input(user_input)
        # End the container
        st.markdown("</div>", unsafe_allow_html=True)

    def _handle_chat_input(self, prompt: str, timestamp=None):

        if timestamp is None:
            timestamp = datetime.datetime.now().strftime("%H:%M")

        user_msg = {
            "role": "user",
            "content": prompt,
            "timestamp": timestamp
        }
        st.session_state.chat_history.append(user_msg)
        # Example: auto-end logic if user says "bye" ...
        lower_prompt = prompt.strip().lower()
        end_phrases = ["that's it", "bye", "nothing else", "i'm done", "end chat", "merci"]
        if any(phrase in lower_prompt for phrase in end_phrases):
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "Thank you for chatting with me! Have a wonderful day.",
                "timestamp": datetime.datetime.now().strftime("%H:%M")
            })
            return
        # Otherwise, call the backend /chat
        try:
            response = requests.post(
                f"{self.API_URL}/chat",
                headers={"Authorization": f"Bearer {st.session_state.user_token}"},
                json={"text": prompt, "language": st.session_state.language}
            )
            if response.status_code == 200:
                data = response.json()
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": data["response"],
                    "timestamp": datetime.datetime.now().strftime("%H:%M"),
                    "relevant_info": data.get("relevant_info", []),
                    "is_emergency": data.get("is_emergency", False)
                })
            else:
                st.error("Failed to get chatbot response")
        except Exception as e:
            st.error(f"Chat error: {str(e)}")
        st.rerun()

    def show_upload_page(self):
        st.header("Upload Blood Test Images")
    
        uploaded_files = st.file_uploader(
            "Choose blood cell images",
            type=['png', 'jpg', 'jpeg'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            st.write(f"Number of files uploaded: {len(uploaded_files)}")

            sample_files = uploaded_files[:3]
            st.write(f"Showing up to {len(sample_files)} sample images...")
            
            cols = st.columns(3)
            for idx, file in enumerate(sample_files):
                with cols[idx % 3]:
                    st.image(file, caption=file.name, use_container_width=True)
            
            if st.button("Analyze Images"):
                self.analyze_images_batch(uploaded_files)

    def analyze_images_batch(self, files):
        with st.spinner("Analyzing images in one batch..."):
            multiple_files = []
            for file in files:
                multiple_files.append(
                    ("files", (file.name, file.getvalue(), "image/jpeg"))
                )
            try:
                response = requests.post(
                    f"{self.API_URL}/analyze-batch",
                    files=multiple_files,
                    headers={"Authorization": f"Bearer {st.session_state.get('user_token', '')}"}
                )

                if response.status_code == 200:
                    final_analysis = response.json()
                    self.display_overall_analysis(final_analysis)
                else:
                    st.error("Failed to analyze images in batch")
            except Exception as e:
                st.error(f"Batch analysis error: {str(e)}")

    def display_overall_analysis(self, analysis_data):
        st.subheader("Overall Batch Analysis")
        risk_level = analysis_data.get("risk_level", "Unknown")
        st.markdown(f"**Risk Level:** {risk_level}")

        # Retrieve 'results' dict (the final_analysis_data from backend)
        results = analysis_data.get("results", {})

        # 2) Format cell counts nicely in a table
        cell_counts = results.get("cell_counts", {})
        st.markdown("### Cell Counts:")
        if cell_counts:
            # Build a list of dicts so we can display them in a table
            table_data = [
                {"Cell": cell, "Percentage (%)": f"{val:.4f}"}
                for cell, val in cell_counts.items()
            ]
            st.table(table_data)
        else:
            st.write("_No cell counts found_")

        # 3) Show risk assessment
        st.markdown("### Risk Assessment:")
        st.write(results.get("risk_assessment", "N/A"))

        # 4) Show recommendations as bullet points
        st.markdown("### Recommendations:")
        recs = results.get("recommendations", [])
        if recs:
            for rec in recs:
                st.markdown(f"- {rec}")
        else:
            st.markdown("_No specific recommendations_")



    def display_analysis_results(self, results):
        st.subheader("Analysis Results")
        
        import pandas as pd
        result_data = []
        
        for result in results:
            analysis = result['analysis']
        
            # Handle missing 'risk_assessment'
            risk_assessment = analysis.get('risk_assessment', 'Unknown')

            # Handle missing 'confidence_score'
            confidence_score = analysis.get('details', {}).get('confidence_score', 0)
            
            cell_counts = analysis.get('cell_counts', {})

            row = {
                'Filename': result['filename'],
                'Risk Level': analysis.get('risk_level', 'Unknown'),  # Direct access
                'Confidence Score': confidence_score,
                **analysis.get('cell_counts', {})
            }
            result_data.append(row)
        
        df = pd.DataFrame(result_data)

        if result_data:
            df = pd.DataFrame(result_data)
            st.dataframe(df, hide_index=True, use_container_width=True)
        else:
            st.warning("No valid results to display.")
       
    def generate_report(self, report):
        from report_generator import ReportGenerator
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            reporter = ReportGenerator()
            pdf_content = reporter.generate(
                test_data=[report["results"]],
                patient_info={
                    "id": report["user_id"],
                    "name": st.session_state.get("username", "Patient")
                }
            )
            

            report_entry = {
                "filename": f"blood_analysis_{report['date']}.pdf",
                "date": report["date"],
                "pdf_content": pdf_content
            }

            if "reports" not in st.session_state:
                st.session_state.reports = []
            
            st.session_state.reports.append(report_entry)

            # Ensure the key is unique by using timestamp
            st.download_button(
                label="Download Full Report",
                data=pdf_content,
                file_name=report_entry["filename"],
                mime="application/pdf",
                key=f"download_report_{report_entry['date']}"
            )
    

    def fetch_reports(self):
        """Fetches the latest analysis reports for the logged-in user."""
        try:
            response = requests.get(
                f"{self.API_URL}/reports",
                headers={"Authorization": f"Bearer {st.session_state.user_token}"}
            )
            
            if response.status_code == 200:
                st.session_state.reports = response.json()
                logging.info(f"📊 {len(st.session_state.reports)} reports loaded successfully")
            else:
                st.error("⚠ Failed to load reports. Please try again.")

        except Exception as e:
            st.error(f"⚠ Error fetching reports: {str(e)}")


            

            

    def show_doctor_interface(self):
        st.title("𝑯𝒆𝒎𝒂𝑩𝒓𝒊𝒅𝒈𝒆 – 𝑫𝒐𝒄𝒕𝒐𝒓 𝑷𝒐𝒓𝒕𝒂𝒍")
        
        with st.sidebar:
            st.title("Navigation")
            selected_page = st.radio(
                "Choose a page",
                ["Patient List", "Search Patient", "Upload Analysis", "Reports", "Appointments"]
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
        elif selected_page == "Appointments":
            self.show_doctor_appointments_list()

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
    
    def fetch_doctors(self):
        """Fetches the list of doctors from the backend."""
        try:
            response = requests.get(
                f"{self.API_URL}/doctors",
                headers={"Authorization": f"Bearer {st.session_state.get('user_token', '')}"}
            )
            if response.status_code == 200:
                return response.json()  # Expect a list like [{"id":1,"username":"Dr.X"},...]
            else:
                st.error("Failed to load doctors list")
                return []
        except Exception as e:
            st.error(f"Error loading doctors: {str(e)}")
            return []
    def show_patient_history(self, patient_id):
        st.subheader(f"Patient History (ID: {patient_id})")
        try:
            response = requests.get(
                f"{self.API_URL}/patient/{patient_id}/history",
                headers={"Authorization": f"Bearer {st.session_state.user_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                st.subheader(f"Patient History")
                
                for analysis in data:
                    st.subheader(f"Analysis from {analysis['date']}")
                    st.write(f"Risk Level: {analysis['risk_level']}")
                    
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

    def display_appointments(self):
        """Retrieves and displays the current user's appointments."""
        st.subheader("Your Appointments")
        try:
            response = requests.get(
                f"{self.API_URL}/appointments",
                headers={"Authorization": f"Bearer {st.session_state.get('user_token', '')}"}
            )
            if response.status_code == 200:
                appointments = response.json()
                if not appointments:
                    st.info("No upcoming appointments.")
                    return
                for apt in appointments:
                    with st.expander(f"Appointment on {apt['date']} - {apt['status']}"):
                        st.write(f"Doctor ID: {apt['doctor_id']}")
                        st.write(f"Patient ID: {apt['patient_id']}")
                        if apt.get("notes"):
                            st.write(f"Notes: {apt['notes']}")
            else:
                st.error("Failed to load appointments.")
        except Exception as e:
            st.error(f"Error fetching appointments: {str(e)}")


    def show_reports_page(self):
        st.header("📑 Medical Reports")
        # Ensure reports are fetched if not available
        if not st.session_state.reports:
            st.warning("🔄 No reports found. Fetching latest reports...")
            self.fetch_reports()
    
        # Refresh Reports Button
        if st.button("🔄 Refresh Reports"):
            self.fetch_reports()
            st.success("✅ Reports refreshed successfully!")
            st.rerun()

        # Ensure reports exist
        if not st.session_state.reports:
            st.warning("⚠ No reports available!")
            return

        # ✅ FIX: Iterate through reports correctly
        for report in st.session_state.reports:
            if not isinstance(report, dict):  # Ensure report is a dictionary
                logging.error("Invalid report format received")
                continue  # Skip invalid reports
            with st.expander(f"📅 Analysis Report - {report.get('date', 'Unknown')} | 🩸 Risk Level: {report.get('risk_level', 'Unknown')}"):
                st.write(f"🆔 Report ID: {report.get('id', 'N/A')}")
                st.write(f"📌 Risk Level: **{report.get('risk_level', 'Unknown')}**")
                st.write(f"📜 Doctor Notes: {report.get('doctor_notes', 'No notes available')}")

                # ✅ FIX: Ensure "results" exists before accessing
                analysis_data = report.get("results", {})
                if not analysis_data:
                    st.warning("⚠ No results found for this report!")
                    continue  # Skip this report

                # Extract details
                cell_counts = analysis_data.get("cell_counts", {})
                risk_assessment = analysis_data.get("risk_assessment", "Unknown")
                confidence_score = analysis_data.get("details", {}).get("confidence_score", "N/A")

                # Display Blood Cell Analysis Table
                if cell_counts:
                    st.subheader("🧬 Blood Cell Analysis")
                    df = [{"Cell Type": cell, "Percentage (%)": f"{value:.2f}%"} for cell, value in cell_counts.items()]
                    st.table(df)

                # Display Risk Assessment
                st.subheader("📊 Risk Assessment")
                st.write(f"**{risk_assessment}**")
                st.write(f"🔍 Confidence Score: **{confidence_score:.2f}%**")

                # ✅ FIX: Ensure Report Download Works
                if st.button(f"📄 Download Report - {report['id']}", key=f"report_{report['id']}"):
                    self.generate_report(report)


    def show_appointment_page(self):
        st.header("Book Appointment")

        # 1) Fetch doctors
        doctors = self.fetch_doctors()
        if not doctors:
            st.warning("No doctors available currently.")
            return

        # Build a list of (doctor_id, doctor_name) for the selectbox
        doc_options = [(doc["id"], doc["username"]) for doc in doctors]
        selected_doc = st.selectbox(
            label="Select Doctor",
            options=doc_options,
            format_func=lambda x: x[1]  # shows the doc's username in the dropdown
        )

        # 2) Date & Time inputs
        appt_date = st.date_input("Select Date")
        appt_time = st.time_input("Select Time")
    
        import datetime
        # Combine them
        appointment_datetime = None
        if appt_date and appt_time:
            appointment_datetime = datetime.datetime.combine(appt_date, appt_time)

        # 3) Notes
        notes = st.text_area("Additional Notes (Optional)")

        # 4) Book button
        if st.button("Book Appointment"):
            if appointment_datetime is None:
                st.error("Please select a valid date and time.")
                return
            try:
                response = requests.post(
                    f"{self.API_URL}/appointment",
                    headers={"Authorization": f"Bearer {st.session_state.get('user_token', '')}"},
                    json={
                        "doctor_id": selected_doc[0],
                        "date": appointment_datetime.isoformat(),
                        "notes": notes
                    }
                )
                if response.status_code == 200:
                    st.success("Appointment booked successfully!")
                else:
                    st.error("Failed to book appointment. Please try again.")
            except Exception as e:
                st.error(f"Error booking appointment: {str(e)}")

        # 5) Show existing appointments
        self.display_appointments()

    def show_doctor_appointments_list(self):
        st.header("Upcoming Appointments")
        
        try:
            response = requests.get(
                f"{self.API_URL}/appointments",
                headers={"Authorization": f"Bearer {st.session_state.get('user_token', '')}"}
            )
            if response.status_code == 200:
                appointments = response.json()
                
                if not appointments:
                    st.info("No upcoming appointments found.")
                    return
            
                # Loop over each appointment
                for apt in appointments:
                    with st.expander(f"Appointment on {apt['date']} - {apt['status']}"):
                        st.write(f"Patient ID: {apt['patient_id']}")
                        st.write(f"Doctor ID: {apt['doctor_id']}")  
                        st.write(f"Status: {apt['status']}")
                        if apt.get('notes'):
                            st.write(f"Notes: {apt['notes']}")
            else:
                st.error("Failed to fetch appointments.")
        except Exception as e:
            st.error(f"Error fetching appointments: {str(e)}")



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
