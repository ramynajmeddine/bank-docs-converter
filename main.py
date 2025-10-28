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
    try:
        tmp_dir = tempfile.mkdtemp()
        input_path = os.path.join(tmp_dir, pdf.filename)
        output_filename = os.path.splitext(pdf.filename)[0] + f".{format}"
        output_path = os.path.join(tmp_dir, output_filename)

        # Save uploaded file
        with open(input_path, "wb") as f:
            f.write(await pdf.read())

        # Extract text line by line using pdfplumber
        data_rows = []
        with pdfplumber.open(input_path) as pdf_doc:
            for page in pdf_doc.pages:
                lines = page.extract_text().split('\n')
                for line in lines:
                    clean_line = line.strip()
                    if clean_line:
                        data_rows.append([clean_line])

        if not data_rows:
            return JSONResponse(status_code=400, content={"error": "No readable text detected in PDF."})

        # Convert text lines to a DataFrame
        df = pd.DataFrame(data_rows, columns=["Extracted Text"])

        # Save to Excel
        df.to_excel(output_path, index=False)

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            return JSONResponse(status_code=500, content={"error": "Excel file not created properly."})

        return FileResponse(
            output_path,
            filename=output_filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
