# Generated by Django 5.1.6 on 2025-03-07 18:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion_cofrade', '0009_hermano_numero_hermano'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hermano',
            name='numero_hermano',
            field=models.IntegerField(),
        ),
    ]
