# Use Debian Bullseye base with Python 3.11
FROM python:3.11-bullseye

# Install LibreOffice (full) and required dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    libreoffice-calc \
    libreoffice-writer \
    fonts-dejavu \
    openjdk-17-jre-headless \
    poppler-utils \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create app dir
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app code
COPY main.py /app/main.py

# Expose the web port Render expects
ENV PORT=8080
EXPOSE 8080

# Start the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "info"]
