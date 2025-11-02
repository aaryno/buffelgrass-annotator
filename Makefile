.PHONY: help google-auth setup venv install test clean status transfer transfer-resume convert-cogs convert-cogs-sequential split-dataset merge-annotations test-chips extract-chips
.PHONY: cvat-install cvat-start cvat-stop cvat-restart cvat-logs cvat-status cvat-create-user cvat-setup-project cvat-complete-setup cvat-backup cvat-clean

# Default target - show help
help:
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║         ASDM Buffelgrass Mapping - Available Commands         ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "🔐 Authentication & Setup:"
	@echo "  make google-auth       Set up GCP credentials for aaryno@gmail.com"
	@echo "  make setup             Create virtual environment and install dependencies"
	@echo ""
	@echo "📊 Data Pipeline:"
	@echo "  make status                   Check Dropbox transfer and COG conversion status"
	@echo "  make transfer                 ⚡ Dropbox → GCS transfer (Cloud Run, 50 workers)"
	@echo "  make transfer-resume          Resume sequential transfer (Cloud Shell, slow)"
	@echo "  make convert-cogs             ⚡ JPEG → COG conversion (Cloud Run, 50 workers)"
	@echo "  make convert-cogs-sequential  Resume sequential conversion (Cloud Shell, slow)"
	@echo ""
	@echo "🔬 Chip Extraction:"
	@echo "  make generate-manifest            ⚡ Generate chip manifest (976 COGs × 30 chips = ~29K windows, 625 bins)"
	@echo "  make merge-manifest               Merge partial manifests into final chip-manifest.csv"
	@echo "  make extract-chips-for-annotation Extract chips from manifest (e.g., BIN=aa COUNT=500)"
	@echo "  make create-bins                  Create random bin assignments (A-Z) for source images"
	@echo "  make check-dimensions             Check typical COG dimensions and chip capacity"
	@echo "  make test-chip-manifest           Test manifest generation with simulated data"
	@echo "  make extract-chips-parallel       ⚡ Extract chips using Cloud Run (975 COGs → 3,900 chips in 10 folders)"
	@echo "  make extract-chips                Extract training chips from COGs (sequential, slow)"
	@echo "  make test-chips                   Test chip extraction with sample image"
	@echo ""
	@echo "👥 Collaborative Annotation:"
	@echo "  make split-dataset     Split chips for parallel annotation (2+ people)"
	@echo "  make merge-annotations Merge COCO annotations from multiple annotators"
	@echo ""
	@echo "🎨 Annotation (CVAT):"
	@echo "  make cvat-complete-setup    🚀 Complete setup: install + user + project + images"
	@echo "  make cvat-install           Install CVAT (Docker Compose)"
	@echo "  make cvat-create-user       Create admin user (bypasses web UI)"
	@echo "  make cvat-setup-project     Create project with labels and upload images"
	@echo "  make cvat-start             Start CVAT services"
	@echo "  make cvat-stop              Stop CVAT services"
	@echo "  make cvat-restart           Restart CVAT services"
	@echo "  make cvat-logs              View CVAT logs"
	@echo "  make cvat-status            Check CVAT status"
	@echo "  make cvat-backup            Backup annotations and data"
	@echo "  make cvat-clean             Remove CVAT (keeps volumes/data)"
	@echo ""
	@echo "🧪 Development:"
	@echo "  make venv              Create Python virtual environment"
	@echo "  make install           Install Python dependencies"
	@echo "  make test              Run unit tests"
	@echo "  make clean             Clean up temporary files and caches"
	@echo ""
	@echo "📖 Documentation:"
	@echo "  make help              Show this help message"
	@echo ""

# GCP Authentication for aaryno@gmail.com
google-auth:
	@echo "🔐 Setting up Google Cloud authentication for aaryno@gmail.com..."
	@echo ""
	@gcloud auth login aaryno@gmail.com
	@echo ""
	@echo "Setting default project to 'asdm'..."
	@gcloud config set project asdm
	@echo ""
	@echo "Setting up application default credentials..."
	@gcloud auth application-default login
	@echo ""
	@echo "✓ Authentication complete!"
	@echo ""
	@echo "Your credentials are now available for:"
	@echo "  • gcloud CLI"
	@echo "  • gsutil"
	@echo "  • Python GCS clients"
	@echo "  • rasterio (for GCS COG access)"

# Create Python virtual environment
venv:
	@echo "📦 Creating Python virtual environment..."
	python3 -m venv venv
	@echo "✓ Virtual environment created at ./venv"
	@echo ""
	@echo "To activate:"
	@echo "  source venv/bin/activate"

# Install Python dependencies
install: venv
	@echo "📥 Installing Python dependencies..."
	@. venv/bin/activate && pip install --upgrade pip --quiet
	@. venv/bin/activate && pip install rasterio google-cloud-storage requests --quiet
	@echo "✓ Dependencies installed"

# Complete setup
setup: install
	@echo ""
	@echo "✓ Setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Run 'make google-auth' to authenticate with GCP"
	@echo "  2. Run 'make status' to check pipeline status"
	@echo "  3. Run 'make convert-cogs' to resume COG conversion"

# Check pipeline status
status:
	@./scripts/check_pipeline_status.sh

# Parallel Dropbox transfer using Cloud Run Jobs (50 parallel workers - FAST!)
transfer:
	@cd scripts/cloudrun && bash deploy_dropbox_transfer.sh 50

# Sequential Dropbox transfer (slow fallback)
transfer-resume:
	@echo "📥 Sequential Dropbox → GCS transfer (Cloud Shell)..."
	@echo "⚠️  Note: This is MUCH slower than 'make transfer'"
	@echo ""
	@echo "Files will be uploaded to: gs://tumamoc-2023/source-jpg/"
	@echo ""
	@nohup ./scripts/transfer_from_local.sh > /tmp/transfer.log 2>&1 &
	@echo "✓ Transfer started in background (PID: $$!)"
	@echo "  Log: /tmp/transfer.log"
	@echo ""
	@echo "Monitor progress:"
	@echo "  tail -f /tmp/transfer.log"
	@echo "  make status"

# COG conversion using Cloud Run Jobs (50 parallel workers - FAST!)
convert-cogs:
	@cd scripts/cloudrun && bash deploy_and_run.sh 50

# Sequential COG conversion (slow fallback)
convert-cogs-sequential:
	@echo "🔄 Sequential JPEG → COG conversion (Cloud Shell)..."
	@echo "⚠️  Note: This is MUCH slower than 'make convert-cogs'"
	@echo ""
	@echo "Source: gs://tumamoc-2023/source-jpg/"
	@echo "Destination: gs://tumamoc-2023/cogs/"
	@echo ""
	@nohup ./scripts/convert_cogs_cloudshell.sh > /tmp/cog_conversion.log 2>&1 &
	@echo "✓ COG conversion started in background (PID: $$!)"
	@echo "  Log: /tmp/cog_conversion.log"
	@echo ""
	@echo "Monitor progress:"
	@echo "  tail -f /tmp/cog_conversion.log"
	@echo "  make status"

# Split dataset for parallel annotation
split-dataset: venv
	@echo "📊 Splitting dataset for parallel annotation..."
	@read -p "Number of annotators [2]: " num; \
	num=$${num:-2}; \
	read -p "Input chips directory [data/training_chips]: " input; \
	input=$${input:-data/training_chips}; \
	echo ""; \
	. venv/bin/activate && python3 scripts/split_dataset_by_region.py $$input -n $$num

# Merge COCO annotations
merge-annotations: venv
	@echo "🔗 Merging COCO annotation files..."
	@echo "Place all annotation JSON files in data/annotation_exports/"
	@read -p "Press Enter when ready..."; \
	. venv/bin/activate && python3 scripts/merge_coco_annotations.py \
		data/annotation_exports/*.json \
		-o data/merged_annotations.json \
		--verify

# Generate complete chip manifest (30 chips per COG)
generate-manifest:
	@echo "⚡ Generating chip manifest (Cloud Run)..."
	@echo ""
	@echo "This will:"
	@echo "  • Process ~976 COGs"
	@echo "  • Compute 6×5 grid (30 chips) per COG"
	@echo "  • Assign each chip to one of 625 bins (AA-YY)"
	@echo "  • Generate ~29,280 chip windows"
	@echo "  • Output to gs://tumamoc-2023/chip_manifests/"
	@echo ""
	@read -p "Press Enter to continue or Ctrl+C to cancel..."; \
	cd scripts/cloudrun && ./deploy_chip_manifest.sh

# Merge partial manifests into final CSV
merge-manifest: venv
	@echo "🔗 Merging partial chip manifests..."
	@echo ""
	@. venv/bin/activate && python3 scripts/merge_chip_manifest.py

# Test chip manifest generation
test-chip-manifest: venv
	@echo "🧪 Testing chip manifest generation..."
	@echo ""
	@. venv/bin/activate && python3 scripts/generate_chip_manifest.py

# Extract chips from manifest for annotation
extract-chips-for-annotation: venv
	@if [ -z "$(BIN)" ]; then echo "❌ Error: BIN not specified"; echo "Usage: make extract-chips-for-annotation BIN=aa COUNT=500"; exit 1; fi
	@echo "✂️  Extracting chips from bin '$(BIN)'..."
	@echo ""
	@. venv/bin/activate && python3 scripts/extract_chips_from_manifest.py \
		--bin $(BIN) \
		--count $(or $(COUNT),1000) \
		--output-dir chips_$(BIN)/

# Create random bin assignments (A-Z) for source images
create-bins: venv
	@echo "🎲 Creating random bin assignments (A-Z)..."
	@echo ""
	@echo "This will:"
	@echo "  • List all COGs from gs://tumamoc-2023/cogs/"
	@echo "  • Randomly assign each to a bin (A-Z)"
	@echo "  • Save to image-bin.csv locally"
	@echo "  • Upload to gs://tumamoc-2023/image-bin.csv"
	@echo ""
	@. venv/bin/activate && python3 scripts/create_image_bins.py

# Check typical COG dimensions
check-dimensions: venv
	@echo "📏 Checking COG dimensions and chip capacity..."
	@echo ""
	@. venv/bin/activate && python3 scripts/check_image_dimensions.py

# Test chip extraction
test-chips: venv
	@echo "🔬 Testing chip extraction (PNG format for GETI)..."
	@mkdir -p /tmp/test_cogs /tmp/test_chips
	@echo "Downloading test COG..."
	@gsutil -q cp gs://tumamoc-2023/cogs/cap-29792.tif /tmp/test_cogs/ 2>/dev/null || echo "Using cached file"
	@echo "Extracting 5 test chips as PNG..."
	@. venv/bin/activate && python3 scripts/chip_extractor.py \
		/tmp/test_cogs/cap-29792.tif \
		-n 5 \
		-o /tmp/test_chips \
		-f png
	@echo ""
	@echo "✓ PNG chips created in /tmp/test_chips/ (ready for GETI)"
	@ls -lh /tmp/test_chips/

# Parallel chip extraction using Cloud Run Jobs (FAST!)
extract-chips-parallel:
	@echo "⚡ Extracting chips using Cloud Run (50 parallel workers)..."
	@echo ""
	@echo "This will:"
	@echo "  • Extract 4 non-overlapping chips per COG"
	@echo "  • Create 10 folders (01-10) for parallel annotation"
	@echo "  • Name chips with 'A_' prefix (for future 'B_' expansion)"
	@echo "  • Output: gs://tumamoc-2023/training_chips/1024x1024/{01-10}/"
	@echo ""
	@read -p "Press Enter to continue or Ctrl+C to cancel..."; \
	cd scripts/cloudrun && ./deploy_chip_extraction.sh --execute

# Extract chips from all COGs (sequential, slow)
extract-chips: venv
	@echo "✂️  Extracting training chips from COGs..."
	@echo ""
	@echo "This will extract 1 random 1024x1024 chip per COG (977 total)."
	@echo ""
	@read -p "Number of chips per image [1]: " n_chips; \
	n_chips=$${n_chips:-1}; \
	read -p "Output directory [./data/training_chips]: " output_dir; \
	output_dir=$${output_dir:-./data/training_chips}; \
	echo ""; \
	echo "Extracting $$n_chips chip(s) per image to $$output_dir..."; \
	echo "This may take a while..."; \
	echo ""; \
	. venv/bin/activate && python3 scripts/batch_extract_chips.py \
		--bucket tumamoc-2023 \
		--prefix cogs/ \
		-n $$n_chips \
		-o $$output_dir

# Run tests
test: venv
	@echo "🧪 Running unit tests..."
	@. venv/bin/activate && python3 tests/test_chip_coords.py

# Clean temporary files
clean:
	@echo "🧹 Cleaning up..."
	@rm -rf __pycache__ scripts/__pycache__ tests/__pycache__
	@rm -rf .pytest_cache
	@rm -rf *.egg-info
	@rm -f /tmp/transfer.log /tmp/cog_conversion.log
	@echo "✓ Cleanup complete"

# Clean everything including venv
clean-all: clean
	@echo "🧹 Removing virtual environment..."
	@rm -rf venv
	@echo "✓ Full cleanup complete"

#==============================================================================
# CVAT Annotation Tools
#==============================================================================

# Complete CVAT setup (one command to rule them all)
cvat-complete-setup:
	@echo "🌾 Complete CVAT Setup for Buffelgrass Annotation"
	@echo "=================================================="
	@echo ""
	@if [ -f .cvat.env ]; then \
		echo "📝 Using credentials from .cvat.env"; \
		. ./.cvat.env; \
		username=$$CVAT_USERNAME; \
		email=$$CVAT_EMAIL; \
		password=$$CVAT_PASSWORD; \
		read -p "Training images directory [./data/training_chips]: " img_dir; \
		img_dir=$${img_dir:-./data/training_chips}; \
	else \
		read -p "Username [admin]: " username; \
		username=$${username:-admin}; \
		read -p "Email [$$username@localhost]: " email; \
		email=$${email:-$$username@localhost}; \
		read -sp "Password: " password; \
		echo ""; \
		read -p "Training images directory [./data/training_chips]: " img_dir; \
		img_dir=$${img_dir:-./data/training_chips}; \
	fi; \
	echo ""; \
	echo "Setting up CVAT with:"; \
	echo "  User: $$username ($$email)"; \
	echo "  Images: $$img_dir"; \
	echo ""; \
	./cvat/complete-setup.sh \
		--username "$$username" \
		--email "$$email" \
		--password "$$password" \
		--image-dir "$$img_dir"

# Install CVAT
cvat-install:
	@echo "🚀 Installing CVAT..."
	@./cvat/setup.sh
	@echo ""
	@echo "✓ CVAT installed!"
	@echo "  Access at: http://localhost:8080"
	@echo ""
	@echo "Next steps:"
	@echo "  make cvat-create-user        Create admin user"
	@echo "  make cvat-setup-project      Create project and upload images"
	@echo "  make cvat-complete-setup     Do everything in one command"

# Start CVAT services
cvat-start:
	@if docker ps | grep -q cvat_server; then \
		echo "✅ CVAT is already running"; \
		echo "   Access at: http://localhost:8080"; \
	else \
		echo "🚀 Starting CVAT..."; \
		cd ~/cvat && docker compose start; \
		echo "✓ CVAT started"; \
		echo "  Access at: http://localhost:8080"; \
	fi

# Stop CVAT services (preserves data)
cvat-stop:
	@echo "⏸️  Stopping CVAT..."
	@cd ~/cvat && docker compose stop
	@echo "✓ CVAT stopped (data preserved)"
	@echo "  To start again: make cvat-start"

# Restart CVAT services
cvat-restart:
	@echo "🔄 Restarting CVAT..."
	@cd ~/cvat && docker compose restart
	@echo "✓ CVAT restarted"
	@echo "  Access at: http://localhost:8080"

# View CVAT logs
cvat-logs:
	@echo "📋 CVAT logs (Ctrl+C to exit):"
	@echo ""
	@cd ~/cvat && docker compose logs -f --tail=100

# Check CVAT status
cvat-status:
	@echo "📊 CVAT Status"
	@echo "=============="
	@echo ""
	@if docker ps | grep -q cvat_server; then \
		echo "✅ CVAT is running"; \
		echo ""; \
		echo "Services:"; \
		docker ps --format "table {{.Names}}\t{{.Status}}" | grep cvat; \
		echo ""; \
		echo "Volumes:"; \
		docker volume ls | grep cvat | awk '{print "  " $$2}'; \
		echo ""; \
		echo "Access at: http://localhost:8080"; \
	else \
		echo "⏸️  CVAT is not running"; \
		echo ""; \
		if [ -d "$$HOME/cvat" ]; then \
			echo "CVAT is installed but stopped"; \
			echo "  Start with: make cvat-start"; \
		else \
			echo "CVAT is not installed"; \
			echo "  Install with: make cvat-install"; \
		fi; \
	fi

# Create CVAT admin user
cvat-create-user:
	@if ! docker ps | grep -q cvat_server; then \
		echo "❌ CVAT is not running"; \
		echo "  Start CVAT first: make cvat-start"; \
		exit 1; \
	fi
	@echo "👤 Create CVAT Admin User"
	@echo "========================="
	@echo ""
	@./cvat/create-user.sh

# Create project with labels and upload images
cvat-setup-project:
	@if ! docker ps | grep -q cvat_server; then \
		echo "❌ CVAT is not running"; \
		echo "  Start CVAT first: make cvat-start"; \
		exit 1; \
	fi
	@echo "📁 Setup Buffelgrass Detection Project"
	@echo "======================================="
	@echo ""
	@if [ -f .cvat.env ]; then \
		echo "📝 Using credentials from .cvat.env"; \
		. ./.cvat.env; \
		username=$$CVAT_USERNAME; \
		password=$$CVAT_PASSWORD; \
		read -p "Training images directory [./data/training_chips]: " img_dir; \
		img_dir=$${img_dir:-./data/training_chips}; \
	else \
		read -p "CVAT Username: " username; \
		read -sp "CVAT Password: " password; \
		echo ""; \
		read -p "Training images directory [./data/training_chips]: " img_dir; \
		img_dir=$${img_dir:-./data/training_chips}; \
	fi; \
	echo ""; \
	if [ ! -d "venv" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv venv; \
		. venv/bin/activate && pip install --quiet cvat-sdk; \
	fi; \
	if [ -d "$$img_dir" ]; then \
		echo "Creating project and uploading images from $$img_dir..."; \
		. venv/bin/activate && python3 cvat/auto-setup-project.py \
			--username "$$username" \
			--password "$$password" \
			--image-dir "$$img_dir"; \
	else \
		echo "⚠️  Directory $$img_dir not found"; \
		echo "Creating project without images..."; \
		. venv/bin/activate && python3 cvat/auto-setup-project.py \
			--username "$$username" \
			--password "$$password"; \
		echo ""; \
		echo "To upload images later:"; \
		echo "  1. Extract chips: make extract-chips"; \
		echo "  2. Run: make cvat-setup-project"; \
	fi

# Backup CVAT data
cvat-backup:
	@echo "💾 Backing up CVAT data..."
	@mkdir -p ./cvat/backups
	@echo "Backing up database..."
	@docker exec cvat_db pg_dump -U root -d cvat > ./cvat/backups/cvat_backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "✓ Database backed up to ./cvat/backups/"
	@echo ""
	@echo "Backing up volumes info..."
	@docker volume ls | grep cvat > ./cvat/backups/volumes_$$(date +%Y%m%d_%H%M%S).txt
	@echo "✓ Volumes list saved"
	@echo ""
	@echo "To backup uploaded images, run:"
	@echo "  docker cp cvat_server:/home/django/data ./cvat/backups/cvat_data_$$(date +%Y%m%d)"

# Clean CVAT (keeps data volumes)
cvat-clean:
	@echo "🧹 Removing CVAT containers..."
	@cd ~/cvat && docker compose down
	@echo "✓ CVAT containers removed (data volumes preserved)"
	@echo ""
	@echo "Your annotations and data are safe in Docker volumes."
	@echo "To remove everything including data:"
	@echo "  cd ~/cvat && docker compose down -v"
	@echo ""
	@echo "To reinstall:"
	@echo "  make cvat-install"

