# Use a slim image with Python
FROM python:3.11-slim

# Install LibreOffice & utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    fonts-dejavu \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Create app dir
WORKDIR /app

# Copy requirements first (better caching)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app code
COPY main.py /app/main.py

# Expose the web port Railway expects
ENV PORT=8080
EXPOSE 8080

# Start the API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "info"]
