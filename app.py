import streamlit as st
from transformers import pipeline
from io import BytesIO
import pandas as pd
import numpy as np
import hashlib
import difflib
import logging
import torch
import nltk
import json
import os
import re
import io
import datetime
import time
import bcrypt
import base64
import threading
logging.basicConfig(level=logging.INFO)
def inject_login_styles():
    """
    custom css styles for login and app ui
    """
    st.markdown("""
        <style>
        html, body, .stApp, .AppHost [data-testid="stApp"] { background: radial-gradient(circle at top right,  #0F172A, #020617) !important; }
        
        div[data-testid="element-container"] + div[data-testid="element-container"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        
        .stMain h1, stMain h2, stMain h3, stMain p, stMain label {
            color: white !important;
            font-family: 'Inter', sans-serif !important;
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
            .chat-input-container {
                display: flex !important;
                flex-direction: column !important;
                gap: 10px !important;
            }
            img {
                max-width: 100% !important;
                height: auto !important;
            }
        }
        </style>
    """, unsafe_allow_html=True)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:   
    nltk.download('punkt')
db_lock = threading.Lock()#handle multiple users improves prevents data corruption 
DB_FILE = "user_database_profiles.json"
#####password utilities###############################################333333
def hash_password(password):
    """
    Hash a password with optional salt.
    Returns (salt, hash_password).
    """
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    return base64.b64encode(hashed).decode()

def verify_password(stored_hash_b64, password_attempt):
    """
    Verify password by hashing attempt with stored salt and comparing to stored hash.
    """
    try:
        hashed = base64.b64decode(stored_hash_b64)
        return bcrypt.checkpw(password_attempt.encode(), hashed)
    except Exception as e:
        logging.error(f"Password verification error: {e}")
        return False

def check_password_strength(password):
    """
    Check password strength with multiple criteria.
    """
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
    """
    validate username with rules:
    -8 to 20 characters
    -letters, numbers, underscores only
    """
    if not 3 <= len(username) <= 20:
        return False, "Username must be between 8 and 20 characters."
    if not re.match(r"^\w+$", username):
        return False, "Username can only contain letters, numbers, and underscores."
    return True, ""
def save_to_local_database(db_dict):
    """
    Save user database dictionary to JSON file.
    """
    try:
        with db_lock:
            with open(DB_FILE, "w") as f:
                json.dump(db_dict, f, indent=4)
        return True
    except Exception:
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

st.set_page_config(page_title="FinanceBox AI", layout="centered")
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
#ui login style################################################################################################

###pdf text extraction############################################
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
    elif any(k in text_blob for k in ["income statement", "profit", "revenue", "expenses", "sales", turnover]):
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
            f"This balance sheet shows total assets of {fmt(data.get('assets', 0))}, "
            f"total liabilities of {fmt(data.get('liabilities', 0))}, and equity of {fmt(data.get('equity', 0))}."
        )
    elif doc_type == "income_statement":
        return (
            f"This income statement reports revenue of {fmt(data.get('revenue', 0))}, "
            f"expenses of {fmt(data.get('expenses', 0))}, and a net income of {fmt(data.get('net income', 0))}."
        )
    return "No summary available."
#Transformer pipelines and document classification##################################

@st.cache_resource(show_spinner=True)
def load_chatbot():
    return pipeline("text-generation", model=distilgpt2)
  
def clear_sensitive_data():
    st.session_state.chat_history = []
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
        

def build_finance_prompt(user_question: str, financial_data: dict, doc_type: str, chat_history: list) -> str:
    system_instructions = (
        "You are a professional financial assistant specializing in analyzing financial documents such as balance sheets and income statements. "
        "Answer clearly, concisely, and accurately based only on the financial data provided. "
    )
    data_summary_lines = []
    for key, val in financial_data.items():
        if key != "validation_notes" and isinstance(val, (int, float)):
            data_summary_lines.append(f"{key.replace('_', ' ').title()}: R{val:,.2f}")
    
    data_summary = "\n".join(data_summary_lines) if data_summary_lines else "No finanacial data found."
    #Include last few users and bot messages for context (up to last 6)############################
    context = ""
    for msg in chat_history[-6:]:
        role = "User" if msg["role"] == "user" else "AI"
        context += f"{role}: {msg['content']}\n"
    prompt = (
        f"{system_instructions}\n\n"
        f"Financial data:\n{data_summary}\n\n"
        f"Conversation history:\n{context}\n"
        f"User question: {user_question}\n"
        f"AI:"
    )
    return prompt[-3000:] if len(prompt) > 3000 else prompt

def chatbot_ui():
    """
    streamlit UI for chatbot interaction.
    """
    st.subheader("Chat with AI")
    st.markdown("""
    <style>
    div.stButton > button {
        margin-top: 26px !important;
        height: 36px !important;
    }
    div.st.TextInput > div > input {
        height: 36px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if st.session_state.get("clear_input", False):
        st.session_state.chat_input = ""
        st.session_state.clear_input = False
    
    st.markdown(
        """
        <div class="chat-input-container" style="width: 100%;">
        """, unsafe_allow_html=True)
    user_input = st.text_input("Ask financeBox AI about your fianacial doc", key="chat_input", placeholder="E.g., What is my net income?")   
    send_clicked = st.button("Send", key="send_button", help="Send your question")
    st.markdown("</div>", unsafe_allow_html=True)
    
    if send_clicked and user_input.strip():
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        prompt = build_finance_prompt(user_input.strip(), financial_data, doc_type, st.session_state.chat_history)
        try:
            chatbot = load_chatbot()
            response = chatbot(prompt, max_length=150, num_return_sequences=1, do_sample=True, temperature=0.7, pad_token_id=50256)
            bot_reply = response[0]["generated_text"].strip()
            
            if bot_reply.lower().startswith(prompt.lower()):
                bot_reply = bot_reply[len(prompt):].strip()
        except Exception as e:
            bot_reply = f"Sorry, AI could not respond right now. Error: {str(e)}"
            logging.error(f"Chatbot error: {e}")
        st.session_state.chat_history.append({"role": "bot", "content": bot_reply})
        st.session_state.clear_input = True
        st.rerun()
        
    if st.session_state.chat_history:
        st.markdown("### Conversation")
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f"**You:** {msg['content']}")
            else:
                st.markdown(f"**AI:** {msg['content']}")
#Privacy and data control ui###########################################################################################                    
def privacy_and_data_control_ui():
    st.sidebar.markdown("### Privacy & Data Control")
    st.sidebar.info("""
    - Your uploaded documents are processed locally and not stored permanently.
    - Chat history is stored only for your current session and can be cleared anytime.
    - AI responses are generated based on extracted financial data; please verify critical decisions.
    - Data is encrypted and never used to train public AI models.
    """)
    st.markdown("[Privacy policy](#) | [Terms of Service](#)")
    
    if st.sidebar.button("Download Chat History"):
        if st.session_state.chat_history:
            chat_json = json.dumps(st.session_state.chat_history, indent=2)
            st.sidebar.download_button("Download JSON", chat_json, file_name="chat_history.json", mime="application/json")
        else:
            st.sidebar.info("No chat history to download.")

def delete_account_ui():
    st.markdown("Delete Account")
    if "confirm_delete" not in st.session_state:
        st.session_state.confirm_delete = False
    if not st.session_state.confirm_delete:
        if st.sidebar.button("Delete Account"):
            st.session_state.confirm_delete = True
    else:
        st.sidebar.warning("Are you sure? This action is irreversable.")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("Confirm Delete"):
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
    st.sidebar.markdown("### FinanceBox AI - Free version")
    privacy_and_data_control_ui()
    delete_account_ui()
    if st.sidebar.button("Log out", type="primary"):
        clear_sensitive_data()
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.rerun()
    #Show user list only for admin######################################3
    if st.session_state.current_user == "demo_user":
        show_user_list()
        
    st.title("FinanceBox AI")
    st.caption("Upload a financial spreadsheet (Excel/CSV) and get simplified results.")
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
        st.markdown("### Uploaded Documents")
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
                    
                st.markdown(f"### {doc_type.replace('-', ' ').title()} Data")
                cols = st.columns(3)
                col_idx = 0
                for key, value in financial_data.items():
                    if key != "validation_notes" and isinstance(value, (int, float)):
                        cols[col_idx % 3].metric(key.replace('_', ' ').title(), f"R{value:,.2f}")
                        col_idx += 1    
                if "validation_notes" in financial_data and financial_data["validation_notes"]:
                    st.markdown("### Financial Health & Validation Checks")
                    for note in financial_data["validation_notes"]:
                        st.markdown(f"- {note}")
                        #Show textual summary###############################################################
                summary_text = generate_summary(financial_data, doc_type)
                st.info(summary_text)
                        #CSV download for income statement data################################################
                df_financial = pd.DataFrame(list(financial_data.items()), columns=["Metric", "Value"])
                csv_financial = df_financial.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download {uploaded_file.name} Analysis (CSV)",
                    data=csv_financial,
                    file_name=f"{doc_type}_data.csv",
                    mime="text/csv"
                )
                    
                st.markdown("---")
    else:
        st.info("Upload your financial document to begin analysis.")
        
    st.markdown("---")
    #User feedback session##############################################################3
    st.header("📰 User Feedback")
    user_comment = st.text_area("Please share your feedback or suggestions to improve financebox AI:")
    if st.button("Submit Feedback"):
        if user_comment.strip():
            st.session_state.feedback_list.append({
                'Timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'Comment': user_comment.strip()
            })
            st.success("Thank you for your feedback!")
        else:
            st.warning("Please enter some feedback before submitting.")
    #Admin feedback dashboard (only visible to admin)########################################33
    if st.session_state.current_user == "demo_user":
        st.markdown("---")
        st.header("Admin Feedback Dashboard")
        if st.session_state.feedback_list:
            st.info(f"total feedback entries: {len(st.session_state.feedback_list)}")
            col1, col2 = st.columns([2, 1])
            with col1:
                st.subheader("Recent Feedback")
                for entry in reversed(st.session_state.feedback_list):
                    st.markdown(f"**{entry['Timestamp']}**")
                    st.info(entry['Comment'])
            with col2:
                st.subheader("Export & Manage")
                df_feedback = pd.DataFrame(st.session_state.feedback_list)
                csv_data = df_feedback.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download feedback as CSV",
                    data=csv_data,
                    file_name=f"FinanceBox_Feedback_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                )
                if st.button("Clear Feedback Logs"):
                    st.session_state.feedback_list = []
                    st.rerun()
        else:
            st.write("No feedback submitted yet.")
    chatbot_ui()

        
def login_ui():
    """
    streamlit UI for login, registration, and password reset.
    """
    inject_login_styles()
    st.markdown("""
        <div style="text-align: center; margin-top: 5px; margin-bottom: 5px; width: 100%; display: block;">
            <h1 style="font-size: 48px; font-weight: 900; color: blue !important; margin: 0; padding: 0;">FinanceBox AI </h1>       
            <p style="text-align: center"; "color: blue !important"; font-size: 18px; margin-top: 4px;">Minimalist Document Analyst</p>
        </div>
    """, unsafe_allow_html=True)
    
    MAX_LOGIN_ATTEMPTS = 5
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
        if st.button("Login FinanceBox AI", type="primary"):  
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
         
 