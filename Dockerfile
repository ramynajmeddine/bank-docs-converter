FROM python:3.11-slim

# ─── Install system packages required for pdf2image and Tesseract ─────────────
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    libgl1 \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

# ─── Set working directory ────────────────────────────────────────────────────
WORKDIR /app
COPY . /app

# ─── Install Python dependencies ─────────────────────────────────────────────
RUN apt-get update && apt-get install -y \
    poppler-utils \
    poppler-data \
    tesseract-ocr \
    libpoppler-cpp-dev \
    libgl1 \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

# ─── Expose port and start FastAPI app ───────────────────────────────────────
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

