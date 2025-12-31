# Base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code (excluding models)
# The .dockerignore file should prevent the models directory from being copied.
COPY . /app

RUN mkdir -p cache && chmod 777 cache

# Command to run the application
CMD ["python", "main.py"] 