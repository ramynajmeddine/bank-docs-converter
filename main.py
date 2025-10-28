import os
import tempfile
import pandas as pd
import camelot
from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI()

@app.get("/")
def root():
    return {"status": "OK", "message": "Bank Docs Converter is running"}

@app.post("/convert")
async def convert(pdf: UploadFile, format: str = "xlsx"):
    try:
        # Create a stable temp directory
        tmp_dir = tempfile.mkdtemp()
        input_path = os.path.join(tmp_dir, pdf.filename)
        output_filename = os.path.splitext(pdf.filename)[0] + f".{format}"
        output_path = os.path.join(tmp_dir, output_filename)

        # Save uploaded file
        with open(input_path, "wb") as f:
            f.write(await pdf.read())

        # Parse PDF tables
        tables = camelot.read_pdf(input_path, pages="all", flavor="stream")

        if not tables:
            return JSONResponse(status_code=400, content={"error": "No tables detected. Try a clearer PDF."})

        # Merge tables into one DataFrame
        df = pd.concat([t.df for t in tables], ignore_index=True)

        # Write Excel safely
        df.to_excel(output_path, index=False)

        # Confirm file exists and is valid before returning
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            return JSONResponse(status_code=500, content={"error": "Excel file not generated correctly."})

        # Return the file with correct headers
        return FileResponse(
            output_path,
            filename=output_filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
