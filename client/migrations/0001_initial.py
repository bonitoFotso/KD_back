# Generated by Django 5.1.4 on 2025-01-31 12:12

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Pays',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100, unique=True)),
                ('code_iso', models.CharField(max_length=3, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('nom', models.CharField(max_length=255)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('telephone', models.CharField(blank=True, max_length=15, null=True)),
                ('adresse', models.TextField(blank=True, null=True)),
                ('c_num', models.CharField(blank=True, max_length=10, null=True)),
                ('secteur_activite', models.CharField(blank=True, max_length=255, null=True, verbose_name="Secteur d'activité")),
                ('address', models.TextField(blank=True, null=True, verbose_name='Adresse')),
                ('bp', models.CharField(blank=True, max_length=10, null=True, verbose_name='Boîte Postale')),
                ('quartier', models.CharField(blank=True, max_length=255, null=True, verbose_name='Quartier')),
                ('matricule', models.CharField(blank=True, max_length=20, null=True, verbose_name='Matricule')),
                ('agreer', models.BooleanField(default=False, verbose_name='Agréé')),
                ('agreement_fournisseur', models.BooleanField(default=False, verbose_name='Agreement Fournisseur')),
                ('entite', models.CharField(blank=True, max_length=255, null=True, verbose_name='Entité')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100)),
                ('pays', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='regions', to='client.pays')),
            ],
        ),
        migrations.CreateModel(
            name='Ville',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100)),
                ('region', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='villes', to='client.region')),
            ],
        ),
        migrations.CreateModel(
            name='Site',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('nom', models.CharField(max_length=255)),
                ('localisation', models.CharField(blank=True, max_length=255, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('s_num', models.CharField(blank=True, max_length=10, null=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client.client')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL)),
                ('ville', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='client.ville')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=255, verbose_name='Nom')),
                ('prenom', models.CharField(blank=True, max_length=255, null=True, verbose_name='Prénom')),
                ('email', models.EmailField(blank=True, max_length=254, null=True, verbose_name='Email')),
                ('telephone', models.CharField(blank=True, max_length=15, null=True, verbose_name='Téléphone')),
                ('mobile', models.CharField(blank=True, max_length=15, null=True, verbose_name='Mobile')),
                ('poste', models.CharField(blank=True, max_length=255, null=True, verbose_name='Poste')),
                ('service', models.CharField(blank=True, max_length=255, null=True, verbose_name='Service')),
                ('role_achat', models.CharField(blank=True, max_length=255, null=True, verbose_name='Rôle dans les achats')),
                ('date_envoi', models.DateField(blank=True, null=True, verbose_name="Date d'envoi")),
                ('relance', models.BooleanField(default=False, verbose_name='Relance')),
                ('adresse', models.TextField(blank=True, null=True, verbose_name='Adresse')),
                ('quartier', models.CharField(blank=True, max_length=255, null=True, verbose_name='Quartier')),
                ('bp', models.CharField(blank=True, max_length=10, null=True, verbose_name='Boîte Postale')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='Notes supplémentaires')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Date de mise à jour')),
                ('client', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='contacts', to='client.client', verbose_name='Client associé')),
                ('ville', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='client.ville', verbose_name='Ville')),
            ],
            options={
                'verbose_name': 'Contact',
                'verbose_name_plural': 'Contacts',
            },
        ),
        migrations.AddField(
            model_name='client',
            name='ville',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='client.ville'),
        ),
    ]
