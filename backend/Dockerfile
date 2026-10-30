FROM python:3.11-slim
WORKDIR /srv
COPY backend/requirements.docker.txt /srv/backend/requirements.docker.txt
RUN pip install --no-cache-dir -r /srv/backend/requirements.docker.txt
COPY backend /srv/backend
COPY ml /srv/ml
COPY database /srv/database
WORKDIR /srv/backend
EXPOSE 8001
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
