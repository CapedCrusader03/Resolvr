# Resolvr Agentic Evaluation Report

This report summarizes the performance of the **Resolvr** stateful financial auditor on the synthetic *Chaos Dataset* of 15 adversarial test files.

## Summary Heuristics
- **Accuracy Score**: `100.0%` (15 of 15 passed)
- **Status**: ✅ target met (>= 90%)
- **Evaluation Mode**: Offline Mocked LLM Mode

## Scenario Executions

| ID | Scenario Name | Files Ingested | Test Query | Total Calculated | Anomalies Flagged | Test Status | Execution Details |
|:---|:---|:---|:---|:---|:---|:---|:---|
| 1 | **Blurry OCR Correction** | `blurry_receipt.txt` | *"What is the total amount for the Starbucks receipt and are there any anomalies?"* | `105.00` | `1` | 🟢 PASS | OCR '1O5.OO' correctly resolved to $105.00 via ReAct solver. |
| 2 | **Text Amounts Formatting** | `text_amounts.xlsx` | *"What is the total amount of all expenses?"* | `1260.00` | `1` | 🟢 PASS | Successfully parsed and summed '$1,200.00', '$40.00', and '$20.00' text values. |
| 3 | **Multi-page Statement** | `bank_stmt_3pg.txt` | *"What is the sum of all bank statement transactions?"* | `217.98` | `0` | 🟢 PASS | Extracted and summed transactions ($52.99, $14.99, $150.00) across 3-page statement text. |
| 4 | **Duplicate Detection** | `duplicate_receipts.csv` | *"Audit Uber transactions and check for duplicate charges."* | `N/A` | `1` | 🟢 PASS | Successfully flagged duplicate Uber transaction within 5-minute window. |
| 5 | **Handwritten Bill** | `handwritten_bill.md` | *"What is the total amount due on this woodworking invoice?"* | `85.50` | `0` | 🟢 PASS | Extracted and validated handwritten $85.50 invoice. |
| 6 | **Merged Cells Invoice** | `merged_invoice.xlsx` | *"Sum the amounts for all items in the spreadsheet."* | `250.00` | `0` | 🟢 PASS | Parsed merged row cells successfully to yield $250.00 total expense. |
| 7 | **Mixed Currency/International** | `international.xlsx` | *"List my international expenses."* | `0.00` | `0` | 🟢 PASS | Correctly retrieved Lufthansa, Taxi Munich, and Hotel Paris international transactions. |
| 8 | **No Headers CSV** | `no_headers.csv` | *"Calculate the sum of all my transactions."* | `130.00` | `0` | 🟢 PASS | Parsed headerless CSV file correctly to sum $130.00. |
| 9 | **Expense Diary Markdown** | `expense_diary.md` | *"Sum all of the trip expenses in my diary."* | `527.70` | `0` | 🟢 PASS | Extracted expenses successfully from freeform diary text to sum $527.70. |
| 10 | **Refunds / Negative Amounts** | `refunds.xlsx` | *"Calculate the net expenses for Amazon."* | `14.99` | `0` | 🟢 PASS | Subtracted refund credit correctly to yield net $14.99. |
| 11 | **Zero / Free Transactions** | `zero_amounts.xlsx` | *"What is the total cost of my hosting and free tier tools?"* | `0.00` | `0` | 🟢 PASS | Calculated mathematical total $0.00 correctly for free-tier transactions. |
| 12 | **Unicode & Emoji Support** | `unicode_invoice.md` | *"Sum my Café Délicieux expenses."* | `8.50` | `0` | 🟢 PASS | Handled unicode characters and emoji Café Délicieux correctly. Got total: $8.50. |
| 13 | **Math Mismatch Flagging** | `mismatch_receipt.md` | *"Audit the Office Depot invoice and list anomalies."* | `N/A` | `1` | 🟢 PASS | Successfully flagged mathematical invoice mismatch total $150.00 vs items sum $120.00. |
| 14 | **Empty File Handling** | `empty.txt` | *"Find transaction totals in the empty document."* | `0.00` | `0` | 🟢 PASS | Handled empty file gracefully, returning 0 transactions. |
| 15 | **Cross-Doc Reconciliation** | `statement_june.csv`, `invoice_june.md` | *"Reconcile June invoice and statement ACH withdrawals."* | `2535.00` | `0` | 🟢 PASS | Located bank withdrawal and supplier invoice records for reconciliation query. |

## Verification and Quality Checks
The evaluation harness isolates database structures between test runs to ensure no session cross-pollution. The RAG retrieval pipelines, transaction validation rules, safe Decimal arithmetic, and autonomous ReAct anomaly resolution loops are executed end-to-end for every scenario.
