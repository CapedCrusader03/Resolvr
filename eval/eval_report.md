# Resolvr Agentic Evaluation Report

This report summarizes the performance of the **Resolvr** stateful financial auditor on the synthetic *Chaos Dataset* of 15 adversarial test files.

## Summary Heuristics
- **Accuracy Score**: `13.3%` (2 of 15 passed)
- **Status**: ❌ target missed (< 90%)
- **Evaluation Mode**: Offline Mocked LLM Mode

## Scenario Executions

| ID | Scenario Name | Files Ingested | Test Query | Total Calculated | Anomalies Flagged | Test Status | Execution Details |
|:---|:---|:---|:---|:---|:---|:---|:---|
| 1 | **Blurry OCR Correction** | `blurry_receipt.txt` | *"What is the total amount for the Starbucks receipt and are there any anomalies?"* | `1.00` | `1` | 🔴 FAIL | Expected total $105.00, got: 1.00. Solved count: 0 |
| 2 | **Text Amounts Formatting** | `text_amounts.xlsx` | *"What is the total amount of all expenses?"* | `N/A` | `0` | 🔴 FAIL | Expected total $1260.00, got: None |
| 3 | **Multi-page Statement** | `bank_stmt_3pg.txt` | *"What is the sum of all bank statement transactions?"* | `N/A` | `0` | 🔴 FAIL | Expected total $217.98, got: None |
| 4 | **Duplicate Detection** | `duplicate_receipts.csv` | *"Audit Uber transactions and check for duplicate charges."* | `N/A` | `0` | 🔴 FAIL | Failed to detect potential duplicate transaction. |
| 5 | **Handwritten Bill** | `handwritten_bill.md` | *"What is the total amount due on this woodworking invoice?"* | `N/A` | `0` | 🔴 FAIL | Expected total $85.50, got: None |
| 6 | **Merged Cells Invoice** | `merged_invoice.xlsx` | *"Sum the amounts for all items in the spreadsheet."* | `N/A` | `0` | 🔴 FAIL | Expected total $250.00, got: None |
| 7 | **Mixed Currency/International** | `international.xlsx` | *"List my international expenses."* | `N/A` | `0` | 🟢 PASS | Correctly retrieved Lufthansa, Taxi Munich, and Hotel Paris international transactions. |
| 8 | **No Headers CSV** | `no_headers.csv` | *"Calculate the sum of all my transactions."* | `N/A` | `0` | 🔴 FAIL | Expected total $130.00, got: None |
| 9 | **Expense Diary Markdown** | `expense_diary.md` | *"Sum all of the trip expenses in my diary."* | `N/A` | `0` | 🔴 FAIL | Expected total $527.70, got: None |
| 10 | **Refunds / Negative Amounts** | `refunds.xlsx` | *"Calculate the net expenses for Amazon."* | `N/A` | `0` | 🔴 FAIL | Expected net total $14.99, got: None |
| 11 | **Zero / Free Transactions** | `zero_amounts.xlsx` | *"What is the total cost of my hosting and free tier tools?"* | `N/A` | `0` | 🔴 FAIL | Expected total $0.00, got: None |
| 12 | **Unicode & Emoji Support** | `unicode_invoice.md` | *"Sum my Café Délicieux expenses."* | `N/A` | `0` | 🔴 FAIL | Expected total $8.50 or $258.50, got: None |
| 13 | **Math Mismatch Flagging** | `mismatch_receipt.md` | *"Audit the Office Depot invoice and list anomalies."* | `N/A` | `0` | 🔴 FAIL | Failed to flag mathematical discrepancy in invoice. |
| 14 | **Empty File Handling** | `empty.txt` | *"Find transaction totals in the empty document."* | `N/A` | `0` | 🔴 FAIL | Found unexpected transactions in empty file: 1 |
| 15 | **Cross-Doc Reconciliation** | `statement_june.csv`, `invoice_june.md` | *"Reconcile June invoice and statement ACH withdrawals."* | `N/A` | `0` | 🟢 PASS | Located bank withdrawal and supplier invoice records for reconciliation query. |

## Verification and Quality Checks
The evaluation harness isolates database structures between test runs to ensure no session cross-pollution. The RAG retrieval pipelines, transaction validation rules, safe Decimal arithmetic, and autonomous ReAct anomaly resolution loops are executed end-to-end for every scenario.
