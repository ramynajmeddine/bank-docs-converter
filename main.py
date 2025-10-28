from fastapi import FastAPI, File, UploadFile, Query
from fastapi.responses import Response
import pdfplumber
import pandas as pd
import os
from pdf2image import convert_from_path
import pytesseract
from io import BytesIO

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
        # Save uploaded PDF temporarily
        input_path = f"/app/temp_{pdf.filename}"
        with open(input_path, "wb") as f:
            f.write(await pdf.read())

        extracted_text = []

        # Try text-based extraction
        try:
            with pdfplumber.open(input_path) as pdf_doc:
                for i, page in enumerate(pdf_doc.pages, start=1):
                    text = page.extract_text()
                    if text:
                        extracted_text.append({"page": i, "text": text.strip()})
        except Exception as e:
            print(f"pdfplumber failed: {e}")

        # Fallback to OCR if no text
        if not extracted_text:
            images = convert_from_path(input_path)
            for i, img in enumerate(images, start=1):
                text = pytesseract.image_to_string(img)
                extracted_text.append({"page": i, "text": text.strip()})

        # Create a DataFrame
        df = pd.DataFrame(extracted_text)

        # Write Excel to memory (not disk)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='ExtractedText')
        output.seek(0)

        # Clean up temp file
        os.remove(input_path)

        # Return proper binary Excel response
        headers = {
            'Content-Disposition': f'attachment; filename="{pdf.filename.replace(".pdf", ".xlsx")}"'
        }
        return Response(
            content=output.read(),
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers=headers
        )

    except Exception as e:
        return {"error": str(e)}
