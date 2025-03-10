# Generated by Django 5.1.6 on 2025-03-07 08:55

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion_cofrade', '0003_auditoriahermano_detalles_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='notificacion',
            options={},
        ),
        migrations.RenameField(
            model_name='notificacion',
            old_name='leida',
            new_name='enviado',
        ),
        migrations.RenameField(
            model_name='notificacion',
            old_name='fecha_creacion',
            new_name='fecha_envio',
        ),
        migrations.RemoveField(
            model_name='notificacion',
            name='fecha_evento',
        ),
        migrations.RemoveField(
            model_name='notificacion',
            name='tipo',
        ),
        migrations.AlterField(
            model_name='notificacion',
            name='usuario',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
