import os
import shutil
import subprocess
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse

app = FastAPI(title="Bank Docs Converter", version="1.0")

# Health check
@app.get("/", response_class=PlainTextResponse)
def root():
    return "OK"

@app.post("/convert")
async def convert(pdf: UploadFile = File(...), format: str = "xlsx"):
    # Accept only PDFs
    if not pdf.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    # Only allow xlsx or csv output
    fmt = format.lower()
    if fmt not in ("xlsx", "csv"):
        raise HTTPException(status_code=400, detail="format must be 'xlsx' or 'csv'")

    # Temporary working dir
    workdir = tempfile.mkdtemp(prefix="convert_")
    try:
        in_path = os.path.join(workdir, pdf.filename)
        with open(in_path, "wb") as f:
            f.write(await pdf.read())

        # Convert with LibreOffice (headless)
        # Note: LibreOffice writes output next to the input file
        cmd = [
            "soffice",
            "--headless",
            "--convert-to", fmt,
            "--outdir", workdir,
            in_path
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Conversion failed: {proc.stderr or proc.stdout}")

        # Determine output filename
        base = os.path.splitext(os.path.basename(in_path))[0]
        out_path = os.path.join(workdir, f"{base}.{fmt}")

        if not os.path.exists(out_path):
            # LibreOffice sometimes uppercases extension; fallback scan
            candidates = [p for p in os.listdir(workdir) if p.startswith(base + ".")]
            if candidates:
                out_path = os.path.join(workdir, candidates[0])
            else:
                raise HTTPException(status_code=500, detail="Converted file not found.")

        # Send file to client (then delete temp dir)
        filename = os.path.basename(out_path)
        return FileResponse(out_path, filename=filename, media_type="application/octet-stream")

    finally:
        # clean up after response is sent
        try:
            shutil.rmtree(workdir, ignore_errors=True)
        except Exception:
            pass
