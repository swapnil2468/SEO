FROM python:3.11-slim

# System dependencies for Playwright + Chrome
RUN apt-get update && apt-get install -y \
    wget curl gnupg unzip xvfb libglib2.0-0 libnss3 libgconf-2-4 \
    libfontconfig1 libxss1 libasound2 libgtk-3-0 libx11-xcb1 libdbus-glib-1-2 && \
    apt-get clean

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright + browser binaries
RUN pip install playwright && playwright install --with-deps

# Copy app code
COPY . /app
WORKDIR /app

# Streamlit entry point
CMD ["streamlit", "run", "app.py", "--server.port=10000", "--server.address=0.0.0.0"]
