FROM python:3.11-slim

# Arbeitsverzeichnis
WORKDIR /app

# Kopiere nur requirements.txt zuerst, um Caching optimal zu nutzen
COPY requirements.txt .

# Systemabhängigkeiten installieren (besonders für GUI-Apps wie Tkinter)
RUN apt-get update && \
    apt-get install -y \
    python3-tk \
    libgl1-mesa-glx && \
    rm -rf /var/lib/apt/lists/*

# Python-Abhängigkeiten installieren
RUN pip install --no-cache-dir -r requirements.txt

# Restlichen Quellcode ins Image kopieren
COPY . .
COPY config.json . 

# Standard-Befehl definieren
CMD ["python", "webseitenscanner.py"]
