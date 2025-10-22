# ---- Base image: Python 3.12 (Debian slim) ----
    FROM python:3.12-slim

    # System deps (OpenCV runtime) + ffmpeg for reliable MP4 writing
    RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
        ffmpeg \
     && rm -rf /var/lib/apt/lists/*
    
    # Runtime env
    ENV PYTHONDONTWRITEBYTECODE=1 \
        PYTHONUNBUFFERED=1 \
        STREAMLIT_BROWSER_GATHERUSAGESTATS=false \
        PORT=8080 \
        VIDEO_DIR=/tmp/video
    
    # Workdir
    WORKDIR /app
    
    # Dependencies first (layer caching)
    COPY requirements.txt /app/requirements.txt
    RUN pip install --no-cache-dir --upgrade pip \
     && pip install --no-cache-dir -r requirements.txt
    # Tip: prefer opencv-python-headless in requirements to slim the image
    
    # Copy code
    COPY . /app
    
    # Non-root user + ensure writable app dir (if you still write under /app)
    RUN useradd -m appuser && chown -R appuser:appuser /app
    USER appuser
    
    # Expose for local debugging (Cloud Run injects $PORT automatically)
    EXPOSE 8080
    
    # Start Streamlit
    CMD ["bash", "-lc", "python -m streamlit run app.py --server.port=${PORT} --server.address=0.0.0.0 --server.headless=true --server.fileWatcherType=none"]
    