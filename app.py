import trial_balance
import balance_sheet
import streamlit as st
from io import BytesIO
import pandas as pd
import hashlib
import difflib
import logging
import json
import os
import re
import io
import datetime
import time
import bcrypt
import base64
import threading
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
def inject_login_styles():
    st.markdown("""
        <style>
        html, body, .stApp, .AppHost [data-testid="stApp"] { background: radial-gradient(circle at top right,  #0F172A, #020617) !important; }
        
        div[data-testid="element-container"] + div[data-testid="element-container"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        [data-testid="stSidebar"] div.stButton > button {
            background-color: black !important;
            color: blue !important;
            border: 1px solid #475569 !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            width: 100% !important;
        }
        [data-testid="stSidebar"] div.stButton > button:hover {
            background-color: blue !important;
            color: blue !important;
            border-color: #3B82F6 !important;
        } 
        [data-testid="stFileUploader"] section {
            background-color: #0F172A !important;
            border: 2px dashed #3B82F6 !important;
            border-radius: 10px !important;
        } 
        [data-testid="stFileUploader"] section button {
            background-color: #2563EB !important;
            color: white !important;
            border: none !important;
            border-radius: 6px !important;
        }
        [data-testid="stFileUploader"] section button p,
        [data-testid="stFileUploader"] section span {
            color: white !important;
            -webkit-text-fill-color: white !important;
        }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span {
            color: black !important;
            font-family: 'Inter', sans-serif !important;
        }
        div.stDownloadButton > button {
            background-color: #2563eb !important;
            color: white !important;
            border: none !important;
        }
        div.stDownloadButton > button:hover {
            background-color: #1d4ed8 !important;
            color: white !important;
        }
        h1, [data-testid="stMarkdownContainer"] h1 {
            background: linear-gradient(to right, #3B82F6, #8B5CF6) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            font-weight: 800 !important;
            letter-spacing: -0.05rem !important;  
        }
        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #2563EB, #4F46E5) !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            padding: 12px 24px !important;
            width: 100% !important;
        }
        div.stButton > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #3B82F6, #6366F1) !important;
            color: #FFFFFF !important;
            border: none !important;
        }
        div.stButton > button[kind="secondary"] {
            background-color: rgba(255, 255, 255, 0.03) !important;
            color: #94A3B8 !important;
            border: 1px solid #334155 !important;
            border-radius: 10px !important;
            font-weight: 500 !important;
            width: 100% !important;
        }
        div.stButton > button[kind="secondary"] :hover{
            background-color: rgba(255, 255, 255, 0.08) !important;
            color: white !important;
            border-color: #475569 !important;
        }
        div[data-baseweb="input"],
        div[data-baseweb="base-input"] {
            background-color: #0F172A !important;
            border: 1px solid #2563EB !important;
            border-radius: 10px !important;
        }
        div[data-baseweb="input"] input {
            color: white !important;
            -webkit-text-fill-color: white !important;
        }
        input::placeholder {
            color: #ccc !important;
        }
        textarea {
            color: white !important;
        }
        input:-webkit-autofill,
        input:-webkit-autofill:hover,
        input:-webkit-autofill:focus,
        div[data-baseweb="input"] input:focus {
            -webkit-text-fill-color: white !important;
            -webkit-box-shadow: 0 0 0px 1000px #0F172A !important;
            transition: background-color 5000s ease-in-out 0s !important;
        }
        body, .stApp, .css-1d391kg, css-1v3fvcr, css-1d391kg * {
            color: white !important;
        }
        div[data-testid="metric-container"] span[data-testid="stMetricValue"] {
            color: white !important;
            font-weight: 700 !important;
            font-size: 1.5rem !important;
        }
        @media (max-width: 600px) {
            div.stButton > button {
                width: 100% !important;
                font-size: 1.2rem !important;
                padding: 14px 20px !important;
            }
            div.stTextInput > div > input {
                font-size: 1.1rem !important;
                width: 100% !important;
            }
           
        }
        </style>
    """, unsafe_allow_html=True)

db_lock = threading.Lock()#handle multiple users improves prevents data corruption 
DB_FILE = "user_database_profiles.json"
#####password utilities###############################################333333
def hash_password(password):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    return base64.b64encode(hashed).decode()

def verify_password(stored_hash_b64, password_attempt):
    try:
        hashed = base64.b64decode(stored_hash_b64)
        return bcrypt.checkpw(password_attempt.encode(), hashed)
    except Exception as e:
        logging.error(f"Password verification error: {e}")
        return False

def check_password_strength(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    return True, "Strong password!"

def validate_username(username):
    if not 3 <= len(username) <= 20:
        return False, "Username must be between 8 and 20 characters."
    if not re.match(r"^\w+$", username):
        return False, "Username can only contain letters, numbers, and underscores."
    return True, ""
def save_to_local_database(db_dict):
    try:
        with db_lock:
            with open(DB_FILE, "w") as f:
                json.dump(db_dict, f, indent=4)
        return True
    except Exception as e:
        logging.error(f"Failed to save user database: {e}")
        return False
    
@st.cache_data(show_spinner=False)
def load_local_database():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except Exception:
            logging.error(f"Failed to load user database JSON file: {e}")
    default_password = "Admin@123"        
    hashed_pw = hash_password(default_password)
    return {"demo_user": {"hash": hashed_pw}}
        
#seesion state initialization##########3

st.set_page_config(page_title="Finalizer", layout="centered")
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "reset_trigger" not in st.session_state:
    st.session_state.reset_trigger = False
if "user_db" not in st.session_state:
    st.session_state.user_db = load_local_database()
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "auth_page" not in st.session_state:
    st.session_state.auth_page = "Login"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "login_attempts" not in st.session_state:
    st.session_state.login_attempts = 0
if "last_active" not in st.session_state:
    st.session_state.last_active = time.time()
if "user_consent_time" not in st.session_state:
    st.session_state.user_consent_time = None
if "financial_data" not in st.session_state:
    st.session_state.financial_data = {}
if "doc_type" not in st.session_state:
    st.session_state.doc_type = "unsupported"
if "feedback_list" not in st.session_state:
    st.session_state.feedback_list = []
if "clear_input" not in st.session_state:
    st.session_state.clear_input = False

def clear_sensitive_data():
    st.session_state.financial_data = {}
    st.session_state.doc_type = "unsupported"
    st.session_state.user_consent_time = None
    st.session_state.login_attempts = 0
    
def check_inactivity():
    INACTIVITY_LIMIT = 1800 #30minutes
    now = time.time()
    last_active = st.session_state.get("last_active", now)
    if now - last_active > INACTIVITY_LIMIT:
        clear_sensitive_data()
        st.session_state.logged_in = False
        st.warning("Session expired due to inactivity. Please log in again.")
        st.rerun()
    else:
        st.session_state["last_active"] = now
#Privacy and data control ui###########################################################################################                    
def privacy_and_data_control_ui():
    st.sidebar.markdown("### Privacy & Data Control")
    st.sidebar.info("""
    - Balance sheets are processed locally and not stored permanently.
    - Data is encrypted and never used to train public AI models.
    """)
    st.markdown("[Privacy policy](#) | [Terms of Service](#)")
    
def delete_account_ui():
    st.markdown("Delete Account")
    if "confirm_delete" not in st.session_state:
        st.session_state.confirm_delete = False
    if not st.session_state.confirm_delete:
        if st.sidebar.button("Delete Account", type="primary"):
            st.session_state.confirm_delete = True
    else:
        st.sidebar.warning("Are you sure? This action is irreversable.")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("Confirm Delete", type="primary"):
                user_db = st.session_state.user_db
                current_user = st.session_state.current_user
                if current_user in user_db:
                    del user_db[current_user]
                    save_to_local_database(user_db)
                    clear_sensitive_data()
                    st.session_state.logged_in = False
                    st.session_state.current_user = None
                    st.sidebar.success("Account deleted successfully.")
                    st.rerun()
                else:
                    st.sidebar.error("User not found.")
        with col2:
            if st.button("Cancel"):
                st.session_state.confirm_delete = False
                st.rerun()
def feedback_sidebar_ui():
    st.sidebar.markdown("---")
    st.sidebar.markdown("Beta Feedback")
    with st.sidebar.form("feedback_form", clear_on_submit=True):
        user_email = st.text_input("Your Email (optional):")
        feedback_text = st.text_area("Thoughts or bug reports?")
        submitted = st.form_submit_button("Send Feedback")
        if submitted:
            if not feedback_text.strip():
                st.warning("Please enter some feedback first.")
            else:
                feedback_data = {
                    "Timestamp": [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                    "User": [str(st.session_state.current_user)],
                    "Email": [user_email if user_email else "Anonymous"],
                    "Comment": [feedback_text]
                    
                }
                df_feedback = pd.DataFrame(feedback_data)
                csv_file = "feedback_csv"
                if os.path.exists(csv_file):
                    df_feedback.to_csv(csv_file, mode='a', header=False, index=False)
                else:
                    df_feedback.to_csv(csv_file, mode='w', header=True, index=False)
                    
                st.success("Thank You! Feedback sent to successfully.")
                          
       
#####Main app ui#################################################333                        
def main_app_ui():
    check_inactivity()
    inject_login_styles()
    st.sidebar.markdown(f"###Welcome: **{st.session_state.current_user}**!")
    st.sidebar.markdown("Financial Document analyzer - Free Beta")
    privacy_and_data_control_ui()
    delete_account_ui()
    feedback_sidebar_ui()
    
    if st.sidebar.button("Log out", type="primary"):
        clear_sensitive_data()
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.rerun()
        
    st.sidebar.markdown("### Upload Type")
    upload_type = st.sidebar.radio("Select document type", ["Balance Sheet", "Trial Balance"])
    #Agree checkbox bfore uploading###########33
    agree = st.checkbox("I agree to the upload and processing of my financial document (ZAR).")
    if agree:
        if st.session_state.user_consent_time is None:
            st.session_state.user_consent_time = datetime.now(timezone.utc).isoformat()
    else:
        st.warning("You must agree to proceed.")
        st.stop()
    st.markdown("---")
    
    if upload_type == "Trial Balance":
        trial_balance.trial_balance_ui()
    else:
        balance_sheet.balance_sheet_ui()
        
    
    
def login_ui():
    """
    streamlit UI for login, registration, and password reset.
    """
    inject_login_styles()
    st.markdown("""
        <div style="text-align: center; margin-top: 5px; margin-bottom: 5px; width: 100%; display: block;">
            <h1 style="font-size: 48px; font-weight: 900; color: blue !important; margin: 0; padding: 0;">Finalizer </h1>       
            <p style="text-align: center"; "color: blue !important"; font-size: 18px; margin-top: 4px;">Minimalist Document Analyst</p>
        </div>
    """, unsafe_allow_html=True)
    
    MAX_LOGIN_ATTEMPTS = 10
    if st.session_state.login_attempts >= MAX_LOGIN_ATTEMPTS:
        st.error("Too many failed login attempts. Please try again later.")
        return
    
    if st.session_state.auth_page == "Login":   
        login_user = st.text_input("Username / Email", key="l_user", placeholder="Enter username")
        login_password = st.text_input("password", type="password", key="l_password", placeholder="Enter password")       
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Forgot Password?", type="secondary"):
                st.session_state.auth_page = "Forgot"
                st.rerun()
        with col2:
            if st.button("Create Account", type="secondary"):
               st.session_state.auth_page = "Register"
               st.rerun()                   
        if st.button("Login", type="primary"):  
            if login_user in st.session_state.user_db:
                stored = st.session_state.user_db[login_user]
                if isinstance(stored, dict) and "hash" in stored:
                    if verify_password(stored["hash"], login_password):
                        st.session_state.logged_in = True
                        st.session_state.current_user = login_user
                        st.session_state.is_admin = (login_user == "demo_user")
                        st.session_state.login_attempts = 0
                        st.rerun()
                    else:
                        st.session_state.login_attempts += 1
                        st.error("Incorrect password or email. Try again.")
                else:
                    st.error("User data corrupted. Please contact admin.")
            else:
                st.session_state.login_attempts += 1
                st.error("Incorrect password or email. Try again.")
                
    elif st.session_state.auth_page == "Register":
        st.markdown("<h3 style='margin-bottom:0;'>Create Account</h3>", unsafe_allow_html=True)
        new_user = st.text_input("Choose a Username", key="r_user", placeholder="Brand identifier").strip()
        new_password = st.text_input("Choose a Password", type="password", key="r_password", placeholder="Create a strong password")
        confirm_password = st.text_input("Confirm Password", type="password", key="r_conf", placeholder="Repeat password")                      
        if st.button("Back to Login", type="secondary"):
            st.session_state.auth_page = "Login"
            st.rerun()             
        if st.button("Register Account", type="primary"):
            if not new_user:
                st.error("Username cannot be blank.")
            else:
                is_valid, validation_msg = validate_username(new_user)
                if not is_valid:
                    st.error(validation_msg)
                elif not new_password or not confirm_password:
                    st.error("Passwords fields cannot be empty.")         
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                elif new_user in st.session_state.user_db:
                    st.error("Username already exists.")
                else:
                    is_strong, strength_msg = check_password_strength(new_password)
                    if is_strong:
                        hashed_pw = hash_password(new_password)
                        st.session_state.user_db[new_user] = {"hash": hashed_pw}
                        if save_to_local_database(st.session_state.user_db):
                            st.success("Account registered successfully.")
                            st.session_state.auth_page = "Login"
                            st.rerun()
                        else:
                            st.error("Failed to save user data. Try again.")
                    else:
                        st.error(strength_msg)
                
    elif st.session_state.auth_page == "Forgot":
        st.markdown("### Reset Password")
        reset_user = st.text_input("Enter Your Username", key="reset_user")
        new_password = st.text_input("New Password", type="password", key="reset_new_password")
        confirm_password = st.text_input("Confirm New Password", type="password", key="reset_confirm_password")
        
        if st.button("Reset Password"):
            if reset_user not in st.session_state.user_db:
                st.error("Username not found.")
            elif not new_password or not confirm_password:
                st.error("Please fill in both password fields.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                is_strong, msg = check_password_strength(new_password)
                if not is_strong:
                    st.error(msg)
                else:
                    hashed_pw = hash_password(new_password)
                    st.session_state.user_db[reset_user] = {"hash": hashed_pw}
                    if save_to_local_database(st.session_state.user_db):
                        st.success("Password reset successfully. Please log in.")
                        st.session_state.auth_page = "Login"
                        st.rerun()
                    else:
                        st.error("Failed to save new password. Try again.")
        if st.button("Back to login", type="secondary"):
            st.session_state.auth_page = "Login"
            st.rerun()
#__________________________________________________________________________________________________________________________             
def main():
    """
    main entry point of the app. Shows login page if not logged in else main app ui
    """   
    if not st.session_state.logged_in:
        login_ui()
    else:
        main_app_ui()
if __name__ == "__main__":
    main()
         
 