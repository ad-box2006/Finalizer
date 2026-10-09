
import streamlit as st
from io import BytesIO
import pandas as pd
import re
import io
import datetime
from datetime import timezone

def clean_number(value_str):
    if pd.isna(value_str):
        return None
    if isinstance(value_str, (int, float)):
        return float(value_str)
    value_str = str(value_str).strip()
    if value_str.startswith("(") and value_str.endswith("("):
        value_str = "-" + value_str[1:-1]
    value_str = re.sub(r"[R,\s€£$]", "", value_str)
    try:
        return float(value_str)
    except:
        return None

def validate_balance_sheet_structure(df):
    """Detects if the user accidentally uploaded a trial balance into the balance sheet tab."""
    text_content = df.to_string().lower()
    trial_balance_markers = ["unadjusted debit", "adjustments debit", "trial balance worksheet", "adjusted debit"]
    for marker in trial_balance_markers:
        if marker in text_content:
            return False, " **Document Type Mismatch:** This appears to be a Trial Balance sheet, but you are in the Balance Sheet section. Please switch tabs or upload a valid Balance Sheet."
        return True, ""
    
@st.cache_data(show_spinner=False)
def load_balance_sheet_file(file_bytes, file_name):
    try:
        if file_name.endswith('.csv'):
            df = pd.read_csv(BytesIO(file_bytes), header=None)
        else:
            xls = pd.ExcelFile(BytesIO(file_bytes))
            best_sheet = xls.sheet_names[0]
            max_filled = -1
            for sheet in xls.sheet_names:
                temp = pd.read_excel(xls, sheet_name=sheet, header=None)
                filled_count = temp.notna().sum().sum()
                if filled_count > max_filled:
                    max_filled = filled_count
                    best_sheet = sheet
               
            df = pd.read_excel(xls, sheet_name=best_sheet, header=None)
            header_idx = 0
            for idx, row in df.head(12).iterrows():
                row_text = " ".join([str(val).lower() for val in row.values if pd.notna(val)])
                if any(k in row_text for k in ["assets", "liabilities", "equity", "balance sheet", "description", "item", "account"]):
                    header_idx = idx
                    break
            if header_idx > 0:
                df.columns = df.iloc[header_idx]
                df = df.iloc[header_idx + 1:].reset_index(drop=True)
            else:
                df.columns = [f"col_{i}" for i in range(df.shape[1])]
           
        return df
    except Exception as e:
        logging.exception("File loading failed")
        return f"FILE_ERROR: {str(e)}"
    
def parse_balance_sheet_metrics(df):
    keywords = {      
        "assets": ["total assets"],
        "current_assets": ["total current assets"],
        "non-current assets": ["total fixed assets", "total non-current assets", "non-current assets"],
        "cash": ["cash and cash equivalents", "cash"],
        "liabilities": ["total liabilities", "liabilities"],
        "current_liabilities": ["total current liabilities", "current liabilities"],
        "equity": ["total equity"]
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
            matched = any(kw in row_str for kw in kw_list)
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
    tot_assets = data.get("assets", 0)
    tot_liab = data.get("liabilities", 0)
    tot_equity = data.get("equity", 0)
         
    if tot_assets > 0 and (tot_liab > 0 or tot_equity > 0):
        expected_le = tot_liab + tot_equity
        if abs(tot_assets - expected_le) > 5.0:
            validation_notes.append(f"Balance Sheet check notice: Total Assets (R{tot_assets:,.2f}) do not equal Total Liabilities & Equity (R{expected_le:,.2f}). Please check your spread sheet entries are mapped correctly.")
        else:
            validation_notes.append(f"Balance Sheet equation verified: Total Assets (R{tot_assets:,.2f}) matches Total Liabilities & Equity (R{expected_le:,.2f}).")
    else:
        validation_notes.append(f"Balance Sheet parsed successfully.")
    data["validation_notes"] = validation_notes
    return data
#Generate textual summary of financial data#########################################################################33
def generate_summary(data):
    def fmt(val):
        return f"R{val:,.2f}" if isinstance(val, (int, float)) and val != 0 else "R0.00"
    
    
    return (
        f"This balance sheet reports total assets of"
        f" {fmt(data.get('assets', 0))}, total liabilities of"
        f" {fmt(data.get('liabilities', 0))}, and equity of"
        f" {fmt(data.get('equity', 0))}."
    )
def balance_sheet_ui():
    st.title("Finalizer | SA Balance Sheet analyzer")
    st.caption("Verify your financial documents instantly with automated parsing and compliance checks.")
    
    uploaded_files = st.file_uploader(
        "Upload your balance sheet document",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True,
        key="document_upload",
    )
    
    if uploaded_files:
        st.markdown("### Balance Sheet Analysis")
        for uploaded_file in uploaded_files:
            if uploaded_file.size > 10 * 1024 * 1024:
                st.error(f"{uploaded_file.name} is too large. Max size is 10MB.")
                continue
            file_bytes = uploaded_file.read()
            
            with st.container():
                st.markdown(f"### {uploaded_file.name}")
                df = load_balance_sheet_file(file_bytes, uploaded_file.name)
                              
                if isinstance(df, str) and df.startswith("FILE_ERROR"):
                    st.error(df)
                    continue
                if df.empty:
                    st.warning("No readable data was found in this file.")
                    continue
                
                is_valid, error_msg = validate_balance_sheet_structure(df)
                if not is_valid:
                    st.error(error_msg)
                    continue
                
                financial_data = parse_balance_sheet_metrics(df)
                st.session_state.financial_data = financial_data
                
                df = df.dropna(how='all').dropna(axis=1, how='all').reset_index(drop=True)
                text_col = df.columns[0]
                
                for col in df.columns:
                    sample_vals = df[col].dropna().head(10)
                    text_count = sum(1 for v in sample_vals if isinstance(v, str) and not re.match(r"^[\d,\.\sR-]+$", v))
                    if text_count > 2:
                        text_col = col
                        break
                amount_col = None
                max_nums = -1
                for col in df.columns:
                    if col == text_col:
                        continue
                        
                    num_count = sum(1 for v in df[col] if clean_number(v) is not None and clean_number(v) != 0.0)
                    if num_count > max_nums:
                        max_nums = num_count
                        amount_col = col
             
                if amount_col is None:
                    amount_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
              
                cleaned_display_df = df[[text_col, amount_col]].copy()   
                cleaned_display_df.columns = ["Financial Line Item", "Amount (ZAR)"]  
                cleaned_display_df["Amount (ZAR)"] = cleaned_display_df["Amount (ZAR)"].apply(clean_number)   
                cleaned_display_df = cleaned_display_df.dropna(subset=["Financial Line Item"])
                cleaned_display_df["Financial Line Item"] = cleaned_display_df["Financial Line Item"].astype(str).str.strip()
                cleaned_display_df = cleaned_display_df[cleaned_display_df["Financial Line Item"] != "nan"]
                cleaned_display_df["Amount (ZAR)"] = cleaned_display_df["Amount (ZAR)"].fillna(0.0)
                
                st.markdown("### Itemized Balance Sheet Breakdown")
                st.dataframe(cleaned_display_df, use_container_width=True)
               
                st.sidebar.markdown("---")
                st.sidebar.markdown("### SA Balance Sheet Config")
                total_assets = st.sidebar.number_input("Total Assets (ZAR)", value=float(financial_data.get('assets', 1000000.0)), step=50000.0)
                current_assets = st.sidebar.number_input("Current Assets (ZAR)", value=float(financial_data.get('current_assets', 400000.0)), step=10000.0)
                current_liabilities = st.sidebar.number_input("Current Liabilities (ZAR)", value=float(financial_data.get('current_liabilities', 200000.0)), step=10000.0)
                total_liabilities = st.sidebar.number_input("Total Liabilities (ZAR)", value=float(financial_data.get('liabilities', 500000.0)), step=10000.0)
                total_equity = st.sidebar.number_input("Total Equity (ZAR)", value=float(financial_data.get('equity', 500000.0)), step=10000.0)
                
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
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(label="Solvency & Health Score", value=f"{health_score}/100", delta="Healthy" if health_score >= 70 else "Needs Review")
                with col2:
                    st.metric(label="Current Ratio (Liquidity)", value=current_ratio, delta="Optimal > 1.5" if current_ratio >= 1.5 else "Low Liquidity")
                with col3:
                    st.metric(label="Debt-To-Equity", value=debt_to_equity, delta="Safe < 1.0" if debt_to_equity <= 1.0 else "High Leverage")
                st.markdown("---")
                sars_checks = [
                    {
                        "item": "Solvency & Capital Adequacy",
                        "status": "Compliant" if total_assets >= total_liabilities else "Risk Detected",
                        "detail": f"Assets (R{total_assets:,.2f}) exceed liabilities (R{total_liabilities:,.2f}) ensuring positive net worth." if total_assets >= total_liabilities else f"Liabilities (R{total_liabilities:,.2f}) exceed assets (R{total_assets:,.2f})."
                    },
                    {
                        "item": "Liquidity Threshold (Current Ratio)",
                        "status": "Optimal" if current_ratio >= 1.0 else "Sub_optimal",
                        "detail": f"Current ratio is {current_ratio} (Target: > 1.5)."
                    }
                ]
                for item_dict in sars_checks:
                    if item_dict["status"] in ["Compliant", "Optimal"]:
                        st.success(f"**{item_dict['item']}**: {item_dict['status']} - {item_dict['detail']}")
                    else:
                        st.warning(f"**{item_dict['item']}**: {item_dict['status']} - {item_dict['detail']}")
                
                
                st.markdown("### Accounting Equation Verification")
                for note in financial_data.get("validation_notes", []):
                    if "Mismatch" in note:
                  
                        st.error(note)
                    else:
                        st.success(note)
                summary_text = generate_summary(financial_data)
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
                        <p><b>Debt-to-Equity Ratio:</b> {debt_to_equity}</p>
                    </div>
                    <div class="card">
                        <h3>SARS Compliance Status</h3>
                        <p><b>{sars_checks[0]['item']}:</b> {sars_checks[0]['status']} - {sars_checks[0]['detail']}</p>
                    </div>
                    <div class="card">
                        <h3>Balance Sheet Breakdown</h3>
                        {table_html}
                    </div>
                </body>
                </html>
                """
                st.download_button(
                    label=f"Download Balance Sheet Report for {uploaded_file.name} (HTML)",
                    data=html_report,
                    file_name=f"Balance_Report_{uploaded_file.name}.html",
                    mime="text/html",
                )
                st.markdown("---")
    else:
        st.info("Upload your financial document to begin analysis.")
    

 