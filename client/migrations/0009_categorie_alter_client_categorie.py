# Generated by Django 5.1.4 on 2025-02-18 10:11

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0008_alter_client_bp_alter_contact_mobile'),
    ]

    operations = [
        migrations.CreateModel(
            name='Categorie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(choices=[('PME', 'PME'), ('TPE', 'TPE'), ('PE', 'PE'), ('GE', 'GE')], max_length=255)),
            ],
        ),
        migrations.AlterField(
            model_name='client',
            name='categorie',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='client.categorie', verbose_name='Catégorie'),
        ),
    ]
