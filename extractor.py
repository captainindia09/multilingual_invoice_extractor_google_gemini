import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables (like GEMINI_API_KEY)
load_dotenv()

# Configure API Key
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

PROMPT = """
You are a highly accurate financial document parser.

Extract the following fields from the invoice text:

* invoice_number
* invoice_date
* vendor_name
* customer_name
* total_amount
* tax_amount
* line_items (list of items with name, quantity, price)

Output format (strict JSON only):

{
"invoice_number": "",
"invoice_date": "",
"vendor_name": "",
"customer_name": "",
"total_amount": 0,
"tax_amount": 0,
"line_items": [
{
"item_name": "",
"quantity": 0,
"price": 0
}
]
}

Rules:

* Return ONLY JSON
* Do not hallucinate
* If a field is missing → return null
* Remove currency symbols (₹, $, etc.)
* Convert all amounts to numeric values
* Normalize date to YYYY-MM-DD
* Vendor = issuer, Customer = billed party
* Extract line items accurately from table-like structures

Invoice Text:
"""

def extract_invoice_data(text: str) -> str:
    """
    Sends the extracted OCR text to Google Gemini (gemini-pro) 
    and returns its JSON response.
    """
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is missing.")
        
    model = genai.GenerativeModel('gemini-pro')
    full_prompt = PROMPT + f"\n\n{text}"
    
    response = model.generate_content(full_prompt)
    return response.text
