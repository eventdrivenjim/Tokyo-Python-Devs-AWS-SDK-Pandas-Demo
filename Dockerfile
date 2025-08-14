# -----------------------------------------------------------------------------
# Multi-stage Dockerfile 
# PURPOSE:
#   - Small, secure runtime images
#   - Reproducible installs with uv.lock
#   - Optional AWS CLI v2 without bloating the runtime
# -----------------------------------------------------------------------------

# ---------- Global build args ----------
# Build arguments are available at build time only (not in running containers)
# They allow customization without modifying the Dockerfile

# Security: Non-root user configuration
# Using UID/GID 1000 is common for first non-system user on Linux
ARG GID=1000
ARG GROUP=app
ARG UID=1000
ARG USER=app
# Application source path(s) to copy into container
# Can be single path (demos/) or multiple paths (demos/ config/ src/)
# Trailing slash copies directory contents, not the directory itself
# Examples: demos/ | src/ config/ | . (entire context)
ARG SOURCE_PATH=demos/

# Python virtual environment location
# /usr/local/venv is standard for system-wide virtual environments
ARG VIRTUAL_ENV=/usr/local/venv

# Python version for consistency across all stages
# Using ARG allows easy version updates without editing multiple FROM statements
ARG DOCKER_PYTHON_VERSION=3.11

# Feature flag: Include development dependencies (awscli, etc.)
# Defaults to false for production security - must explicitly enable for dev builds
ARG INCLUDE_DEV_DEPS=false

# Development tools for local debugging and data processing
# jq: JSON processor for parsing AWS CLI output and API responses
# unzip: Archive extraction for downloading packages/datasets
ARG DEV_PACKAGES="jq unzip"


# ---------- BUILDER STAGE ----------
# Multi-stage pattern: Use full image for building, slim image for runtime
# ECR Public provides better reliability and rate limits than Docker Hub
# Full Python image includes build tools (gcc, make) needed for compiling packages
FROM public.ecr.aws/docker/library/python:${DOCKER_PYTHON_VERSION} AS builder

# Import build arguments into this stage
# ARGs must be re-declared in each stage where they're used
ARG VIRTUAL_ENV
ARG DOCKER_PYTHON_VERSION
ARG INCLUDE_DEV_DEPS
ARG SOURCE_PATH

# Install system dependencies and uv (ultra-fast Python package manager)
# --no-install-recommends: Reduces image size by avoiding suggested packages
# ca-certificates: Required for HTTPS connections to package repositories
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates apt-transport-https \
 && update-ca-certificates \
 && curl -LsSf https://astral.sh/uv/install.sh | sh

# Clean package cache to reduce layer size
# This is critical in builder stage to avoid carrying cache to final image
RUN rm -rf /var/lib/apt/lists/*

# Configure uv environment for builder stage
# PATH: Add uv binary location to PATH for command availability
# UV_NO_PROGRESS: Disable progress bars for cleaner build logs
# UV_PROJECT_ENVIRONMENT: Tell uv to use our custom venv location instead of default
ENV PATH="/root/.local/bin:${PATH}" \
    UV_NO_PROGRESS=1 \
    UV_PROJECT_ENVIRONMENT="${VIRTUAL_ENV}"

# Set working directory and copy dependency files first
# Docker layer caching: Dependencies change less frequently than source code
# Copying deps first allows reuse of dependency installation layer
WORKDIR /app
COPY pyproject.toml uv.lock ./

# Install dependencies based on build argument
# --frozen: Use exact versions from lockfile (reproducible builds)
# --no-install-project: Only install dependencies, not the project itself
# --extra dev: Include optional development dependencies when requested
RUN if [ "$INCLUDE_DEV_DEPS" = "true" ]; then \
      uv sync --frozen --no-install-project --extra dev; \
    else \
      uv sync --frozen --no-install-project; \
    fi

# Update PATH to prioritize virtual environment binaries
# This ensures we use the correct Python and installed packages
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

# Copy application source code AFTER dependencies
# Layer caching optimization: Source changes more frequently than dependencies
# This allows Docker to reuse the dependency installation layer
COPY ${SOURCE_PATH} .

# Precompile Python bytecode for performance and security
# Benefits: Faster startup time, enables read-only filesystem
# -q: Quiet mode (suppress output)
# Compile both application code and installed packages
RUN python -m compileall -q . \
 && python -m compileall -q "${VIRTUAL_ENV}/lib/python${DOCKER_PYTHON_VERSION}/site-packages"

# ---------- RUNTIME STAGE ----------
# Multi-stage optimization: Use minimal slim image for final runtime
# slim-bookworm: Debian 12 with minimal packages (~100MB vs ~900MB full image)
# Security benefit: Smaller attack surface, fewer potential vulnerabilities
FROM public.ecr.aws/docker/library/python:${DOCKER_PYTHON_VERSION}-slim-bookworm AS runtime

# Re-import build arguments needed in runtime stage
# Each stage is isolated and must explicitly import required ARGs
ARG GID
ARG GROUP
ARG UID
ARG USER
ARG VIRTUAL_ENV

# Configure Python runtime environment for containers
# PYTHONUNBUFFERED=1: Force stdout/stderr to be unbuffered for real-time logs
# PYTHONDONTWRITEBYTECODE=1: Don't create .pyc files (we precompiled in builder)
# TMPDIR=/tmp: Explicit temp directory for applications
# MALLOC_ARENA_MAX=2: Reduce memory fragmentation in containerized environments
# PATH: Ensure virtual environment binaries are found first
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TMPDIR=/tmp \
    MALLOC_ARENA_MAX=2 \
    PATH="${VIRTUAL_ENV}/bin:${PATH}"

# Install minimal runtime dependencies only
# ca-certificates: Required for HTTPS connections (AWS SDK, external APIs)
# curl: Useful for health checks and debugging
# Clean package cache immediately to minimize layer size
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl \
 && update-ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Security: Create non-root user for application execution
# Principle of least privilege: Container should not run as root
# -s /usr/sbin/nologin: No shell access (prevents interactive login)
# -M: No home directory creation (reduces attack surface)
RUN groupadd --gid "${GID}" "${GROUP}" \
 && useradd -u "${UID}" -g "${GID}" -s /usr/sbin/nologin -M "${USER}"

# Configure temporary directory with proper permissions
# /tmp needs to be writable for Python temporary files and caches
# chmod 1777: Sticky bit ensures users can only delete their own files
# chown root:root: Owned by root for security
RUN mkdir -p /tmp \
 && chown root:root /tmp \
 && chmod 1777 /tmp

# Copy application and dependencies from builder stage
# --from=builder: Multi-stage copy from named stage
# --chown: Set ownership during copy (more efficient than separate chown)
# Application owned by app user, virtual env owned by root (security)
COPY --from=builder --chown=${USER}:${GROUP} /app /app
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Security: Make application and dependencies read-only
# chmod 555: Read and execute permissions only (no write)
# Prevents runtime modification of code or dependencies
# Defense-in-depth against code injection attacks
RUN chmod -R 555 /app "${VIRTUAL_ENV}"

# Security: Switch to non-root user for application execution
# All subsequent operations run with limited privileges
# Container orchestrators (ECS/EKS) will provide the CMD at runtime
USER ${USER}:${GROUP}
WORKDIR /app
# No CMD specified - allows flexible deployment in different orchestrators

# ---------- TOOLSET STAGE ----------
# Advanced pattern: Extract package files without installing package manager
# This allows adding tools to final stage without apt/dpkg overhead
FROM debian:bookworm-slim AS toolset

ARG DEV_PACKAGES

# Advanced technique: Download and extract .deb packages without installing
# This creates a clean toolset that can be copied to other stages
# Benefits: No package manager overhead, smaller final images
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends ca-certificates apt-transport-https; \
    update-ca-certificates; \
    mkdir -p /tmp/aptcache /rootfs; \
    apt-get -o Dir::Cache::archives=/tmp/aptcache \
        install -y --reinstall --no-install-recommends --download-only ${DEV_PACKAGES}; \
    for deb in /tmp/aptcache/*.deb; do dpkg-deb -x "$deb" /rootfs; done; \
    tar -C /rootfs -cf /toolset.tar .;

# ---------- DEV-TOOLS STAGE (Development Only) ----------
# Extends runtime with development tools for local development
# WARNING: This stage is NOT for production - includes package managers and CLI tools
# Use case: Local development, debugging
FROM runtime AS dev-tools

ARG GROUP
ARG USER

# Temporarily switch to root for system modifications
USER root

# Install toolset without package manager overhead
# Advanced pattern: Extract pre-downloaded packages from toolset stage
# ldconfig: Update dynamic linker cache after adding new libraries
COPY --from=toolset /toolset.tar /tmp/toolset.tar
RUN set -eux; tar -C / -xf /tmp/toolset.tar && rm /tmp/toolset.tar && ldconfig

# Copy uv package manager from builder for dependency management
# Allows updating pyproject.toml and uv.lock during development
COPY --from=builder /root/.local/bin/uv /usr/local/bin/uv

# Create home directory for development user
# Some tools expect a writable home directory
RUN mkdir -p /home/app && chown -R "${USER}:${GROUP}" /home/app

# Configure development tool caching
# All caches point to /tmp for easy cleanup and security
# UV_NO_PROGRESS: Clean logs without progress bars
# XDG_CACHE_HOME: Standard cache location for many tools
# AWS_PAGER: Disable AWS CLI pagination for container-friendly output
ENV UV_NO_PROGRESS=1 \
    UV_CACHE_DIR=/tmp \
    XDG_CACHE_HOME=/tmp \
    PIP_CACHE_DIR=/tmp \
    AWS_PAGER=""

# Install AWS CLI v2 for development and infrastructure management
# Multi-architecture support: Detects and installs correct binary for platform
# AWS CLI v2 provides better performance and features than v1
# Only installed in dev-tools stage to avoid bloating production runtime
RUN set -eux; \
    arch="$(dpkg --print-architecture)"; \
    case "$arch" in \
      amd64) AWS_ARCH=x86_64 ;; \
      arm64) AWS_ARCH=aarch64 ;; \
      *) echo "Unsupported architecture: $arch"; exit 1 ;; \
    esac; \
    curl -LsS "https://awscli.amazonaws.com/awscli-exe-linux-${AWS_ARCH}.zip" -o awscliv2.zip; \
    unzip -q awscliv2.zip; \
    ./aws/install --bin-dir /usr/local/bin --install-dir /usr/local/aws-cli; \
    rm -rf awscliv2.zip aws/;

# Switch back to non-root user for development work
# Maintains security principles even in development environment
USER ${USER}:${GROUP}

WORKDIR /app 

# Default to interactive bash shell for development
# Provides convenient environment for running demos and debugging
CMD ["bash"]
