# main.py

import os
import tempfile
from pathlib import Path
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse

app = FastAPI()


@app.get("/")
def root():
    return {"status": "OK", "message": "Bank Docs Converter is running"}


@app.post("/convert")
async def convert(pdf: UploadFile = File(...), format: str = "xlsx"):
    """
    Upload a PDF bank statement and convert it to XLSX or CSV.
    """

    # Create a temporary working directory
    temp_dir = Path(tempfile.mkdtemp())
    input_path = temp_dir / "statement.pdf"
    output_path = temp_dir / f"statement.{format}"

    # Save uploaded PDF file
    with open(input_path, "wb") as f:
        f.write(await pdf.read())

    # Run LibreOffice to convert the file
    command = f"libreoffice --headless --convert-to {format} {input_path} --outdir {temp_dir}"
    exit_code = os.system(command)

    if exit_code != 0 or not output_path.exists():
        return {"error": "Conversion failed. Please check your PDF file."}

    # Send converted file back to the user
    return FileResponse(output_path, filename=f"converted.{format}")
