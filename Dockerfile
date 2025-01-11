FROM python:3.12.7-slim

# Install dependencies for PostgreSQL
RUN apt-get update && \
    apt-get install -y gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN apt-get update && \
    apt-get install -y tzdata \
    libpq-dev postgresql-client && \
    pip install --no-cache-dir -r requirements.txt

RUN ln -fs /usr/share/zoneinfo/Asia/Moscow /etc/localtime && \
    dpkg-reconfigure --frontend noninteractive tzdata

CMD ["python", "-m", "main"]