FROM python:3.11-slim

WORKDIR /app

COPY ./services/service-ai-analyzer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-u", "-m", "services.service-ai-analyzer.app.main"]
