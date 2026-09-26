# Kage 🖤 userbot
# Code lives in the image (/app), your session, config and modules in the /data volume.
FROM python:3.13-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DOCKER=true \
    GIT_PYTHON_REFRESH=quiet \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH

# Runtime libs used by popular modules (media, images, file types) + build tools for their wheels
RUN apt-get update && apt-get install --no-install-recommends -y \
        build-essential \
        ffmpeg \
        git \
        libcairo2 \
        libmagic1 \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Unprivileged user; the venv is theirs so modules can `# requires:` extra packages at runtime
RUN useradd --create-home --uid 1000 kage \
    && python -m venv /opt/venv \
    && mkdir -p /data /app \
    && chown -R kage:kage /opt/venv /data /app

USER kage
WORKDIR /app

COPY --chown=kage:kage requirements.txt .
RUN pip install --no-cache-dir --no-warn-script-location -r requirements.txt

COPY --chown=kage:kage . .

VOLUME ["/data"]

# The bot rewrites /data/.heartbeat every 30s while Telegram is connected.
# The long start period covers the first interactive login.
HEALTHCHECK --interval=60s --timeout=10s --start-period=10m --retries=3 \
    CMD ["python", "-m", "kage._health"]

CMD ["python", "-m", "kage"]
