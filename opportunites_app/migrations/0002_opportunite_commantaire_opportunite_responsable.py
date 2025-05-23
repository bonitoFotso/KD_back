# Generated by Django 5.1.4 on 2025-04-05 13:46

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opportunites_app', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='opportunite',
            name='commantaire',
            field=models.TextField(blank=True, null=True, verbose_name='Commentaire'),
        ),
        migrations.AddField(
            model_name='opportunite',
            name='responsable',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='opportunites_responsables', to=settings.AUTH_USER_MODEL, verbose_name='Responsable'),
            preserve_default=False,
        ),
    ]
