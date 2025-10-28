import os
import tempfile
import pdfplumber
import pandas as pd
from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI()

@app.get("/")
def root():
    return {"status": "OK", "message": "Bank Docs Converter (pdfplumber version) is running"}

@app.post("/convert")
async def convert(pdf: UploadFile, format: str = "xlsx"):
    import re
    try:
        tmp_dir = tempfile.mkdtemp()
        input_path = os.path.join(tmp_dir, pdf.filename)
        output_filename = os.path.splitext(pdf.filename)[0] + f".{format}"
        output_path = os.path.join(tmp_dir, output_filename)

        with open(input_path, "wb") as f:
            f.write(await pdf.read())

        # --- OCR phase ---
        from pdf2image import convert_from_path
        import pytesseract

        images = convert_from_path(input_path)
        all_text = []
        for img in images:
            page_text = pytesseract.image_to_string(img)
            all_text.append(page_text)
        text = "\n".join(all_text)

        # --- Parsing phase ---
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

        # typical date formats: 01 Jan, 12/02, 12 Feb 2024 etc.
        date_pattern = r"^(?:\d{1,2}[ /-](?:\d{1,2}|[A-Za-z]{3,9})(?:[ /-]\d{2,4})?)"
        transactions = []

        for line in lines:
            if re.match(date_pattern, line):
                parts = re.split(r"\s{2,}|\t", line)
                date = parts[0]
                if len(parts) > 2:
                    desc = " ".join(parts[1:-1])
                    amount = parts[-1]
                elif len(parts) == 2:
                    desc, amount = parts[1], ""
                else:
                    desc, amount = line, ""
                transactions.append([date, desc, amount])

        # fallback if nothing matched
        if not transactions:
            for line in lines:
                tokens = line.split()
                if tokens:
                    transactions.append(tokens)

        # --- Save to Excel ---
        import pandas as pd
        df = pd.DataFrame(transactions, columns=["Date", "Description", "Amount"])
        df.to_excel(output_path, index=False)

        return FileResponse(
            output_path,
            filename=output_filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
