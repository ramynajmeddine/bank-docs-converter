import tempfile
import os
import pdfplumber
import openpyxl
from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI()

@app.get("/")
def root():
    return {"status": "OK", "message": "Bank Docs Converter is running"}

@app.post("/convert")
async def convert_pdf(pdf: UploadFile, format: str = Form("xlsx")):
    try:
        # Save uploaded PDF to a temp file
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, pdf.filename)
        with open(input_path, "wb") as f:
            f.write(await pdf.read())

        # Extract tables from PDF using pdfplumber
        output_path = os.path.join(temp_dir, f"converted.{format}")
        workbook = openpyxl.Workbook()
        sheet = workbook.active

        with pdfplumber.open(input_path) as pdf_file:
            row_index = 1
            for page in pdf_file.pages:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        for col_index, cell in enumerate(row, start=1):
                            sheet.cell(row=row_index, column=col_index).value = cell
                        row_index += 1
                    row_index += 1  # add blank line between tables

        workbook.save(output_path)
        return FileResponse(output_path, filename=f"converted.{format}")

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
