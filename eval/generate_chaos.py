import os
import csv
import pandas as pd
from pathlib import Path

# Paths
EVAL_DIR = Path(__file__).parent.resolve()
DATASET_DIR = EVAL_DIR / "chaos_dataset"
EXPECTED_DIR = EVAL_DIR / "expected_outputs"

# Ensure directories exist
DATASET_DIR.mkdir(parents=True, exist_ok=True)
EXPECTED_DIR.mkdir(parents=True, exist_ok=True)

def generate_blurry_receipt():
    # Scenario 1: OCR blurry receipt with raw text misreading total "1O5.OO" instead of 105.00
    content = """Starbucks Coffee Shop
Date: 2025-06-10
Items:
- Cafe Latte: $50.00
- Blueberry Muffin: $30.00
- Avocado Toast: $25.00
---------------------
Total: $1O5.OO
"""
    with open(DATASET_DIR / "blurry_receipt.txt", "w", encoding="utf-8") as f:
        f.write(content)

def generate_text_amounts():
    # Scenario 2: Excel sheet with text-formatted amounts (like "$1,234.56") and extra spaces
    data = {
        "Merchant": ["AWS", "GitHub", "Vercel"],
        "Date": ["2025-07-01", "2025-07-02", "2025-07-03"],
        "Amount": [" $1,200.00 ", " $40.00 ", " $20.00 "]
    }
    df = pd.DataFrame(data)
    df.to_excel(DATASET_DIR / "text_amounts.xlsx", index=False)

def generate_bank_statement_3pg():
    # Scenario 3: Bank statement text file spanning multiple pages
    content = """--- Page 1 ---
ACME National Bank - Statement Q2 2025
Account: XXXX-XXXX-1234
Date: 2025-04-15
Transaction: Adobe Systems - $52.99

--- Page 2 ---
ACME National Bank - Statement Q2 2025
Date: 2025-05-15
Transaction: Zoom Video Communications - $14.99

--- Page 3 ---
ACME National Bank - Statement Q2 2025
Date: 2025-06-15
Transaction: Slack Technologies - $150.00
"""
    with open(DATASET_DIR / "bank_stmt_3pg.txt", "w", encoding="utf-8") as f:
        f.write(content)

def generate_duplicate_receipts():
    # Scenario 4: CSV containing duplicate receipts within a 2-minute window
    with open(DATASET_DIR / "duplicate_receipts.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Merchant", "Amount"])
        writer.writerow(["2025-06-12 14:30:00", "Uber Technologies", "18.50"])
        writer.writerow(["2025-06-12 14:31:00", "Uber Technologies", "18.50"])  # Duplicate
        writer.writerow(["2025-06-12 15:45:00", "Shell Oil", "45.00"])

def generate_handwritten_bill():
    # Scenario 5: Freeform handwriting style text document with word-based amounts
    content = """Handwritten Invoice #9982
Date: June 15, 2025
To: Resolvr Project
From: Custom Woodwork Shop
Items:
Consulting work: fifty dollars
Materials: thirty-five dollars and fifty cents
Total Due: eighty-five dollars and fifty cents ($85.50)
Please pay within 30 days.
"""
    with open(DATASET_DIR / "handwritten_bill.md", "w", encoding="utf-8") as f:
        f.write(content)

def generate_merged_invoice():
    # Scenario 6: Excel sheet with merged cells that breaks standard row-by-row parsing
    # We will construct a DataFrame with NaN values representing merged cells
    data = {
        "Invoice": ["INV-100", None, "INV-101", None],
        "Date": ["2025-06-01", None, "2025-06-02", None],
        "Merchant": ["Google Cloud", None, "OpenAI API", None],
        "Item": ["Compute Engine", "Cloud SQL", "GPT-4 usage", "Embeddings API"],
        "Amount": [120.00, 30.00, 85.00, 15.00]
    }
    df = pd.DataFrame(data)
    df.to_excel(DATASET_DIR / "merged_invoice.xlsx", index=False)

def generate_international():
    # Scenario 7: Mixed currencies in one spreadsheet
    data = {
        "Vendor": ["Lufthansa", "Taxi Munich", "Hotel Paris"],
        "Date": ["2025-06-05", "2025-06-06", "2025-06-07"],
        "Amount": ["450.00 EUR", "25.50 EUR", "120.00 USD"]
    }
    df = pd.DataFrame(data)
    df.to_excel(DATASET_DIR / "international.xlsx", index=False)

def generate_no_headers():
    # Scenario 8: CSV file without a header row
    with open(DATASET_DIR / "no_headers.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["2025-06-08", "Stripe Inc", "15.00"])
        writer.writerow(["2025-06-09", "Figma", "45.00"])
        writer.writerow(["2025-06-10", "Postgres Hosting", "70.00"])

def generate_expense_diary():
    # Scenario 9: Freeform diary markdown text
    content = """# My Business Trip Expense Diary (June 2025)

## June 12, 2025
Arrived in San Francisco. Took a Uber ride to the hotel. It cost me exactly $45.20. 
Later that evening, had a welcome business dinner at Fisherman's Wharf. 
The restaurant bill came out to $120.00 including tips.

## June 13, 2025
Had a quick breakfast at Starbucks for $12.50.
Purchased conference ticket for $350.00.
"""
    with open(DATASET_DIR / "expense_diary.md", "w", encoding="utf-8") as f:
        f.write(content)

def generate_refunds():
    # Scenario 10: Refunds as negative values in Excel
    data = {
        "Merchant": ["Amazon Prime", "Amazon Books", "Amazon Refund"],
        "Date": ["2025-06-20", "2025-06-21", "2025-06-22"],
        "Amount": [14.99, 45.50, -45.50]  # Negative amount to subtract
    }
    df = pd.DataFrame(data)
    df.to_excel(DATASET_DIR / "refunds.xlsx", index=False)

def generate_zero_amounts():
    # Scenario 11: Spreadsheet with $0.00 transactions or free items
    data = {
        "Merchant": ["Vite Starter", "GitHub Free Tier", "Vercel Hobby Plan"],
        "Date": ["2025-06-01", "2025-06-01", "2025-06-01"],
        "Amount": [0.00, 0.00, 0.00]
    }
    df = pd.DataFrame(data)
    df.to_excel(DATASET_DIR / "zero_amounts.xlsx", index=False)

def generate_unicode_invoice():
    # Scenario 12: Unicode and special characters in merchant/vendor names
    content = """Café Délicieux ☕
Date: 2025-06-18
Croissant & Coffee: €8.50
Méridien Hotel: $250.00
Total Paid: $250.00
"""
    with open(DATASET_DIR / "unicode_invoice.md", "w", encoding="utf-8") as f:
        f.write(content)

def generate_mismatch_receipt():
    # Scenario 13: Stated total mismatching line items sum (anomaly detector test)
    content = """Office Depot Store #883
Date: 2025-06-14
Items:
- Printer Paper: $20.00
- Ink Cartridges: $100.00
---------------------
Total Stated: $150.00
"""
    with open(DATASET_DIR / "mismatch_receipt.md", "w", encoding="utf-8") as f:
        f.write(content)

def generate_empty():
    # Scenario 14: Empty document
    content = ""
    with open(DATASET_DIR / "empty.txt", "w", encoding="utf-8") as f:
        f.write(content)

def generate_cross_doc_reconcile():
    # Scenario 15: Cross-document reconciliation (Statement + Invoice)
    # Bank Statement
    with open(DATASET_DIR / "statement_june.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Description", "Amount"])
        writer.writerow(["2025-06-12", "ACH Withdrawal - Vendor 102", "1250.00"])
        writer.writerow(["2025-06-15", "POS - Gas Station", "35.00"])
    
    # Invoice
    invoice_content = """INVOICE #102
Vendor: Custom Consulting LLC
Date: 2025-06-10
Hours: 10 hrs @ $125/hr
Total Amount: $1250.00
Reconciliation Code: CC-102-ACH
"""
    with open(DATASET_DIR / "invoice_june.md", "w", encoding="utf-8") as f:
        f.write(invoice_content)

def main():
    print("Generating synthetic chaos dataset...")
    generate_blurry_receipt()
    generate_text_amounts()
    generate_bank_statement_3pg()
    generate_duplicate_receipts()
    generate_handwritten_bill()
    generate_merged_invoice()
    generate_international()
    generate_no_headers()
    generate_expense_diary()
    generate_refunds()
    generate_zero_amounts()
    generate_unicode_invoice()
    generate_mismatch_receipt()
    generate_empty()
    generate_cross_doc_reconcile()
    print("Chaos dataset generated successfully in eval/chaos_dataset/.")

if __name__ == "__main__":
    main()
