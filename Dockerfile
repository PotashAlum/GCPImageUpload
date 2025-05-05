# Dockerfile
FROM python:3.11-slim

WORKDIR /app

ENV HOST 0.0.0.0

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables (these will be overridden by Cloud Run)
ENV PORT=8080

# Run the application
CMD exec uvicorn main:app --host ${HOST} --port ${PORT}