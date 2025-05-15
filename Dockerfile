# Use a Python 3.10 slim image
FROM python:3.10-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY streamlit_app_dynamic.py .
COPY img/ ./img/
COPY .streamlit/ ./.streamlit/

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=TRUE
ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Run the application
CMD streamlit run streamlit_app_dynamic.py 