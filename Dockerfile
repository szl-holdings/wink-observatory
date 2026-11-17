FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 GRADIO_ANALYTICS_ENABLED=False HF_HUB_DISABLE_TELEMETRY=1
WORKDIR /workspace
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip check
COPY app.py .
COPY backend/ ./backend/
COPY data/ ./data/
COPY SOURCE_REVISION ./SOURCE_REVISION
RUN useradd --create-home --uid 1000 wink && chown -R wink:wink /workspace
USER wink
EXPOSE 7860
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","7860","--workers","1"]
