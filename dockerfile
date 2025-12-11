# -------------------------------
# Base Image
# -------------------------------
FROM python:3.11-slim

# -------------------------------
# Work Directory
# -------------------------------
WORKDIR /app

# -------------------------------
# Install system dependencies
# -------------------------------
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------
# Copy dependency file first
# -------------------------------
COPY requirements.txt .

# -------------------------------
# Install Python dependencies
# -------------------------------
RUN pip install --no-cache-dir -r requirements.txt

# -------------------------------
# Copy your entire application
# -------------------------------
COPY . .

# -------------------------------
# Expose Streamlit port
# -------------------------------
EXPOSE 8501

# -------------------------------
# Streamlit (headless) config
# -------------------------------
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ENABLE_CORS=false

# -------------------------------
# Run your main Streamlit file
# -------------------------------
CMD ["streamlit", "run", "web1.py", "--server.address=0.0.0.0"]
