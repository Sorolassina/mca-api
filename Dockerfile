# 1️⃣ Utiliser l'image officielle de Python
FROM python:3.13.2

# 2️⃣ Définir le répertoire de travail
WORKDIR /app

# 3️⃣ Mise à jour et installation des bibliothèques système en premier
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    libcairo2 \
    libpango-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libjpeg-dev \
    zlib1g-dev \
    shared-mime-info \
    libnss3 libx11-xcb1 libxcomposite1 libxcursor1 libxi6 libxrandr2 \
    libasound2 libatk1.0-0 libgtk-3-0 \
    curl wget gnupg \
    && rm -rf /var/lib/apt/lists/*
    
# Installer Google Chrome stable
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable

# 3️⃣ Copier tous les fichiers du projet dans le conteneur
COPY . .

# 6️⃣ Installer les dépendances Python
RUN pip install --no-cache-dir --upgrade pip
#RUN pip install -r requirements-light.txt
RUN cat requirements-light.txt && pip install -r requirements-light.txt
 
# 5️⃣ Exposer le port 8080
EXPOSE 8080

# 7️⃣ Lancer l'application FastAPI avec Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
