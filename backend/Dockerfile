FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including LibreOffice for PDF conversion
RUN apt-get update && apt-get install -y \
    libreoffice \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose port 8000
EXPOSE 8000

# DEBUG MODE: List files and sleep to inspect logs
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
