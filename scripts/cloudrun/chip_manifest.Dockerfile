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
    requests

# Copy script
COPY chip_manifest_job.py /app/chip_manifest_job.py
WORKDIR /app

RUN chmod +x chip_manifest_job.py

CMD ["python3", "chip_manifest_job.py"]


