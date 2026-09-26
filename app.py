import streamlit as st
import os
import json
import hashlib
import re
import torch
from io import BytesIO
import io
import pandas as pd
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
from PIL import ImageFilter
from fpdf import FPDF
import easyocr
import difflib
import pymupdf as fitz
from transformers import pipeline
import numpy as np
from difflib import SequenceMatcher
import nltk
import logging
from collections import Counter

logging.basicConfig(level=logging.INFO)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:   
    nltk.download('punkt')
#session state initialization##################################
st.set_page_config(page_title="FinanceBox AI", layout="wide")
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "reset_trigger" not in st.session_state:
    st.session_state.reset_trigger = False
if "user_db" not in st.session_state:
    DB_FILE = "user_database_profiles.json"
    
    @st.cache_data(show_spinner=False)
    def load_local_database():
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                logging.error("Failed to load user database JSON file.")
                pass
        salt, hashed_pw = hash_password("Admin@123")
        return {"demo_user": {"salt": salt, "hash": hashed_pw}}
        
    st.session_state.user_db = load_local_database()
    
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "auth_page" not in st.session_state:
    st.session_state.auth_page = "Login"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
#password utilities############################################################
def hash_password(password, salt=None):
    """
    Hash a password with optional salt.
    Returns (salt, hash_password).
    """
    if salt is None:
        salt = os.urandom(16).hex()
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return salt, hashed
def verify_password(stored_salt, stored_hash, password_attempt):
    """
    Verify password by hashing attempt with stored salt and comparing to stored hash.
    """
    _, attempt_hash = hash_password(password_attempt, stored_salt)
    return attempt_hash == stored_hash
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
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>|]", password):
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
    DB_FILE = "user_database_profiles.json"
    try:
        with open(DB_FILE, "w") as f:
            json.dump(db_dict, f, indent=4)
        return True
    except Exception:
        logging.error(f"Failed to save user database: {e}")
        return False
#ui login style################################################################################################
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
        </style>
    """, unsafe_allow_html=True)
#OCR and pdf text extraction############################################
@st.cache_data(show_spinner=False)
def load_easyocr_reader():
    """
    load easyocr reader with english language and gpu if available
    """
    return easyocr.Reader(['en'], gpu=torch.cuda.is_available())

reader = load_easyocr_reader()

def preprocess_image_for_ocr(image_bytes, contrast=2.0, unsharp_radius=2, unsharp_percent=150, unsharp_threshold=3, median_size=3, threshold_val=140):
    """
    preprocess image bytes for ocr by enhancing contrast, sharpening, denoising, thresholding, and resizing
    """   
    image = Image.open(io.BytesIO(image_bytes)).convert("L")
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(contrast)   
    image = image.filter(ImageFilter.UnsharpMask(radius=unsharp_radius, percent=unsharp_percent, threshold=unsharp_threshold))
    image = image.filter(ImageFilter.MedianFilter(size=median_size)) 
    image = image.point(lambda p: 255 if p > threshold_val else 0)
    base_width = 1200
    wpercent = (base_width / float(image.size[0]))
    hsize = int((float(image.size[1]) * float(wpercent)))
    image = image.resize((base_width, hsize), Image.LANCZOS)
    return image

st.cache_data(show_spinner=False)
def extract_text_from_image(file_bytes):
    """
    extract text from image bytes using multiple preprocessing settings and easyocr.
    Combines results from different preprocessing variant for robustness
    """
    try:
        preprocessed_images = []
        preprocessed_images.append(preprocess_image_for_ocr(file_bytes, contrast=2.0, threshold_val=140))
        preprocessed_images.append(preprocess_image_for_ocr(file_bytes, contrast=1.8, unsharp_radius=1, unsharp_percent=120, threshold_val=130))
        preprocessed_images.append(preprocess_image_for_ocr(file_bytes, contrast=2.2, unsharp_radius=2, unsharp_percent=180, threshold_val=150))                           
        
        ocr_results = []
        for image in preprocessed_images:
            result = reader.readtext(np.array(image), detail=0, paragraph=True)
            ocr_results.append(" ".join(result).strip())            
        combined_text = " ".join(" ".join(ocr_results).strip())
        return combined_text if combined_text else "OCR_ERROR: No text was found"        
    except Exception as e:
        logging.exception("Image OCR failed")
        return f"OCR_ERROR: {str(e)}"
   
@st.cache_data(show_spinner=False)
def extract_text_from_pdf(file_bytes):
    """
    extract text from pdf bytes using pymupdf.Extracts text blocks from each page and concatenates
    """
    try:
        pdf = fitz.open(stream=file_bytes, filetype="pdf")
        full_text = []
        for page in pdf:
            blocks = page.get_text("blocks")
            page_text = " ".join(block[4] for block in blocks if block[4].strip())
            full_text.append(page_text)
        raw_text = "\n".join(full_text)       
        cleaned_text = clean_extracted_text(raw_text)          
        return cleaned_text
    except Exception as e:
        logging.exception("PDF extraction failed")
        return f"PDF_ERROR: {str(e)}"

def clean_extracted_text(text):
    """
    clean extracted text by normalizing white space and removing non-printable characters
    """
    text = re.sub(r"\s+", " ", text)
    text = "".join(c for c in text if c.isprintable())
    return text.strip()
 #financial data helpers################################### 
def clean_number(value_str):
    """
    clean and convert a string representing a number to float.Handle parentheses for negative numbers and removes common formatting characters
    """
    value_str = value_str.strip()
    if value_str.startswith('(') and value_str.endswith(')'):
        value_str = '-' + value_str[1:-1]
    value_str = re.sub(r"[,\s\$€£]", "", value_str)
    try:
        return float(value_str)
    except:
        return None

def extract_value_near_keyword(lines, idx, pattern, allow_negative=False):
    """
    search for numeric values near a keyword line within a window of lines returns the closest valid number found
    """
    window_size = 4
    start = max(0, idx - window_size)
    end = min(len(lines), idx + window_size + 1)
    candidates = []
    for i in range(start, end):
        matches = re.findall(pattern, lines[i], re.IGNORECASE)
        for match in matches:
            val = clean_number(match)
            if val is not None:
                if allow_negative or val >= 0:
                    candidates.append((val, abs(i - idx)))
    if candidates:
        candidates.sort(key=lambda x: (x[1], -abs(x[0])))
        return candidates[0][0]
    return None


def fuzzy_match(keyword, text, threshold=0.85):
    """
    perfom fuzzy matching between keyword and text with a similarity threshold
    """
    ratio = difflib.SequenceMatcher(None, keyword.lower(), text.lower()).ratio()
    return ratio >= threshold

def parse_balance_sheet(text):
    """
    parse_balance_sheet data from text using keyword matching and value extraction
    """
    keywords = {      
        "assets": [("total assets", 15), ("assets", 10), ("current assets", 12), ("non-current assets", 12), ("fixed assets", 10), ("property plant and equipment", 15), ("ppe", 10)],
        "liabilities": [("total liabilities", 15), ("liabilities", 10), ("current liabilities", 12), ("long-term liabilities", 12), ("debt", 10), ("loans payable", 12), ("accounts payable", 10)],
        "equity": [("total equity", 15), ("shareholders' equity", 15), ("stockholders' equity", 15), ("equity", 10), ("retained earnings", 12),("capital stock", 10), ("owner's equity", 12)]
    }
    data = {}
    lines = text.splitlines()
    number_pattern = r"\$?[\d,.]+"
    for key, kw_list in keywords.items():
        candidates = []
        for idx, line in enumerate(lines):
            line_lower = line.lower()
            for kw, weight in kw_list:
                
                if kw in line_lower or fuzzy_match(kw, line_lower):         
                    val = extract_value_near_keyword(lines, idx, number_pattern, allow_negative=False)
                    if val is not None and val != 0:
                        candidates.append((val, weight))
        if candidates:
            candidates.sort(key=lambda x: (-x[1], -x[0]))
            data[key] = candidates[0][0]
        else:        
            data[key] = 0.0
    return data

def parse_income_statement(text):
    """
    parse_income_statement data from text using keyword matching and value extraction
    """
    keywords = {      
        "revenue": [("revenue", 15), ("sales", 15), ("total sales", 15), ("turnover", 12), ("net sales", 12), ("operating revenue", 12), ("gross revenue", 12)],
        "expenses": [("expenses", 15), ("operating expenses", 15), ("cost of goods sold", 15), ("cogs", 15), ("selling expenses", 12), ("administrative expenses", 12), ("general expense", 12), ("research and development", 10), ("r&d expenses", 10)],
        "net_income": [("net income", 20), ("net profit", 20), ("profit", 18), ("net earnings", 18), ("net loss", 15), ("earnings", 15), ("bottom line", 15), ("income after tax", 15), ("net operating income", 15), ("comprehensive income", 12), ("profit after tax", 15), ("loss", 15)]
    }
    data = {}
    lines = text.splitlines()
    number_pattern = r"\$?[\d,.]+"
    for key, kw_list in keywords.items():
        candidates = []
        for idx, line in enumerate(lines):
            line_lower = line.lower()
            for kw, weight in kw_list:
                if kw in line_lower or fuzzy_match(kw, line_lower):
                    allow_negative = (key == "net_income")
                    val = extract_value_near_keyword(lines, idx, number_pattern, allow_negative=allow_negative)
                    if val is not None:
                        candidates.append((val, weight))
        if candidates:
            candidates.sort(key=lambda x: (-x[1], -abs(x[0])))
            data[key] = candidates[0][0]
        else:        
            data[key] = 0.0
    return data

def generate_summary(data):
    """
    generate a simple textual summary of key financial data points.
    """
    points = []
    if "net_income" in data:
        points.append(f"Net Income: ${data.get('net_income', 0):,.2f}.")
    if "revenue" in data:
        points.append(f"Revenue: ${data.get('revenue', 0):,.2f}.")
    if "expenses" in data:
        points.append(f"Expenses: ${data.get('expenses', 0):,.2f}.")
    if "assets" in data:
        points.append(f"Total Asssets: ${data.get('assets', 0):,.2f}.")
    if "liabilities" in data:
        points.append(f"Total Liabilities: ${data.get('liabilities', 0):,.2f}.")
    if "equity" in data:
        points.append(f"Total Equity: ${data.get('equity', 0):,.2f}.")
    return points

#Transformer pipelines and document classification##################################
@st.cache_resource(show_spinner=False)
def load_transformer_pipelines():
    """
    load transformer pipelines for classifications and ner
    """
    classifier = pipeline("text-classification", model="distilbert-base-uncased-fintuned-sst-2-english")
    ner = pipeline("ner", grouped_entities=True)
    return classifier, ner

classifier, ner = load_transformer_pipelines()

def chunk_text(text, max_tokens=512, overlaps=50):
    """
    split text into overlapping chunks of max_token tokens for transformer input
    """
    word = nltk.word_tokenize(text)
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + max_tokens, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = end - overlap
    return chunks
    
def detect_document_type(text):
    """
    transformer based document classification with fallback
    """
    if not text:
        return "unsupported"
    try:
        chunks = chunk_text(text)
        labels = []
        for chunk in chunks:
            results = classifier(chunk)
            label.append(results[0]['label'].lower())
        most_common_label = Counter(labels).most_common(1)[0][0]
        if "balance" in most_common_label:
            return "balance_sheet"
        elif "income" in most_common_label or "profit" in most_common_label:
            return "income_statement"
        else:
            return detect_document_type_keyword(text)
    except Exception as e:
        logging.error(f"Transformers classification failed: {e}")
        return detect_document_type_keyword(text)
    
def extract_financial_entities_transformer(text):
    """
    extract financial entities using transformer ner
    """
    try:
        chunks = chunk_text(text)
        all_entities = []
        money_values = []
        for chunk in chunks:
            entities = ner(chunk)
            all_entities.extend(entities)
        return all_entities
    except Exception as e:
        logging.error(f"Transformers NER failed: {e}")
        return []
    
def detect_document_type_keyword(text):
    """
    fallback keyword based document type detection
    """
    text_lower = text.lower()
    if any(k in text_lower for k in ["balance sheet", "assets", "liabilities"]):
        return "balance_sheet"
    elif any(k in text_lower for k in ["income statement", "profit", "revenue", "expenses"]):
        return "income_statement"
    else:
        return "unsupported"    
    
def parse_financial_data(text, doc_type):
    """
    combined transformer ner and keyword parsing to extract financial data.
    """
    transformer_data = extract_financial_entities_transformer(text)
    if doc_type == "balance_sheet":
        keyword_data = parse_balance_sheet(text)
    elif doc_type == "income_statement":
        keyword_data = parse_income_statement(text)
    else:
        keyword_data = {}
    if transformer_data.get("money_values"):
        logging.info(f"Transformer detected money entities: {transformer_data}")
    return keyword_data

######chatbot UI and Logic#################################

def load_chatbot():
    """
    load text generation pipeline for chatbot.
    """
    return pipeline("text-generation", model="distilgpt2")

def build_finance_prompt(user_question: str, financial_data: dict, doc_type: str, chat_history: list) -> str:
    """
    buit prompt for chatbot with system instructions and financial data summary.
    """
    system_instructions = (
        "You are a professional financial assistant. "
        "Answer clearly and concisely based only on the financial data provided. "
        "If you don't know the answer, say so politetly. "
        "Explain financial terms simply and provide actionable advice when possible."
    )
    data_summary_lines = []
    if doc_type == "balance_sheet":
        for key in ["assets", "liabilities", "equity"]:
            if key in financial_data:
                val = financial_data[key]
                data_summary_lines.append(f"{key.title()}: ${val:,.2f}")
    elif doc_type == "income_statement":
        for key in ["revenue", "expenses", "net_income"]:
            if key in financial_data:
                val = financial_data[key]
                data_summary_lines.append(f"{key.replace('_', ' ').title()}: ${val:,.2f}")
    else:
        data_summary_lines.append("No financial data available.")
    data_summary = "\n".join(data_summary_lines)
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
        f"Answer:"
    )
    return prompt[-3000:] if len(prompt) > 3000 else prompt

def suggest_follow_ups(doc_type: str, financial_data: dict) -> list:
    """
    suggest follow up questions based on document type and financial data.
    """
    suggestions = []
    question_lower = last_user_question.lower()
    if doc_type == "balance_sheet":
        if "debt" in question_lower or "liabilities" in question_lower:
            suggestions.append("Would you like me to explain how debt affects your health?")
        if financial_data.get("liabilities", 0) > financial_data.get("equity", 0):
            suggestions.append("Your liabilities exceed equity, would you like advice on managing financial risk?")
    elif doc_type == "income_statement":
        if "profit" in question_lower or "net_income" in question_lower:
            suggestions.append("Would you like a summary of profit margins?")
        if financial_data.get("net_income", 0) < 0:
            suggestions.append("Your net income is negative, would you like suggestions to improve profitability?")
    else:
        suggestions.append("Feel free to ask any questions about your financial document.?")
    return suggestions
        
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
    col1, col2 = st.columns([0.9, 0.1])
    user_input = col1.text_input("ask financeBox AI about your fianacial doc", key="chat_input", placeholder="E.g., What is my net income?")
    
    send_clicked = col2.button("Send", key="send_button")    
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
         #get last user question for suggestions############################################################################################       
        last_question = ""
        for msg in reversed(st.session_state.chat_history):
            if msg["role"] == "user":
                last_question = msg["content"]
                break
        suggestions = suggest_follow_ups(doc_type, financial_data, last_question)
        if suggestions:
            st.markdown("### suggestions")
            for s in suggestions:             
                if st.button(s):
                    st.session_state.chat_input = s
                    st.session_state.clear_input = False
                    st.rerun()
#Privacy and data control ui###########################################################################################                    
def privacy_and_data_control_ui():
    st.sidebar.markdown("### Privacy & Data Control")
    st.sidebar.info("""
    - Your uploaded documents are processed locally and not stored permanently.
    - Chat history is stored only for your current session and can be cleared anytime.
    - AI responses are generated based on extracted financial data; please verify critical decisions.
    """)
    if st.sidebar.button("Clear Chat History"):
        st.session_state.chat_history = []
        st.sidebar.success("Chat history cleared.")
        
def show_user_list():
    st.subheader("Registered Users")
    user_db = st.session_state.user_db
    total_users = len(user_db)
    st.write(f"Total registered users: {total_users}")
    st.write("User List:")
    for username in user_db.keys():
        st.write(f"- {username}")
#Main UI functions###########################                    
def clear_chat():
    if st.confirm("Are you sure you want to clear the chat history?"):
        st.session_state.chat_history = []
        
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
                if isinstance(stored, dict) and "salt" in stored and "hash" in stored:
                    if verify_password(stored["salt"], stored["hash"], login_password):
                        st.session_state.logged_in = True
                        st.session_state.current_user = login_user
                        st.session_state.is_admin = (login_user == "demo_user")
                        st.rerun()
                    else:
                        st.error("Incorrect password or email. Try again.")
                else:
                    st.error("User data corrupted. Please contact admin.")
            else:
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
                        salt, hashed_pw = hash_password(new_password)
                        st.session_state.user_db[new_user] = {"salt": salt, "hash": hashed_pw}
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
                    salt, hashed_pw = hash_password(new_password)
                    st.session_state.user_db[reset_user] = {"salt": salt, "hash": hashed_pw}
                    if save_to_local_database(st.session_state.user_db):
                        st.success("Password reset successfully. Please log in.")
                        st.session_state.auth_page = "Login"
                        st.rerun()
                    else:
                        st.error("Failed to save new password. Try again.")
        if st.button("Back to login", type="secondary"):
            st.session_state.auth_page = "Login"
            st.rerun()
            
                        
def main_app_ui():
    inject_login_styles()
    st.sidebar.markdown(f"###Welcome: **{st.session_state.current_user}**!")
    st.sidebar.markdown("### FinanceBox AI - Free version")
    privacy_and_data_control_ui()
    if st.sidebar.button("Log out", type="primary"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        clear_chat()
        st.rerun()
    #Show user list only for admin######################################3
    if st.session_state.current_user == "demo_user":
        show_user_list()
        
    st.title("FinanceBox AI")
    st.caption("Upload a financial image or PDF and get simplified results.")
    #Agree checkbox bfore uploading###########33
    agree = st.checkbox("I agree to upload and processing of my financial doc.")
    if not agree:
        st.warning("You must agree to proceed.")
        st.stop()
        
    uploaded_files = st.file_uploader(
        "Upload your financial documents",
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="document_upload",
    )
    
    global financial_data, doc_type
    financial_data = {}
    doc_type = "unsupported"
    
    if uploaded_files:
        st.markdown("### Uploaded Documents")
        for uploaded_file in uploaded_files:
            if uploaded_file.size > 10 * 1024 * 1024:
                st.error(f"{uploaded_file.name} is too large. Max size is 10MB.")
                continue
            file_bytes = uploaded_file.read()
            
            with st.container():
                st.markdown(f"### {uploaded_file.name}")
                if uploaded_file.type.startswith("image/"):
                    try:
                        image = Image.open(BytesIO(file_bytes)).convert("RGB")
                        st.image(image, caption=uploaded_file.name, width=300)
                    except Exception as e:
                        st.error(f"Could not display image: {e}")
                        
                
                if uploaded_file.type == "application/pdf":
                    with st.spinner(f"Extracting text from PDF: {uploaded_file.name}"):
                        text = extract_text_from_pdf(file_bytes)
                elif uploaded_file.type.startswith("image/"):
                    with st.spinner(f"Extracting text from image: {uploaded_file.name}"):
                        text = extract_text_from_image(file_bytes)
                else:
                    text = ""                  
                if text.startswith("OCR_ERROR") or text.startswith("PDF_ERROR"):
                    st.error(text)
                    continue
                if not text.strip():
                    st.warning("No readable text was found in this file.")
                    continue
                          
                doc_type = detect_document_type(text)
                st.markdown(f"**Detected Document Type:** {doc_type.replace('_', ' ').title()}")
                
                if doc_type == "unsupported":
                    st.warning("Unsupported document type. Please upload only Balance Sheets or Income Statements.")
                    continue
                elif doc_type == "ambiguous_financial_doc":
                    st.warning("The document appears to contain mixed or ambiguous financial data. Please verify the document type.")
                    continue
                
                if doc_type == "balance_sheet":
                    financial_data = parse_balance_sheet(text)
                    st.markdown("### Balance Sheet Data")
                    if financial_data:
                        for key, value in financial_data.items():
                            st.metric(key.title(), f"${value:,.2f}")
                    else:
                        st.info("No Key Balance Sheet data found.")
                 
                elif doc_type == "income_statement":
                    financial_data = parse_income_statement(text)
                    st.markdown("### Income Statement Data")
                    if financial_data:
                        for key, value in financial_data.items():
                            st.metric(key.title().replace("_", " "), f"${value:,.2f}")
                    else:
                        st.info("No Key Income Statement data found.")
               
                st.markdown("---")
    else:
        st.info("Upload your financial document to begin analysis.")
        
    st.markdown("---")   
    chatbot_ui()
              
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
         
 