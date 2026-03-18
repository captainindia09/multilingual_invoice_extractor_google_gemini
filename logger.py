import json
import os
from datetime import datetime

LOG_FILE = "logs.json"

def log_processed_file(filename, status, extracted_data=None, error_msg=None):
    """
    Logs the outcome of processing an invoice.
    Tracks file name, success/failure, and extracted fields or error message.
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "filename": filename,
        "status": status,
        "extracted_data": extracted_data,
        "error": error_msg
    }
    
    try:
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'w') as f:
                json.dump([log_entry], f, indent=4)
        else:
            # Read existing logs
            with open(LOG_FILE, 'r') as f:
                try:
                    logs = json.load(f)
                except json.JSONDecodeError:
                    logs = []
            
            logs.append(log_entry)
            
            with open(LOG_FILE, 'w') as f:
                json.dump(logs, f, indent=4)
    except Exception as e:
        print(f"Failed to write to log file: {e}")
