# Generated by Django 5.1.6 on 2025-02-26 13:36

import django.db.models.deletion
import django.db.models.query
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion_cofradia', '0006_alter_hermano_cofradia_alter_hermano_estado_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='hermano',
            old_name='apellido',
            new_name='apellidos',
        ),
        migrations.AlterField(
            model_name='hermano',
            name='cofradia',
            field=models.ForeignKey(default=django.db.models.query.QuerySet.first, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gestion_cofradia.cofradia'),
        ),
        migrations.AlterField(
            model_name='hermano',
            name='estado',
            field=models.ForeignKey(default=django.db.models.query.QuerySet.first, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gestion_cofradia.estado'),
        ),
        migrations.AlterField(
            model_name='hermano',
            name='forma_comunicacion',
            field=models.ForeignKey(default=django.db.models.query.QuerySet.first, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gestion_cofradia.formacomunicacion'),
        ),
        migrations.AlterField(
            model_name='hermano',
            name='forma_pago',
            field=models.ForeignKey(default=django.db.models.query.QuerySet.first, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gestion_cofradia.formapago'),
        ),
    ]
