FROM nvidia/cuda:12.2.0-base-ubuntu22.04

WORKDIR /app

# Instalación del sistema
RUN apt-get update && apt-get install -y \
    python3 python3-pip git ffmpeg libsm6 libxext6 curl && \
    apt-get clean

COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt

COPY . .

CMD ["python3", "main.py"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]