# 1️⃣ Utiliser l'image officielle de Python
FROM python:3.12.2

# 2️⃣ Définir le répertoire de travail
WORKDIR /app

# 3️⃣ Copier tous les fichiers du projet dans le conteneur
COPY . .

# 4️⃣ Installer les dépendances
RUN pip install --no-cache-dir --upgrade pip && \
    pip install -r requirements.txt

# 5️⃣ Exposer le port 8000
EXPOSE 8000

# Installer les dépendances nécessaires
RUN apt-get update && apt-get install -y \
    wget unzip curl \
    libnss3 libx11-xcb1 libxcomposite1 libxcursor1 libxi6 libxrandr2 libasound2 libatk1.0-0 libgtk-3-0

# Installer Google Chrome stable
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable


# 7️⃣ Lancer l'application FastAPI avec Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
