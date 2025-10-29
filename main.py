from fastapi import FastAPI, File, UploadFile, Response
import pandas as pd
from io import BytesIO
import os
from pdf2image import convert_from_path
import pytesseract
import tempfile

app = FastAPI()

@app.post("/convert")
async def convert_pdf_to_excel(pdf: UploadFile = File(...)):
    try:
        # Save uploaded PDF
        input_path = f"/app/temp_{pdf.filename}"
        with open(input_path, "wb") as f:
            f.write(await pdf.read())

        # Convert pages to images
        images = convert_from_path(input_path)

        data = []
        for i, img in enumerate(images, start=1):
            text = pytesseract.image_to_string(img)
            data.append({"Page": i, "Text": text.strip()})

        df = pd.DataFrame(data)

        # Write to Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='ExtractedText')
        output.seek(0)

        os.remove(input_path)

        headers = {'Content-Disposition': f'attachment; filename="{pdf.filename.replace('.pdf', '.xlsx')}"'}
        return Response(
            content=output.read(),
