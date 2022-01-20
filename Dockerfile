FROM python:3.10.2-slim

WORKDIR /usr/src/app

RUN apt-get update && \
    apt-get install exiftool ffmpeg -y && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./app.py" ]
