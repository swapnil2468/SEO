FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=0 \
    HOME=/root

# System dependencies
RUN apt-get update && apt-get install -y \
    wget gnupg unzip curl \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdbus-1-3 libx11-xcb1 \
    libxcomposite1 libxdamage1 libxrandr2 libgbm1 libasound2 libpangocairo-1.0-0 \
    fonts-liberation libappindicator3-1 libxss1 lsb-release libgtk-3-0 \
    chromium && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Python packages
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt && playwright install chromium

# App source
COPY . /app
WORKDIR /app

# Expose Streamlit port
EXPOSE 8501

# Run app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
