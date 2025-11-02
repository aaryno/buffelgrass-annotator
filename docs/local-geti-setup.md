# Running GETI Locally for Annotations

This guide covers setting up GETI on your local machine for annotation work.

## Quick Start

```bash
# 1. Install prerequisites (if needed)
brew install k3d helm kubectl

# 2. Run the setup script
./k8s/k3d-local-setup.sh

# 3. Build and deploy GETI (from geti/ directory)
cd geti
make build-image
make publish-image
make build-umbrella-chart
make publish-umbrella-chart

# 4. Install GETI platform
# Copy installer to temp directory and run
cp -r platform/services/installer/platform_<TAG> /tmp/geti
cd /tmp/geti
./platform_installer install
```

## What Gets Created

- **k3d Kubernetes cluster** named `geti-local` with 2 agent nodes
- **Local Docker registry** on `localhost:5000`
- **Load balancer** exposing ports 8080 (HTTP) and 8443 (HTTPS)

## Accessing GETI

Once deployed, access the GETI web UI at:
- **URL**: http://localhost:8080
- Create an account and start annotating!

## Architecture

GETI is a microservices platform running on Kubernetes with:
- **Web UI** for annotation and model training
- **Platform services** (identity, logging, observability)
- **ML workflows** (training, optimization, deployment)
- **Data storage** (MongoDB, PostgreSQL, Kafka, etcd)

## Useful Commands

```bash
# Check cluster status
kubectl get nodes
kubectl get pods -A

# View GETI logs
kubectl logs -f <pod-name> -n <namespace>

# Restart cluster
k3d cluster stop geti-local
k3d cluster start geti-local

# Delete cluster
k3d cluster delete geti-local

# Rebuild and update a specific component
cd geti/interactive_ai/services/<service-name>
make build-image
make publish-image
helm upgrade <release-name> <chart> -n <namespace>
```

## Building Specific Components

If you're developing and need to rebuild individual components:

```bash
# Navigate to component directory
cd geti/interactive_ai/services/<component-name>

# Build just that component
make build-image
make tests

# Push to local registry
make publish-image
```

## Troubleshooting

**Port conflicts:**
- Ensure ports 8080, 8443, and 5000 are available
- Modify ports in setup script if needed

**Not enough resources:**
- GETI requires significant memory (~16GB recommended)
- Reduce agent nodes or use a lighter config

**Images not pulling:**
- Verify local registry is running: `docker ps | grep registry`
- Check registry connectivity: `curl http://localhost:5000/v2/_catalog`

**Installer not found:**
- Check the VERSION file in geti/ to find the correct tag
- The installer path includes the version tag

## Alternative: Using the GETI SDK Without Full Platform

If you only need to **annotate** and don't need the full platform running locally, consider:

1. **Use a remote GETI instance** (if available)
2. **Use the GETI SDK** to interact with projects programmatically
3. **Deploy on a cloud VM** with more resources (see `docs/remote-training-via-sdk.md`)

For just annotation work, option #1 (remote instance) is much simpler than running the full stack locally.

## Next Steps

After GETI is running:
1. Create a new project for buffelgrass detection
2. Upload training chips from `gs://tumamoc-2023/training_chips/`
3. Annotate buffelgrass regions (semantic segmentation)
4. Train your model
5. Export for inference on full imagery

See the [SDK notebooks](../geti-sdk/notebooks/) for programmatic workflows.



