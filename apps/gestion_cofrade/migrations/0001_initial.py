# Generated by Django 5.1.6 on 2025-03-06 10:06

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
            name='Cargo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cargo', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Cofradia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, unique=True)),
                ('descripcion', models.TextField()),
                ('color', models.CharField(help_text='Código HEX del color (ej: #ff5733)', max_length=7, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Estado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='FormaComunicacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='FormaPago',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Evento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('fecha', models.DateField()),
                ('tipo', models.CharField(choices=[('Ensayo', 'Ensayo'), ('Procesión', 'Procesión'), ('Reunión', 'Reunión')], max_length=50)),
                ('cofradia', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gestion_cofrade.cofradia')),
            ],
        ),
        migrations.CreateModel(
            name='Finanza',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('Ingreso', 'Ingreso'), ('Gasto', 'Gasto')], max_length=10)),
                ('monto', models.DecimalField(decimal_places=2, max_digits=10)),
                ('fecha', models.DateField(auto_now_add=True)),
                ('cofradia', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gestion_cofrade.cofradia')),
            ],
        ),
        migrations.CreateModel(
            name='Hermano',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dni', models.CharField(max_length=9, null=True)),
                ('nombre', models.CharField(max_length=100)),
                ('apellidos', models.CharField(max_length=100)),
                ('telefono', models.CharField(max_length=9, null=True)),
                ('direccion', models.CharField(max_length=255, null=True)),
                ('localidad', models.CharField(max_length=100)),
                ('fecha_nacimiento', models.DateField(null=True)),
                ('fecha_inicio', models.PositiveIntegerField(default=2025, null=True)),
                ('fecha_ultimo_pago', models.PositiveIntegerField(default=2025, null=True)),
                ('email', models.EmailField(max_length=254, null=True)),
                ('iban', models.CharField(max_length=24, null=True)),
                ('cuota_pendiente', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('cofradia', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gestion_cofrade.cofradia')),
                ('estado', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gestion_cofrade.estado')),
                ('forma_comunicacion', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gestion_cofrade.formacomunicacion')),
                ('forma_pago', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gestion_cofrade.formapago')),
            ],
        ),
        migrations.CreateModel(
            name='AuditoriaHermano',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('accion', models.CharField(choices=[('CREAR', 'Crear'), ('MODIFICAR', 'Modificar'), ('ELIMINAR', 'Eliminar')], max_length=10)),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('usuario', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('hermano', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gestion_cofrade.hermano')),
            ],
        ),
        migrations.CreateModel(
            name='PerfilUsuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cargo', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gestion_cofrade.cargo')),
                ('cofradia', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='gestion_cofrade.cofradia')),
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Tarea',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=200)),
                ('descripcion', models.TextField(blank=True, null=True)),
                ('asignado_a', models.CharField(max_length=200)),
                ('fecha_limite', models.DateField()),
                ('estado', models.CharField(choices=[('Pendiente', 'Pendiente'), ('En Proceso', 'En Proceso'), ('Completada', 'Completada'), ('Atrasada', 'Atrasada')], default='Pendiente', max_length=20)),
                ('prioridad', models.CharField(choices=[('Baja', 'Baja'), ('Media', 'Media'), ('Alta', 'Alta')], default='Media', max_length=10)),
                ('cofradia', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gestion_cofrade.cofradia')),
            ],
        ),
    ]
