FROM python:3.9-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système
RUN apt-get update && \
    apt-get install -y \
        build-essential \
        wget \
        ca-certificates \
        libpq-dev \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Installer ta-lib depuis la source
RUN cd /tmp && \
    wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xvzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib/ && \
    wget http://git.savannah.gnu.org/cgit/config.git/plain/config.guess -O config.guess && \
    wget http://git.savannah.gnu.org/cgit/config.git/plain/config.sub -O config.sub && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib-0.4.0-src.tar.gz ta-lib/

# Copier les fichiers requirements et installer les dépendances
COPY requirements.txt .
RUN apt-get update && \
    apt-get install -y build-essential wget && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir numpy==1.21.6 Cython==3.0.0 wheel && \
    wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xvzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib/ && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib-0.4.0-src.tar.gz ta-lib/ && \
    pip install --no-cache-dir -r requirements.txt

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Créer le répertoire pour les données
RUN mkdir -p /app/data

# Exposer le port
EXPOSE 8000

# Commande par défaut
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
