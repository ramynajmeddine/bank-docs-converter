import camelot
import pandas as pd
from io import BytesIO
from fastapi import FastAPI, File, UploadFile, Response

app = FastAPI()

@app.post("/convert")
async def convert_pdf_to_excel(pdf: UploadFile = File(...)):
    input_path = f"/app/temp_{pdf.filename}"
    with open(input_path, "wb") as f:
        f.write(await pdf.read())

    # Detect tables
    tables = camelot.read_pdf(input_path, pages="all")

    # Combine all tables into one Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for i, table in enumerate(tables):
            table.df.to_excel(writer, index=False, sheet_name=f"Page_{i+1}")
    output.seek(0)

    return Response(
        content=output.read(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={'Content-Disposition': f'attachment; filename="{pdf.filename.replace(".pdf", ".xlsx")}"'}
    )
