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
        tmp_dir = tempfile.mkdtemp()
        input_path = os.path.join(tmp_dir, pdf.filename)
        output_filename = os.path.splitext(pdf.filename)[0] + f".{format}"
        output_path = os.path.join(tmp_dir, output_filename)

        with open(input_path, "wb") as f:
            f.write(await pdf.read())

        # Try lattice first (for bordered tables)
        tables = camelot.read_pdf(input_path, pages="all", flavor="lattice")

        # Fallback to stream if lattice fails
        if len(tables) == 0:
            tables = camelot.read_pdf(input_path, pages="all", flavor="stream")

        if len(tables) == 0:
            return JSONResponse(status_code=400, content={"error": "No tables detected in PDF."})

        # Merge all tables
        dfs = []
        for t in tables:
            df = t.df
            # Clean up headers and empty columns
            df.columns = [str(c).strip() for c in df.columns]
            df = df.dropna(how="all", axis=1)
            dfs.append(df)

        merged_df = pd.concat(dfs, ignore_index=True)

        # Export to Excel
        merged_df.to_excel(output_path, index=False)

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            return JSONResponse(status_code=500, content={"error": "Excel file generation failed."})

        return FileResponse(
            output_path,
            filename=output_filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
