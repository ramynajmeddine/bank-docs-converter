FROM python:3.11-slim

# ─── System packages required by pdf2image & Tesseract ─────────────────────────
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    libgl1 \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

# ─── Workdir & project setup ──────────────────────────────────────────────────
WORKDIR /app
COPY . /app

# ─── Install Python dependencies ──────────────────────────────────────────────
RUN pip install --no-cache-dir -r requirements.txt

# ─── Expose port & start server ───────────────────────────────────────────────
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
