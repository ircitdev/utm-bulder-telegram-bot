# Use Python 3.9 slim image as base
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port (if your bot needs to expose any ports)
# EXPOSE 8080

# Command to run the bot
CMD ["python", "utm_telegram_bot.py"]