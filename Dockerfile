# Multi-stage Docker build for AWS Wrangler demos
# Stage 1 (builder): Install dependencies and compile Python packages
# Stage 2 (final): Copy only what's needed for a smaller, more secure runtime image
# This approach reduces final image size and attack surface

# Build arguments (ARG) - available at build time only, not in running container
# These define user/group settings and Python version for consistency
# our user name/id for this container
# the uid/gid will be matched as user in our task definition to 
# restrict user in container
ARG GID=1000
ARG GROUP=app
ARG UID=1000
ARG USER=app
ARG VIRTUAL_ENV=/usr/local/venv  # Virtual env location - /usr/local for system-wide packages
ARG DOCKER_PYTHON_VERSION=3.11

# BUILDER STAGE: Install dependencies and compile packages
# Use ECR Public instead of Docker Hub for better reliability and AWS integration
# ECR Public has higher rate limits and is optimized for AWS workloads
FROM public.ecr.aws/docker/library/python:${DOCKER_PYTHON_VERSION} AS builder

# Import build arguments into this stage
ARG VIRTUAL_ENV
ARG DOCKER_PYTHON_VERSION

# Create Python virtual environment at /usr/local/venv to isolate dependencies
# Location choice: /usr/local is standard for system-wide installed software
# This prevents conflicts with system Python packages and improves security
RUN python3 -m venv ${VIRTUAL_ENV}
# Environment variables (ENV) persist in running container, unlike ARG
# Add virtual environment to PATH so Python uses our isolated packages
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

# Set working directory to /app - standard location for application code
WORKDIR /app

# Copy dependency files first for better Docker layer caching
COPY pyproject.toml .
COPY uv.lock . 

# Install packages using uv (ultra-fast Python package installer)
# Extract and install dependencies directly without building project
# We run as separate for debugging - image size is not a concern in the builder
RUN pip3 install uv 
RUN uv export --format requirements-txt > requirements.txt
RUN uv pip install wheel
RUN uv pip install -r requirements.txt
RUN rm -rf *.egg-info/ pyproject.toml uv.lock requirements.txt

# Copy application files (filtered by .dockerignore to exclude unnecessary files)
# .dockerignore prevents copying build artifacts, cache files, and secrets
COPY demos/ .

# Pre-compile our python packages to speed up initial hit
# and that the final image is read-only
# this is to ensure that we do not have to compile on first run
# we do both our app and included packages
RUN python -m compileall -q . && \
    python -m compileall -q ${VIRTUAL_ENV}/lib/python${DOCKER_PYTHON_VERSION}/site-packages

# FINAL STAGE: Create minimal runtime container
# slim-bookworm = Debian 12 (Bookworm) with minimal packages for smaller, more secure image
# This excludes build tools, compilers, and other unnecessary packages from the final image
FROM public.ecr.aws/docker/library/python:${DOCKER_PYTHON_VERSION}-slim-bookworm

# Import build arguments into final stage
ARG GID
ARG GROUP
ARG UID
ARG USER
ARG VIRTUAL_ENV

# Environment variables for runtime container
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}" 

# this is to ensure that we do not have to wait for the buffer to fill
# before we see the output in our logs
ENV PYTHONUNBUFFERED=1 

# do not write bytecode to disk
# this is to ensure that we do not have to write bytecode to disk
ENV PYTHONDONTWRITEBYTECODE=1

# Security: Create non-root user without shell access or home directory
# -s /sbin/nologin prevents shell access, -M prevents home directory creation
# This follows principle of least privilege - container runs with minimal permissions
RUN groupadd --gid ${GID} ${GROUP} && useradd -u ${UID} -g ${GID} -s /sbin/nologin -M ${USER}

# Update container and install minimal runtime dependencies
# curl: for health checks and debugging
# ca-certificates: required for HTTPS connections (awswrangler, AWS SDK)
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y curl ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy application files from builder stage
# Assign ownership to app user for security (non-root execution)
# This only brings over the compiled application, not build tools
COPY --from=builder --chown=${USER}:${GROUP} /app /app

# Copy virtual environment from builder stage
# Keep ownership as root (not app user) for security:
# - Virtual env contains system-wide packages that shouldn't be modified by app
# - Prevents application from tampering with its own dependencies
# - App user can read/execute but not modify the packages
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Security: Make filesystems read-only (555 = read+execute, no write)
# Prevents runtime modification of application code or dependencies
# This is a defense-in-depth security measure against code injection attacks
RUN chmod -R 555 /app && chmod -R 555 ${VIRTUAL_ENV}

# Switch to non-root user for security
# Container will run with minimal privileges, following principle of least privilege
USER ${USER}:${GROUP}

# Set final working directory for application execution
WORKDIR /app