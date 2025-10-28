from fastapi import FastAPI, File, UploadFile, Query
from fastapi.responses import FileResponse, JSONResponse
import pdfplumber
import pandas as pd
import os
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

app = FastAPI()

@app.get("/")
def root():
    return {"message": "PDF to Excel Converter API is running successfully."}


@app.post("/convert")
async def convert_pdf_to_excel(
    pdf: UploadFile = File(...),
    format: str = Query("xlsx", enum=["xlsx"])
):
    try:
        # Save uploaded PDF
        input_path = f"/app/temp_{pdf.filename}"
        output_path = input_path.replace(".pdf", f".{format}")

        with open(input_path, "wb") as f:
            f.write(await pdf.read())

        extracted_text = []

        # Try reading as text-based PDF first
        try:
            with pdfplumber.open(input_path) as pdf_doc:
                for i, page in enumerate(pdf_doc.pages, start=1):
                    text = page.extract_text()
                    if text:
                        extracted_text.append({"page": i, "text": text.strip()})
        except Exception as e:
            print(f"pdfplumber failed: {e}")

        # If no text found, fallback to OCR
        if not extracted_text:
            images = convert_from_path(input_path)
            for i, img in enumerate(images, start=1):
                text = pytesseract.image_to_string(img)
                extracted_text.append({"page": i, "text": text.strip()})

        # Create a DataFrame
        df = pd.DataFrame(extracted_text)

        # Write to Excel safely
        df.to_excel(output_path, index=False, engine='openpyxl')

        # Close all file handles before returning
        del df

        # Double-check file exists and has size
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise Exception("Output Excel file was not created correctly.")

        # Return as a downloadable response
        return FileResponse(
            path=output_path,
            filename=os.path.basename(output_path),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

