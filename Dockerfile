FROM python:3.12-slim

WORKDIR /app/backend

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend/ /app/backend/

ENV DATABASE_URL=sqlite+aiosqlite:////data/data.db
ENV PYTHONPATH=/app/backend

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
