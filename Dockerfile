FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY honeyjar.py .

# Default ports - override via env on real deploys
EXPOSE 22 23 80 445

CMD ["python", "honeyjar.py"]
