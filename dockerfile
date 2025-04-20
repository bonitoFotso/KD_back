FROM python:3.10-slim

# Définir les variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        netcat-openbsd \
        gcc \
        python3-dev \
        musl-dev \
        libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Installer les dépendances Python
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copier le projet
COPY . .

# Créer les répertoires nécessaires
RUN mkdir -p /app/staticfiles /app/mediafiles

# Utilisateur non-root pour la sécurité
RUN groupadd -r django && useradd -r -g django django
RUN chown -R django:django /app
USER django

# Exposer le port
EXPOSE 8000

# Vérifier que la base de données est disponible avant de démarrer l'application
COPY ./entrypoint.sh /
ENTRYPOINT ["sh", "/entrypoint.sh"]