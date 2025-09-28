FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY telegram_bot/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY telegram_bot/ .

# Create logs directory
RUN mkdir -p logs

# Expose port (Railway needs this)
EXPOSE 8000

# Start the bot
CMD ["python", "bot_runner.py"]