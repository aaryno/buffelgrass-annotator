FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir \
    google-cloud-storage \
    requests

# Copy the transfer script
COPY dropbox_transfer_job.py /app/dropbox_transfer_job.py
RUN chmod +x dropbox_transfer_job.py

# Set environment variables (will be overridden at runtime)
ENV GCS_BUCKET="tumamoc-2023"
ENV GCS_PREFIX="source-jpg/"

CMD ["python3", "dropbox_transfer_job.py"]



