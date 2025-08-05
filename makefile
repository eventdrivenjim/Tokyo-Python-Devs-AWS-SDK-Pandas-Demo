# AWS Wrangler Demo Container Management
# Usage: make <target>
# Common targets: build, shell, inspect, clean

# Container configuration
NS = local                    # Namespace for image tagging
VERSION ?= latest            # Image version (can be overridden)

# Container engine - change to podman if preferred
CONTAINER_ENGINE=docker

# Build configuration
INCLUDE_DEV_DEPS ?= true     # Include dev dependencies (awscli) - set to false for production

# Container naming
REPO = wrangler-demo         # Repository name for the image
NAME = wrangler-demo         # Container name when running

INSTANCE = default           # Instance identifier for multiple containers

# Runtime environment variables
ENV = \
	-e AWS_DEFAULT_REGION=ap-northeast-1

# Volume mounts for container
VOLUMES= \
  -v $(HOME)/.aws:/home/app/.aws:ro \  # Mount AWS credentials (read-only)
  -v $(PWD):/app                   # Mount current directory to /app

# Declare phony targets (not files)
.PHONY: help build shell inspect clean rm status

# Default target - show help
.DEFAULT_GOAL := help


# Build image with configurable dev dependencies
# Override with: make build INCLUDE_DEV_DEPS=false
build:
	$(CONTAINER_ENGINE) build --no-cache \
		--build-arg INCLUDE_DEV_DEPS=$(INCLUDE_DEV_DEPS) \
		-t $(NS)/$(REPO):$(VERSION) .

# Run interactive shell with local files mounted (development mode)
shell: build
	$(CONTAINER_ENGINE) run --rm --name $(NAME)-$(INSTANCE) -i -t $(PORTS) $(VOLUMES) $(ENV) $(NS)/$(REPO):$(VERSION) /bin/bash

# Run interactive shell without local files (simulates production deployment)
inspect: build
	$(CONTAINER_ENGINE) run --rm --name $(NAME)-$(INSTANCE) -i -t $(PORTS) $(ENV) $(NS)/$(REPO):$(VERSION) /bin/bash

# Clean up images and containers
clean:
	$(CONTAINER_ENGINE) image prune -f
	$(CONTAINER_ENGINE) rmi $(NS)/$(REPO):$(VERSION) 2>/dev/null || true

# Show running containers
status:
	$(CONTAINER_ENGINE) ps -a --filter name=$(NAME)

# Remove stopped container (cleanup)
rm:
	$(CONTAINER_ENGINE) rm $(NAME)-$(INSTANCE)

# Show available targets and their descriptions
help:
	@echo "AWS Wrangler Demo Container Management"
	@echo "Usage: make <target>"
	@echo ""
	@echo "Available targets:"
	@echo "  build      - Build image with dev dependencies (override: INCLUDE_DEV_DEPS=false)"
	@echo "  shell      - Run interactive shell with local files mounted (development)"
	@echo "  inspect    - Run interactive shell without local files (production-like)"
	@echo "  status     - Show running containers"
	@echo "  clean      - Remove built images and prune unused images"
	@echo "  rm         - Remove stopped container"
	@echo "  help       - Show this help message"
	@echo ""
	@echo "Configuration:"
	@echo "  CONTAINER_ENGINE=$(CONTAINER_ENGINE)"
	@echo "  INCLUDE_DEV_DEPS=$(INCLUDE_DEV_DEPS)"
	@echo "  VERSION=$(VERSION)"