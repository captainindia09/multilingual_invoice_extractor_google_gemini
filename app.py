import streamlit as st
import pandas as pd
import json
import base64
from io import BytesIO

# Import our modular components
from ocr import extract_text
from extractor import extract_invoice_data
from validator import validate_and_parse
from logger import log_processed_file

st.set_page_config(page_title="Multi-Invoice AI Parser", layout="wide", page_icon="📄")

st.title("📄 Multi-Invoice Extraction Pipeline")
st.markdown("Upload multiple invoice files (PDF, JPG, PNG) and extract structured JSON outputs automatically via Google Gemini.")

uploaded_files = st.file_uploader("Upload Invoices here", type=['pdf', 'jpg', 'jpeg', 'png', 'tiff', 'bmp'], accept_multiple_files=True)

if 'results' not in st.session_state:
    st.session_state.results = []

if st.button("Process Invoices") and uploaded_files:
    st.session_state.results = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_files = len(uploaded_files)
    all_results = []
    
    for i, file in enumerate(uploaded_files):
        status_text.text(f"Processing ({i+1}/{total_files}): {file.name}")
        try:
            # Step 1: Extract Text via OCR/PDF Parsing
            text = extract_text(file, file.name)
            
            # Step 2: Extract Data via LLM (Gemini)
            raw_response = extract_invoice_data(text)
            
            # Step 3: Parse and Validate Output
            parsed_data = None
            try:
                parsed_data = validate_and_parse(raw_response)
            except Exception as valid_err:
                # Retry logic
                status_text.text(f"Retrying ({i+1}/{total_files}): {file.name}")
                raw_response_retry = extract_invoice_data(text)
                parsed_data = validate_and_parse(raw_response_retry)
                
            parsed_data['_filename'] = file.name
            
            # Log success and store results
            all_results.append(parsed_data)
            log_processed_file(file.name, "SUCCESS", extracted_data=parsed_data)
            
        except Exception as e:
            st.error(f"Failed to process {file.name}: {str(e)}")
            # Log failure but continue processing remaining files
            log_processed_file(file.name, "FAILED", error_msg=str(e))
            
        progress_bar.progress((i + 1) / total_files)
        
    st.session_state.results = all_results
    status_text.text("Processing Complete!")
    st.success(f"Successfully processed {len(all_results)} out of {total_files} invoices.")

# Display Dashboard if there are results
if st.session_state.results:
    st.markdown("---")
    st.header("📊 Extraction Dashboard")
    
    results = st.session_state.results
    total_invoices = len(results)
    
    def get_amount(item, key):
        val = item.get(key, 0)
        try: return float(val) if val is not None else 0.0
        except: return 0.0
        
    total_revenue = sum(get_amount(r, 'total_amount') for r in results)
    
    col1, col2 = st.columns(2)
    col1.metric("Total Invoices Extracted", total_invoices)
    col2.metric("Total Revenue ($)", f"${total_revenue:,.2f}")
    
    # Vendor Breakdown
    vendor_revenues = {}
    for r in results:
        vendor = r.get('vendor_name') or "Unknown"
        amount = get_amount(r, 'total_amount')
        vendor_revenues[vendor] = vendor_revenues.get(vendor, 0) + amount
        
    if vendor_revenues:
        st.subheader("Vendor-wise Breakdown")
        df_vendors = pd.DataFrame(list(vendor_revenues.items()), columns=["Vendor", "Total Amount"])
        st.dataframe(df_vendors, use_container_width=True)
        
    st.subheader("Extracted Results")
    # Show individual invoice extractions
    for r in results:
        vendor = r.get('vendor_name', 'Unknown')
        amount = r.get('total_amount', 0)
        with st.expander(f"Invoice: {r['_filename']} | {vendor} | ${amount}"):
            display_dict = {k: v for k, v in r.items() if k != '_filename'}
            st.json(display_dict)
            
    # Export Data Section
    st.markdown("---")
    st.header("📥 Export Data")
    
    col_json, col_csv = st.columns(2)
    
    # Export JSON
    json_data = json.dumps([{k: v for k, v in r.items() if k != '_filename'} for r in results], indent=2)
    col_json.download_button(
        label="Download Results as JSON",
        data=json_data,
        file_name="extracted_invoices.json",
        mime="application/json"
    )
    
    # Export CSV
    csv_data = []
    for r in results:
        # Create base record
        base = {k: v for k, v in r.items() if k not in ['line_items', '_filename']}
        base['uploaded_filename'] = r['_filename']
        
        line_items = r.get('line_items')
        if not line_items:
            csv_data.append(base)
        else:
            for item in line_items:
                record = base.copy()
                if isinstance(item, dict):
                    for k, v in item.items():
                        record[f"item_{k}"] = v
                csv_data.append(record)
                
    if csv_data:
        df_export = pd.DataFrame(csv_data)
        csv_bytes = df_export.to_csv(index=False).encode('utf-8')
        col_csv.download_button(
            label="Download Results as CSV",
            data=csv_bytes,
            file_name="extracted_invoices.csv",
            mime="text/csv"
        )
