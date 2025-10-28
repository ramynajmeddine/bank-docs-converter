from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse, JSONResponse
import tempfile
import subprocess
import os
from pathlib import Path

app = FastAPI()

@app.get("/")
def root():
    return {"status": "OK", "message": "Bank Docs Converter is running"}

@app.post("/convert")
async def convert(pdf: UploadFile, format: str = "xlsx"):
    # Create a temporary working directory
    temp_dir = Path(tempfile.mkdtemp())
    input_path = temp_dir / "statement.pdf"

    # Save uploaded PDF file
    with open(input_path, "wb") as f:
        f.write(await pdf.read())

    # Check if LibreOffice exists
    if os.system("which libreoffice") != 0:
        return JSONResponse(
            status_code=500,
            content={"error": "LibreOffice not found on system"}
        )

    # Convert the PDF using LibreOffice
    output_dir = "/app"
    command = [
        "libreoffice",
        "--headless",
        "--convert-to", format,
        "--outdir", output_dir,
        str(input_path)
    ]

    process = subprocess.run(command, capture_output=True, text=True)

    if process.returncode != 0:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Conversion failed",
                "details": process.stderr
            }
        )

    # Determine converted file path inside /app
    converted_filename = f"{Path(input_path).stem}.{format}"
    converted_path = Path(output_dir) / converted_filename

    if not converted_path.exists():
        return JSONResponse(
            status_code=500,
            content={"error": "Converted file not found"}
        )

    # Return the converted file
    return FileResponse(converted_path, filename=f"converted.{format}")
