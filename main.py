import os
import tempfile
import subprocess
from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI()

@app.get("/")
def root():
    return {"status": "OK", "message": "Bank Docs Converter is running"}

@app.post("/convert")
async def convert(pdf: UploadFile, format: str = "xlsx"):
    try:
        # Create a temporary working directory
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, "statement.pdf")
        output_path = os.path.join(temp_dir, f"statement.{format}")

        # Save uploaded PDF
        with open(input_path, "wb") as f:
            f.write(await pdf.read())

        # Check if LibreOffice is available
        if os.system("which libreoffice") != 0:
            return JSONResponse(status_code=500, content={"error": "LibreOffice not found"})

        # Convert PDF using LibreOffice
        command = [
            "libreoffice",
            "--headless",
            "--convert-to", format,
            "--outdir", temp_dir,
            input_path
        ]

        process = subprocess.run(command, capture_output=True, text=True)

        if process.returncode != 0:
            return JSONResponse(status_code=500, content={
                "error": "Conversion failed",
                "details": process.stderr
            })

        # Check output file actually exists
        if not os.path.exists(output_path):
            return JSONResponse(status_code=500, content={"error": "Converted file not found"})

        # Return converted file
        return FileResponse(output_path, filename=f"converted.{format}")

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
