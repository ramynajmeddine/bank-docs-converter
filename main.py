import os
import re
import tempfile
from typing import List, Dict

import pdfplumber
import pandas as pd
from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI()

AMOUNT_RE = re.compile(r"^-?\$?\s*\d{1,3}(?:,\d{3})*\.\d{2}$")

def clean_amount(x: str | None) -> float | None:
    if not x:
        return None
    x = x.replace("$", "").replace(",", "").strip()
    try:
        return float(x)
    except Exception:
        return None

def extract_page_rows(page: pdfplumber.page.Page) -> List[Dict]:
    """
    Try table extraction via lines first; if that fails, fallback to regex line parsing.
    """
    rows: List[Dict] = []

    # 1) Try table extraction (most reliable if page has ruling lines)
    try:
        tables = page.extract_tables(
            table_settings={
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "intersection_x_tolerance": 5,
                "intersection_y_tolerance": 5,
                "snap_tolerance": 5,
                "min_words_vertical": 2,
                "min_words_horizontal": 2,
                "keep_blank_chars": False,
                "text_x_tolerance": 2,
                "text_y_tolerance": 2,
            }
        )
    except Exception:
        tables = []

    def normalize_and_add(row: List[str]):
        # We expect 5 columns. Some pages include a small header above—we skip non-data rows.
        if not row or len(row) < 3:
            return
        cells = [ (c or "").strip() for c in row ]
        # pad to 5 cols
        while len(cells) < 5:
            cells.append("")
        date, details, wd, dep, bal = cells[:5]

        # Basic sanity: date should look like "22 JAN" or "03 MAR" or "2025" OPENING BALANCE row etc.
        date_ok = bool(re.match(r"^\d{2}\s+[A-Z]{3}$", date)) or "OPENING BALANCE" in (details.upper() or "") or "CREDIT INTEREST" in details.upper()
        # Some PDFs place Date+Details in col0 and shift amounts right; keep permissive but require any amount at end.
        amountish = AMOUNT_RE.match(wd) or AMOUNT_RE.match(dep) or AMOUNT_RE.match(bal)
        if not (date_ok or amountish):
            return

        rows.append({
            "Date": date,
            "Details": details,
            "Withdrawals": clean_amount(wd),
            "Deposits": clean_amount(dep),
            "Balance": clean_amount(bal),
        })

    # Consume any tables found
    for t in tables:
        for r in t:
            # Skip header rows (look for the known header labels)
            joined = " ".join([ (c or "").strip().lower() for c in r ])
            if ("withdrawals" in joined and "deposits" in joined and "balance" in joined) or joined.startswith("date transaction details"):
                continue
            normalize_and_add(r)

    if rows:
        return rows

    # 2) Fallback: regex parse line-by-line text when lines aren’t detected
    text = page.extract_text() or ""
    for line in text.splitlines():
        L = line.strip()
        # We’ll catch lines whose tail contains 2 or 3 amounts and a details blob near the front.
        # Pattern: DATE  DETAILS ....  [Withdrawals]  [Deposits]  Balance
        m = re.match(
            r"^(?P<date>\d{2}\s+[A-Z]{3})\s+(?P<details>.*?)\s+(?P<a1>-?\$?\s*\d[\d,]*\.\d{2})\s+(?P<a2>-?\$?\s*\d[\d,]*\.\d{2})(?:\s+(?P<a3>-?\$?\s*\d[\d,]*\.\d{2}))?$",
            L
        )
        if not m:
            continue

        date = m.group("date")
        details = m.group("details")
        a1 = m.group("a1")
        a2 = m.group("a2")
        a3 = m.group("a3")

        # Heuristic: last amount is always the Balance.
        if a3:
            wd, dep, bal = a1, a2, a3
        else:
            # Some lines omit one of wd/dep; try to infer by presence of minus or context.
            # If there are two amounts, the second is Balance; the first could be either wd or dep.
            bal = a2
            # If it starts with a minus OR details looks like a debit keyword, treat as Withdrawal
            if a1.strip().startswith("-"):
                wd, dep = a1, ""
            else:
                # If details contains things like PAYMENT/EFTPOS/ATM, tend to be Withdrawal
                if re.search(r"(payment|eftpos|atm|fee|purchase|debit)", details, re.I):
                    wd, dep = a1, ""
                else:
                    dep, wd = a1, ""

        rows.append({
            "Date": date,
            "Details": details,
            "Withdrawals": clean_amount(wd),
            "Deposits": clean_amount(dep),
            "Balance": clean_amount(bal),
        })

    return rows

@app.get("/")
def root():
    return {"status": "OK", "message": "Bank Docs Converter is running"}

@app.post("/convert")
async def convert(pdf: UploadFile = File(...), format: str = Query("xlsx")):
    # Only xlsx output for this path
    if format.lower() != "xlsx":
        return JSONResponse(status_code=422, content={"error": "Only xlsx is supported for this endpoint."})

    # Save uploaded PDF
    with tempfile.TemporaryDirectory() as tmp:
        in_path = os.path.join(tmp, "statement.pdf")
        out_path = os.path.join(tmp, "statement.xlsx")
        with open(in_path, "wb") as f:
            f.write(await pdf.read())

        # Parse with pdfplumber
        all_rows: List[Dict] = []
        try:
            with pdfplumber.open(in_path) as pdfdoc:
                for i, page in enumerate(pdfdoc.pages, start=1):
                    # Skip obvious cover/summary pages by checking for the table header
                    page_text = (page.extract_text() or "").lower()
                    if "transaction details" not in page_text and "withdrawals" not in page_text:
                        continue
                    rows = extract_page_rows(page)
                    all_rows.extend(rows)
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": "Failed to read PDF", "detail": str(e)})

        if not all_rows:
            return JSONResponse(status_code=500, content={"error": "No rows detected. Check the PDF layout or send another sample."})

        # Build DataFrame and save
        df = pd.DataFrame(all_rows, columns=["Date", "Details", "Withdrawals", "Deposits", "Balance"])
        # Clean: if both wd/dep are None, drop the row; also forward-fill balances if needed
        df = df.dropna(how="all", subset=["Withdrawals", "Deposits", "Balance"])

        with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Transactions")

        return FileResponse(out_path, filename="statement.xlsx")
