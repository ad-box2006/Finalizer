import streamlit as st
from io import BytesIO
import pandas as pd
import numpy as np
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
from email.message import EmailMessage
DEVELOPER_EMAIL = "katlegokirra@gmail.com"
GMAIL_APP_PASSWORD = "yogqyswdhrphwggi"

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

@st.cache_data(show_spinner=False)
def load_financial_file(file_bytes, file_name):
    try:
        if file_name.endswith('.csv'):
            df = pd.read_csv(BytesIO(file_bytes))
        else:
            xls = pd.ExcelFile(BytesIO(file_bytes))
            sheet_name = xls.sheet_names[0]
            df = pd.read_excel(xls, sheet_name=sheet_name)
        return df
    except Exception as e:
        logging.exception("File loading failed")
        return f"FILE_ERROR: {str(e)}"

def clean_number(value_str):
    if pd.isna(value_str):
        return None
    if isinstance(value_str, (int, float)):
        return float(value_str)
    value_str = str(value_str).strip()
    if value_str.startswith("(") and value_str.endswith(")"):
        value_str = "-" + value_str[1:-1]
    value_str = re.sub(r"[,\sR€£$]", "", value_str)
    try:
        return float(value_str)
    except:
        return None
    
def detect_document_type_from_df(df):
    text_blob = " ".join([str(col).lower() for col in df.columns])
    for idx, row in df.head(15).iterrows():
        text_blob += " " + " ".join([str(val).lower() for val in row.values if pd.notna(val)])
    if any(k in text_blob for k in ["balance sheet", "assets", "liabilities", "equity"]):
        return "balance_sheet"
    elif any(k in text_blob for k in ["income statement", "profit", "revenue", "expenses", "sales", "turnover"]):
        return "income_statement"
    else:
        return "unsupported"    

def parse_dataframe_metrics(df, doc_type):
    if doc_type == "balance_sheet":
        keywords = {      
            "assets": ["total assets"],
            "current_assets": ["total current assets"],
            "non-current assets": ["total fixed assets", "total non-current assets", "non-current assets", "fixed_assets"],
            "cash": ["cash and cash equivalents", "cash"],
            "liabilities": ["total liabilities", "liabilities"],
            "current_liabilities": ["total current liabilities", "current liabilities"],
            "equity": ["total equity"]
        }
    else:
        keywords = {
            "revenue": ["total revenue", "revenue", "sales", "turnover", "net sales"],
            "expenses": ["total expenses", "operating expenses", "cost of goods sold", "cogs", "expenses"],
            "net_income": ["net income", "net profit", "profit", "net earnings"]
        }  
    data = {}
    df = df.dropna(how='all').reset_index(drop=True)
    for key, kw_list in keywords.items():
        found_val = 0.0
        for idx, row in df.iterrows():
            row_vals = [str(val).strip().lower() for val in row.values if pd.notna(val)]
            if not row_vals:
                continue
            row_str = " ".join(row_vals)
            matched = any(kw == row_vals[0] for kw in row_str for kw in kw_list)
            if matched:
                for val in row.values:
                    num = clean_number(val)
                    if num is not None and num != 0.0:
                        found_val = num
                        break
                if found_val != 0.0:
                        break
        data[key] = found_val
        
    validation_notes = []
    if doc_type == "balance_sheet":
        tot_assets = data.get("assets", 0)
        tot_liab = data.get("liabilities", 0)
        tot_equity = data.get("equity", 0)
        if tot_assets > 0 and (tot_liab > 0 or tot_equity > 0):
            expected_le = tot_liab + tot_equity
            if abs(tot_assets - expected_le) > 1.0:
                validation_notes.append(f"Balance Sheet Mismatch: Assets (R{tot_assets:,.2f}) != Liabilities + Equity (R{expected_le:,.2f})")
            else:
                validation_notes.append(f"Balance Sheet equation balances perfectly! Assets (R{tot_assets:,.2f}) = Liabilities + Equity (R{expected_le:,.2f})")
    elif doc_type == "income_statements":
        rev = data.get("revenue", 0.0)
        exp = data.get("expenses", 0.0)
        net = data.get("net_income", 0.0)
        if rev > 0 and exp > 0:
            calculated_net = rev - exp
            data["calculated_net_income"] = calculated_net
            if net == 0.0:
                data["net_income"] = calculated_net
                validation_notes.append(f"Net Income was inferred via formula (Revenue - Expenses): R{calculated_net:,.2f}")
            else:
                validation_notes.append("Income statement formula checks out cleanly.")
    data["validation_notes"] = validation_notes
    return data
#Generate textual summary of financial data#########################################################################33
def generate_summary(data, doc_type):
    def fmt(val):
        return f"R{val:,.2f}" if isinstance(val, (int, float)) and val != 0 else "R0.00"
    
    if doc_type == "balance_sheet":
        return (
            f"This balance sheet shows total assets of"
            f" {fmt(data.get('assets', 0))}, total liabilities of"
            f" {fmt(data.get('liabilities', 0))}, and equity of"
            f" {fmt(data.get('equity', 0))}."
        )
    elif doc_type == "income_statement":
        return (
            f"This income statement reports revenue of"
            f" {fmt(data.get('revenue', 0))}, expenses of"
            f" {fmt(data.get('expenses', 0))}, and a net income of"
            f" {fmt(data.get('net_income', 0))}."
        )
    return "No summary available."
#Transformer pipelines and document classification##################################
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
    - Your uploaded documents are processed locally and not stored permanently.
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
    with st.sidebar.form("feedback_form"):
        user_email = st.text_input("Your Email (optional):")
        feedback_text = st.text_area("Thoughts or bug reports?")
        submitted = st.form_submit_button("Send Feedback")
        if submitted:
            if not feedback_text.strip():
                st.warning("Please enter some feedback first.")
            else:
                try:
                    msg = EmailMessage()
                    msg.set_content(
                        f"New feedback from Finalizer user:"
                        f" {st.session_state.current_user}\nUser Email Provided:"
                        f" {user_email}\n\nFeedback:\n{feedback_text}"
                    )
                    msg["Subject"] = "Finalizer Beta Feedback"
                    msg["From"] = DEVELOPER_EMAIL
                    msg["To"] = DEVELOPER_EMAIL
                    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                        server.login(DEVELOPER_EMAIL, EMAIL_APP_PASSWORD)
                        server.send_message(msg)
                    st.success("Thank You! Feedback sent to developer.")
                except Exception as e:
                    st.error("Could not send email right now.")    
#A show list for admin###########################                    
def show_user_list():
    st.subheader("Registered Users")
    user_db = st.session_state.user_db
    total_users = len(user_db)
    st.write(f"Total registered users: {total_users}")
    st.write("User List:")
    for username in user_db.keys():
        st.write(f"- {username}")           
#####Main app ui#################################################333                        
def main_app_ui():
    check_inactivity()
    inject_login_styles()
    st.sidebar.markdown(f"###Welcome: **{st.session_state.current_user}**!")
    st.sidebar.markdown("Finalizer - Free Beta")
    privacy_and_data_control_ui()
    delete_account_ui()
    feedback_sidebar_ui()
    if st.sidebar.button("Log out", type="primary"):
        clear_sensitive_data()
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.rerun()
        
    
    #Show user list only for admin######################################3
    if st.session_state.current_user == "demo_user":
        show_user_list()
    st.title("Finalizer | SA Finance")
    st.caption("An easy way to check if your balance sheet or income statement is healthy and follows south african tax rules.")
    #Agree checkbox bfore uploading###########33
    agree = st.checkbox("I agree to upload and processing of my financial doc.")
    if agree:
        if st.session_state.user_consent_time is None:
            st.session_state.user_consent_time = datetime.datetime.utcnow().isoformat()
    else:
        st.warning("You must agree to proceed.")
        st.stop()
        
    uploaded_files = st.file_uploader(
        "Upload your financial document",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True,
        key="document_upload",
    )
    
    if uploaded_files:
        st.markdown("### Uploaded Documents Analysis")
        for uploaded_file in uploaded_files:
            if uploaded_file.size > 10 * 1024 * 1024:
                st.error(f"{uploaded_file.name} is too large. Max size is 10MB.")
                continue
            file_bytes = uploaded_file.read()
            
            with st.container():
                st.markdown(f"### {uploaded_file.name}")
                df = load_financial_file(file_bytes, uploaded_file.name)
                              
                if isinstance(df, str) and df.startswith("FILE_ERROR"):
                    st.error(df)
                    continue
                if df.empty:
                    st.warning("No readable text was found in this file.")
                    continue
                
                doc_type = detect_document_type_from_df(df)
                st.session_state.doc_type = doc_type
                st.markdown(f"**Detected Document Type:** {doc_type.replace('_', ' ').title()}")
                
                if doc_type == "unsupported":
                    st.warning("Unsupported document type. Please upload only Balance Sheets or Income Statements.")
                    continue
                
                financial_data = parse_dataframe_metrics(df, doc_type)
                st.session_state.financial_data = financial_data
                if len(df.columns) >= 6:
                    cleaned_display_df = df.iloc[:, [0, 5]].copy()
                else:
                    cleaned_display_df = df.iloc[:, [0, min(1, len(df.columns)-1)]].copy()
                cleaned_display_df.columns = ["Financial Line Item", "Amount (ZAR)"]
                cleaned_display_df = cleaned_display_df.dropna(subset=["Amount (ZAR)"])
               
                st.markdown("### Itemized Statement Breakdown")
                st.dataframe(cleaned_display_df, use_container_width=True)
               
                st.sidebar.markdown("---")
                st.sidebar.markdown("### SA Financial Config")
                total_revenue = st.sidebar.number_input("Annual Revenue / Turnover (ZAR)", value=float(financial_data.get('revenue', 2500000.0)), step=50000.0)
                current_assets = st.sidebar.number_input("Current Assets (ZAR)", value=float(financial_data.get('current_assets', 500000.0)), step=10000.0)
                current_liabilities = st.sidebar.number_input("Current Liabilities (ZAR)", value=float(financial_data.get('current_liabilities', 300000.0)), step=10000.0)
                total_liabilities = st.sidebar.number_input("Total Liabilities (ZAR)", value=float(financial_data.get('liabilities', 600000.0)), step=10000.0)
                total_equity = st.sidebar.number_input("Total Equity (ZAR)", value=float(financial_data.get('equity', 400000.0)), step=10000.0)
                
                current_ratio = round(current_assets / current_liabilities, 2) if current_liabilities > 0 else 0.0
                debt_to_equity = round(total_liabilities / total_equity, 2) if total_equity > 0 else 0.0
                score = 100
                if current_ratio < 1.0:
                    score -= 35
                elif current_ratio < 1.5:
                    score -= 15
                if debt_to_equity > 2.0:
                    score -= 40
                elif debt_to_equity > 1.0:
                    score -= 20
                health_score = max(score, 0)
                
                sars_checks = []
                if total_revenue >= 2300000:
                    sars_checks.append({
                        "item": "Voluntary VAT Registration",
                        "status": "Action Required",
                        "detail": "Turnover meets or exceeds the R2.3M compulsory VAT threshold. Ensure registration with SARS."
                    })
                elif total_revenue >= 120000:
                    sars_checks.append({
                        "item": "Voluntary VAT Registration",
                        "status": "Eligible",
                        "detail": "Turnover qualifies for voluntary VAT registration (above R120,000)."
                    })
                else:
                    sars_checks.append({
                        "item": "Voluntary Threshold Status",
                        "status": "Compliant",
                        "detail": "Turnover is below compulsory VAT registration thresholds."
                    })
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(label="Financial Health Score", value=f"{health_score}/100", delta="Healthy" if health_score >= 70 else "Needs Review")
                with col2:
                    st.metric(label="Current Ratio (Liquidity)", value=current_ratio, delta="Optimal > 1.5" if current_ratio >= 1.5 else "Low Liquidity")
                with col3:
                    st.metric(label="Debt-To-Equity", value=debt_to_equity, delta="Safe < 1.0" if debt_to_equity <= 1.0 else "High Leverage")
                st.markdown("### SARS Tax & Compliance Checks")
                for check in sars_checks:
                    if "Action Required" in check["status"]:
                        st.error(f"**{check['item']}** ({check['status']}): {check['detail']}")
                    elif "Eligible" in check["status"]:
                        st.warning(f"**{check['item']}** ({check['status']}): {check['detail']}")
                    else:
                        st.success(f"**{check['item']}** ({check['status']}): {check['detail']}")
                st.markdown("### MULTY-PERIOD Trend Simulation")
                with st.expander("Compare with Previous Period"):
                    prev_revenue = st.number_input("Previous Period Revenue (ZAR)", value=float(total_revenue * 0.9), step=50000.0)
                    if prev_revenue > 0:
                        growth_pct = round(((total_revenue - prev_revenue) / prev_revenue) * 100, 2)
                        st.metric("Revenue Growth Year-over-Year", f"{growth_pct}%", delta="Growing" if growth_pct > 0 else "Declining")
                    else:
                        st.info("Enter previous period metrics to compute variance.")
                summary_text = generate_summary(financial_data, doc_type)
                st.info(summary_text)
                
                st.markdown("---")
                table_html = cleaned_display_df.to_html(classes='dataframe', index=False)
                html_report = f"""
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; color: #333; padding: 20px; }}
                        h1 {{ color: #0f172a; border-bottom: 2px solid #cbd5e1; padding-bottom: 10px; }}
                        .card {{ background: #f8fafc; padding: 15px; margin-bottom: 15px; border-radius: 8px; border: 1px solid #e2e8f0; }}
                        .score {{ font-size: 24px; font-weight: bold; color: #2563eb; }}
                        table.dataframe {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                        table.dataframe th, table.dataframe td {{ border: 1px solid #cbd5e1; padding: 8px; text-align: left; font-size: 14px; }}
                        table.dataframe th, {{ background-color: #f1f5f9; }}
                    </style>
                </head>
                <body>
                    <h1>Finalizer - SA Executive Financial Health Report</h1>
                    <div class="card">
                        <h3>Financial Health Score</h3>
                        <p class="score">{health_score}/100</p>
                    </div>
                    <div class="card">
                        <h3>Core Ratios</h3>
                        <p><b>Current Ratio:</b> {current_ratio}</p>
                        <p><b>Debt-to-Equity Ratio:</b> {current_ratio}</p>
                    </div>
                    <div class="card">
                        <h3>SARS Compliance Status</h3>
                        <p><b>{sars_checks[0]['item']}:</b> {sars_checks[0]['status']} - {sars_checks[0]['detail']}</p>
                    </div>
                    <div class="card">
                        <h3>Itemized Statement</h3>
                        {table_html}
                    </div>
                </body>
                </html>
                """
                st.download_button(
                    label=f"Download Branded Report for {uploaded_file.name} (HTML)",
                    data=html_report,
                    file_name=f"Finalizer_Report_{uploaded_file.name}.html",
                    mime="text/html",
                )
                st.markdown("---")
    else:
        st.info("Upload your financial document to begin analysis.")
    
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
        if st.button("Login Finalizer", type="primary"):  
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
         
 