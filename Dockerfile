FROM python:3.12-slim
ARG APP_VERSION=dev
ENV APP_VERSION=$APP_VERSION PYTHONUNBUFFERED=1
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
RUN useradd -r -u 10001 appuser && mkdir /data && chown appuser /data
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=15s CMD python -c "import urllib.request as u;u.urlopen('http://localhost:8000/health')"
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app.main:app"]
