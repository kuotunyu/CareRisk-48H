FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1

RUN apt-get update \
    && apt-get install --no-install-recommends -y libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY pyproject.toml README.md LICENSE NOTICE ./
COPY src ./src
COPY app ./app
COPY app.py ./app.py
RUN pip install --no-cache-dir ".[app,tabular]"

EXPOSE 7860
CMD ["python", "app.py"]
