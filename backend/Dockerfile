FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose port 8000
EXPOSE 8000

# DEBUG MODE: List files and sleep to inspect logs
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
