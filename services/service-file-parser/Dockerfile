FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y poppler-utils && rm -rf /var/lib/apt/lists/*

COPY ./services/service-file-parser/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-u", "-m", "services.service-file-parser.app.main"]
