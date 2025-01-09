#FROM python:3.12.7-slim
#
#WORKDIR /app
#
#COPY . .
#
#RUN apt-get update && \
#    apt-get install -y tzdata \
#    libpq-dev postgresql-client && \
#    pip install --no-cache-dir -r requirements.txt
#
#RUN ln -fs /usr/share/zoneinfo/Asia/Moscow /etc/localtime && \
#    dpkg-reconfigure --frontend noninteractive tzdata
#
#CMD ["python", "-m", "main"]

FROM python:3.12.7-slim

WORKDIR /app

COPY . .

RUN apt-get update && \
    apt-get install -y tzdata \
    libpq-dev postgresql-client && \
    pip install --no-cache-dir uv

RUN ln -fs /usr/share/zoneinfo/Asia/Moscow /etc/localtime && \
    dpkg-reconfigure --frontend noninteractive tzdata

RUN uv install

CMD ["python", "-m", "main"]
