# Cloud Run container for parallel chip extraction
FROM python:3.11-slim

# Install GDAL and rasterio dependencies
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Set GDAL environment
ENV GDAL_CONFIG=/usr/bin/gdal-config

# Install Python packages
RUN pip install --no-cache-dir \
    google-cloud-storage \
    rasterio \
    pillow \
    numpy

# Copy extraction script
COPY chip_extraction_job.py /app/chip_extraction_job.py
WORKDIR /app

# Make script executable
RUN chmod +x chip_extraction_job.py

# Run the job
CMD ["python3", "chip_extraction_job.py"]


