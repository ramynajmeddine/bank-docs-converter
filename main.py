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
        import pdfplumber
        from pdfminer.high_level import extract_text
        import openpyxl
        import os, tempfile
        from fastapi.responses import FileResponse, JSONResponse

        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, pdf.filename)
        output_path = os.path.join(temp_dir, f"converted.{format}")

        # Save uploaded PDF
        with open(input_path, "wb") as f:
            f.write(await pdf.read())

        workbook = openpyxl.Workbook()
        sheet = workbook.active
        row_index = 1
        extracted = False

        # Try to extract tables first
        with pdfplumber.open(input_path) as pdf_file:
            for page in pdf_file.pages:
                tables = page.extract_tables()
                for table in tables:
                    extracted = True
                    for row in table:
                        for col_index, cell in enumerate(row, start=1):
                            sheet.cell(row=row_index, column=col_index).value = cell
                        row_index += 1
                    row_index += 1

        # Fallback: extract plain text if no tables found
        if not extracted:
            text = extract_text(input_path)
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            for line in lines:
                sheet.append([line])

        workbook.save(output_path)
        return FileResponse(output_path, filename=f"converted.{format}")

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
