from fastapi import FastAPI, File, UploadFile, Response
import pandas as pd
from io import BytesIO
import os
from pdf2image import convert_from_path
import pytesseract

app = FastAPI()

@app.get("/")
def root():
    return {"message": "PDF to Excel Converter API is running successfully."}

@app.post("/convert")
async def convert_pdf_to_excel(pdf: UploadFile = File(...)):
    try:
        # Save uploaded PDF
        input_path = f"/app/temp_{pdf.filename}"
        with open(input_path, "wb") as f:
            f.write(await pdf.read())

        # Convert pages of PDF into images
        images = convert_from_path(input_path)

        # Extract text from each page using OCR (Tesseract)
        data = []
        for i, img in enumerate(images, start=1):
            text = pytesseract.image_to_string(img)
            data.append({"Page": i, "Text": text.strip()})

        # Create a DataFrame
        df = pd.DataFrame(data)

        # Write the extracted text to an Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="ExtractedText")
        output.seek(0)

        # Clean up temporary PDF
        os.remove(input_path)

        # Prepare downloadable Excel response
        headers = {
            "Content-Disposition": f"attachment; filename=\"{pdf.filename.replace('.pdf', '.xlsx')}\""
        }

        return Response(
            content=output.read(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers
        )

    except Exception as e:
        return {"error": str(e)}
