# Hafif bir Python imajı kullan
FROM python:3.10-slim

# Çalışma dizinini ayarla
WORKDIR /app

# Bağımlılıkları kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kodları kopyala
COPY ingestion.py .

# Container başladığında scripti çalıştır
CMD ["python", "ingestion.py"]