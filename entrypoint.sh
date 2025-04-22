#!/bin/sh

# Attendre que Postgres soit prêt
if [ "$DATABASE" = "postgres" ]
then
    echo "En attente de PostgreSQL..."
    
    while ! nc -z $DB_HOST $DB_PORT; do
      sleep 0.1
    done
    
    echo "PostgreSQL démarré"
fi

# Si vous avez besoin de charger des données initiales ffdfd
echo "Chargement des données initiales..."
python manage.py seed_client
python manage.py seed_docs



# Exécuter la commande fournie
exec "$@"