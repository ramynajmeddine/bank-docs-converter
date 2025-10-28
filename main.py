import pdfplumber
import pandas as pd
import tempfile
from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse, JSONResponse
import os

app = FastAPI()

@app.get("/")
def root():
    return {"status": "OK", "message": "Bank Docs Converter is running"}

@app.post("/convert")
async def convert(pdf: UploadFile, format: str = "xlsx"):
    try:
        # Temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "statement.pdf")
            output_path = os.path.join(tmpdir, f"statement.{format}")

            # Save uploaded file
            with open(input_path, "wb") as f:
                f.write(await pdf.read())

            # Extract text from PDF
            text_data = []
            with pdfplumber.open(input_path) as pdf_doc:
                for i, page in enumerate(pdf_doc.pages):
                    text = page.extract_text()
                    if text:
                        lines = text.split("\n")
                        for line in lines:
                            text_data.append([i + 1, line])

            # If no text found
            if not text_data:
                return JSONResponse(status_code=500, content={"error": "No text extracted from PDF"})

            # Convert to DataFrame and save Excel
            df = pd.DataFrame(text_data, columns=["Page", "Text"])
            df.to_excel(output_path, index=False)

            if not os.path.exists(output_path):
                raise RuntimeError(f"Output file not found at {output_path}")

            return FileResponse(output_path, filename=f"converted.{format}")

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
