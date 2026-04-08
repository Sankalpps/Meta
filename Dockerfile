FROM python:3.11-slim

# OpenEnv Intersection: 3-way traffic control with emergency vehicle prioritization
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app/src
EXPOSE 7860

CMD ["uvicorn", "openenv_intersection.app:app", "--host", "0.0.0.0", "--port", "7860"]
