# ---- Base image: Python 3.12 (Debian slim) ----
    FROM python:3.12-slim 
# doing modifs 


    # System deps some libs need (opencv/numpy etc.)
    RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
        && rm -rf /var/lib/apt/lists/*
    
    # Python runtime flags
    ENV PYTHONDONTWRITEBYTECODE=1 \
        PYTHONUNBUFFERED=1 \
        STREAMLIT_BROWSER_GATHERUSAGESTATS=false \
        PORT=8080
    
    # Workdir
    WORKDIR /app
    
    # Dependencies first (better layer caching)
    COPY requirements.txt /app/requirements.txt
    RUN pip install --no-cache-dir --upgrade pip \
     && pip install --no-cache-dir -r requirements.txt
    
    # Copy the rest of your code
    COPY . /app
    
    # Non-root user (Cloud Run best practice)
    RUN useradd -m appuser
    USER appuser
    
    # Expose for local runs (Cloud Run injects $PORT)
    EXPOSE 8080
    
    # Start Streamlit (bind to 0.0.0.0 and $PORT)
    CMD ["bash", "-lc", "python -m streamlit run app_v2.py --server.port=${PORT} --server.address=0.0.0.0 --server.headless=true --server.fileWatcherType=none"]
    