# Image that runs the DataStrap dashboard on the built-in DEMO data.
# The dashboard server (serve.py) only uses Python's standard library,
# so no pip packages are needed here: smaller image, fewer security findings.
FROM python:3.12.11-slim-bookworm

# Settings you can change when starting the container (docker run -e PORT=9000 ...)
#  HOST=0.0.0.0 lets the port be reached from outside the container (serve.py defaults to 127.0.0.1)
#  PORT is the port the server listens on inside the container
ENV HOST=0.0.0.0 \
    PORT=8080 \
    PYTHONUNBUFFERED=1

# Install the operating system's latest security patches (a pinned base image gets older every week;
# without this, the Trivy scan in the pipeline would find known holes in it).
RUN apt-get update \
 && apt-get upgrade -y --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*

# Run as a normal user instead of root, so a bug cannot damage the container.
RUN useradd --create-home --uid 10001 appuser

WORKDIR /app

# Copy only the files the dashboard needs (serve.py only serves a fixed list of files anyway).
COPY --chown=appuser:appuser serve.py index.html app.js styles.css icons.js demo_data.json placeholder-man.webp placeholder-woman.webp ./

USER 10001

# serve.py refuses requests whose Host port differs from its own port,
# so publish the SAME number on both sides: docker run -e PORT=8080 -p 8080:8080 ...
EXPOSE 8080

# Docker asks "are you healthy?" every 10 s by fetching the home page.
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/' % os.environ['PORT'], timeout=2)"]

# --no-browser: there is no browser inside a container. "exec" makes Python PID 1 so docker stop works fast.
CMD ["sh", "-c", "exec python serve.py --port ${PORT} --no-browser"]
