FROM python:3.11.14-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN groupadd --system carerisk \
    && useradd --system --gid carerisk --home-dir /app --no-create-home carerisk

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir --requirement /app/requirements.txt

COPY app.py /app/app.py
COPY carerisk_mvp/__init__.py /app/carerisk_mvp/__init__.py
COPY carerisk_mvp/content.py /app/carerisk_mvp/content.py
COPY carerisk_mvp/ui.py /app/carerisk_mvp/ui.py

RUN chown -R carerisk:carerisk /app
USER carerisk

EXPOSE 7860
CMD ["python", "app.py"]
