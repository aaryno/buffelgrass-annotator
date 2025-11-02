# Setup GCS Credentials for Rasterio

Rasterio (via GDAL) needs application default credentials to read COGs from GCS without downloading them.

## One-Time Setup

Run this command:

```bash
gcloud auth application-default login --configuration=asdm
```

This will:
1. Open your browser for authentication
2. Create credentials at `~/.config/gcloud/application_default_credentials.json`
3. Allow rasterio/GDAL to access GCS using your gcloud credentials

## After Setup

You'll be able to:
- Read COG metadata directly from GCS (no download needed)
- Extract chips directly from GCS URLs
- Run `make check-dimensions` successfully

## Verify It Works

```bash
# Should work after setup
make check-dimensions
```

This will sample 20 COGs from `gs://tumamoc-2023/cogs/` and report typical dimensions.


