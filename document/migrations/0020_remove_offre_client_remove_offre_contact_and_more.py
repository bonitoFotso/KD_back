# Generated by Django 5.1.4 on 2025-03-10 19:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('document', '0019_alter_opportunite_statut'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='offre',
            name='client',
        ),
        migrations.RemoveField(
            model_name='offre',
            name='contact',
        ),
        migrations.RemoveField(
            model_name='offre',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='offre',
            name='entity',
        ),
        migrations.RemoveField(
            model_name='offre',
            name='produit',
        ),
        migrations.RemoveField(
            model_name='offre',
            name='produits',
        ),
    ]
