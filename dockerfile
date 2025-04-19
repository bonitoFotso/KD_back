FROM python:3.10-slim

# Définir le répertoire de travail
WORKDIR /app

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=core.settings

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copier le reste du code source
COPY . .

# Collecte des fichiers statiques
RUN python manage.py collectstatic --noinput

# Exposer le port sur lequel le serveur Django s'exécutera
EXPOSE 8000

# Commande pour lancer le serveur
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "core.wsgi:application"]

# Script pour migrations automatiques et démarrage
# Si vous préférez utiliser un script de démarrage personnalisé:
# COPY ./scripts/entrypoint.sh /
# RUN chmod +x /entrypoint.sh
# ENTRYPOINT ["/entrypoint.sh"]