FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY telegram_bot/requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code to current directory
COPY telegram_bot/ ./

# Create logs directory
RUN mkdir -p logs

# Expose port (Railway needs this)
EXPOSE 8000

# Start the bot (no cd needed since files are in current directory)
CMD ["python", "bot_runner.py"]