# Use a slim Python image
FROM python:3.11-slim

# Install LibreOffice, Unoconv, and fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    fonts-dejavu \
    poppler-utils \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependencies first (for Docker cache efficiency)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY main.py /app/main.py

# Ensure /tmp exists and is writable (Render uses ephemeral FS)
RUN mkdir -p /tmp && chmod -R 777 /tmp

# Set environment variables
ENV PORT=8080
EXPOSE 8080

# Run FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "info"]

