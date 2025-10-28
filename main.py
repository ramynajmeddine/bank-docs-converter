import os
import tempfile
import pandas as pd
import camelot
from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI()

@app.get("/")
def root():
    return {"status": "OK", "message": "Bank Docs Converter is live"}

@app.post("/convert")
async def convert(pdf: UploadFile, format: str = "xlsx"):
    try:
        tmp_dir = tempfile.mkdtemp()
        input_path = os.path.join(tmp_dir, "statement.pdf")
        output_path = os.path.join(tmp_dir, f"statement.{format}")

        with open(input_path, "wb") as f:
            f.write(await pdf.read())

        # Extract tables using Camelot
        tables = camelot.read_pdf(input_path, pages="all", flavor="stream")

        if len(tables) == 0:
            return JSONResponse(status_code=400,
                                 content={"error": "No tables detected. Try a clearer PDF scan."})

        # Concatenate all tables
        dfs = [t.df for t in tables]
        df = pd.concat(dfs, ignore_index=True)

        # Save to Excel
        df.to_excel(output_path, index=False)

        return FileResponse(output_path, filename=f"converted.{format}")

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
