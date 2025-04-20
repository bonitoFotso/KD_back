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

# Exécuter la commande fournie
exec "$@"