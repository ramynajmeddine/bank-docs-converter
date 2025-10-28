# Clean final Dockerfile for Bank Docs Converter
FROM python:3.11-slim

# Install lightweight dependencies used by pdfplumber
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python requirements
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code
COPY main.py /app/main.py

# Environment setup
ENV PORT=8080
EXPOSE 8080

# Run the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
