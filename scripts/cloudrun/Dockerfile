# Cloud Run container for parallel COG conversion
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
    rio-cogeo

# Copy conversion script
COPY convert_cog_job.py /app/convert_cog_job.py
WORKDIR /app

# Make script executable
RUN chmod +x convert_cog_job.py

# Run the job
CMD ["python3", "convert_cog_job.py"]


