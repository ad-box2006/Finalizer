import trial_balance
import balance_sheet
import streamlit as st
from io import BytesIO
import time
import requests
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
st.set_page_config(
    page_title="Finalizer",
    page_icon="asset.jpg",
    layout="centered",
    initial_sidebar_state="expanded"
)
def inject_styles():
    st.markdown("""
        <style>
        .stApp { background: #0b1220; color: #e5eef8 !important; }
        #MainMenu, footer {visibility: hidden; }
        
        section[data-testid="stSidebar"] {
            background: #0f172a !important;
            border-right: 1px solid #1f2a44 !important;
        }
        .title {
            font-size: 2.1rem;
            font-weight: 800;
            letter-spacing: -0.04rem;
            margin: 0 0 0.2rem 0;
            color: #ffffff !important;   
        }
        .subtitle {
            color: #a7b4c7 !important;
            font-size: 0,98rem;
            margin: 0 0 1.6rem;
        }
        section[data-testid="stSidebar"] * { color: #e5eef8 !important; }
        
        .stButton > button, div.stFormSubmitButton > button, button[kind="primary"], button[kind="secondary"] {
            border-radius: 10px;
            border: 1px solid #24324f !important;
            background: #172033 !important;
            color: #e5eef8 !important;;
            width: 100%;
        }
        .stButton > button:hover, div.stFormSubmitButton > button:hover {
            background: #22314f;
            border-color: #35507a;
            color: #ffffff;
        }
        div[data-testid="stSidebar"] .stButton > button {
            background: #111827;
        }
        input, textarea, div[data-baseweb="select"] {
            background-color: #111827;
            color: #e5eef8;
        }
        div[data-testid="stFileUploader"] section {
            background-color: #0F172A !important;
            border: 1px dashed #35507a !important;
            border-radius: 12px !important;
        } 
        .block-container {
            padding-top: 13rem;
            padding-bottom: 4rem;
            max-width: 900px;
            margin: 0 auto;
        }
        .title {
            font-size: 2.1rem;
            font-weight: 800;
            letter-spacing: -0.04rem;
            margin: 0 0 0.2rem 0;
            color: #ffffff;
        }
        .subtitle {
            font-size: 0.98rem;
            margin: 0 0 1.6rem 0;
            color: #a7b4c7;
        }
        </style>
    """, unsafe_allow_html=True)

#Privacy and data control ui###########################################################################################                    
def privacy_and_data_control_ui():
    st.sidebar.markdown("### Privacy & Data Control")
    st.sidebar.info("""
    - Balance sheets are processed locally and not stored permanently.
    - Data is encrypted and never used to train public AI models.
    """)
    st.markdown("[Privacy policy](#) | [Terms of Service](#)")
    
def feedback_sidebar_ui():
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Beta Feedback & Leads")
    
    with st.sidebar.form("feedback_form", clear_on_submit=True):
        user_email = st.text_input("Your Email (for beta updates):", placeholder="accountant@firm.co.za")
        feedback_text = st.text_area("Thoughts, feature request, or bug reports?", placeholder="What would make month-end faster for you?")
        submitted = st.form_submit_button("Send Feedback")
        if submitted:
            if not feedback_text.strip() and not user_email.strip():
                st.warning("Please enter your email or feedback first.")
            else:
                formspree_url = "https://formspree.io/f/xzedgjev"
                valid_email = user_email if user_email and "@" in user_email else "beta_user@finalizer.co.za"
                
                payload = {
                    "user": str(st.session_state.get("current_user", "anonymous")),
                    "email": valid_email,
                    "original_input_email": user_email if user_email else "None provided",
                    "comment": feedback_text   
                }
                headers = {"Accept": "application/json"}
                try:
                    response = requests.post(formspree_url, data=payload, headers=headers, timeout=8)
                    if response.status_code == 200:
                        st.success("Thank You! Feedback sent successfully.")
                    else:
                        st.error(f"Formspree error ({response.status_code}): {response.text}")
                except Exception as e:
                    st.error(f"Detailed error: {e}")
                    logging.error(f"Email dispatch error: {e}", exc_info=True)
                    
                          
       
#####Main app ui#################################################333                        
def main_app_ui():
    inject_styles()
    st.markdown('<div class="title">Finalizer</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Quick document analysis</div>', unsafe_allow_html=True)
    st.sidebar.markdown("### Upload Type")
    upload_type = st.sidebar.radio("Select document type", ["Balance Sheet", "Trial Balance"])
    
    st.markdown("---")
    
    if upload_type == "Trial Balance":
        trial_balance.trial_balance_ui()
    else:
        balance_sheet.balance_sheet_ui()
                     
def main():
    if "user_consent_time" not in st.session_state:
        st.session_state.user_consent_time = None
    if "current_user" not in st.session_state:
        st.session_state.current_user = "anonymous"
            
    privacy_and_data_control_ui()
    feedback_sidebar_ui()
    main_app_ui()
if __name__ == "__main__":
    main()
         
 