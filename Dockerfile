# Use Ubuntu base to get full LibreOffice filters
FROM ubuntu:22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install Python, LibreOffice (with Calc) and dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip libreoffice libreoffice-calc \
    openjdk-17-jre-headless fonts-dejavu poppler-utils \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY main.py /app/main.py

# Expose Render port
ENV PORT=8080
EXPOSE 8080

# Run API
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
