FROM python:3.12-slim

# Install system dependencies (including poppler for PDF conversion)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libgl1 \
    libglib2.0-0 \
    poppler-utils \
    && which pdftoppm \
    && rm -rf /var/lib/apt/lists/*

# Install nodejs for localtunnel
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
