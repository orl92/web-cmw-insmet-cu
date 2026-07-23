import django.core.validators
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    state_operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('record_active', models.BooleanField(default=True, verbose_name='Registro activo')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='Fecha de eliminación')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('client_type', models.CharField(choices=[('natural', 'Persona Natural'), ('juridica', 'Persona Jurídica')], default='juridica', max_length=8, verbose_name='Tipo de Cliente')),
                ('company_name', models.CharField(blank=True, max_length=100, null=True, verbose_name='Nombre de la Empresa')),
                ('reeup', models.CharField(blank=True, max_length=12, null=True, validators=[django.core.validators.RegexValidator(message='El REEUP debe tener el formato ###.#.####, ###.#.#####, ###.##.#### o ###.##.#####', regex='^\\d{3}\\.\\d{1,2}\\.\\d{4,5}$')], verbose_name='REEUP')),
                ('nit', models.CharField(blank=True, max_length=11, null=True, validators=[django.core.validators.RegexValidator(message='El NIT debe estar compuesto por 11 dígitos numéricos.', regex='^\\d{11}$')], verbose_name='NIT')),
                ('account', models.CharField(max_length=16, validators=[django.core.validators.RegexValidator(message='La cuenta bancaria debe tener 16 dígitos numéricos.', regex='^\\d{16}$')], verbose_name='Cuenta Bancaria')),
                ('agency_bank', models.CharField(blank=True, max_length=100, null=True, verbose_name='Agencia Bancaria')),
                ('address', models.TextField(verbose_name='Dirección')),
                ('phone', models.CharField(max_length=8, validators=[django.core.validators.RegexValidator(message='El número de teléfono debe tener 8 dígitos (sin espacios ni guiones).', regex='^\\d{8}$')], verbose_name='Número de Teléfono')),
                ('accept_terms', models.BooleanField(default=False, verbose_name='Aceptó Términos')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Usuario')),
            ],
            options={
                'verbose_name': 'Cliente',
                'verbose_name_plural': 'Clientes',
                'db_table': 'dashboard_customer',
                'permissions': (('view_customer', 'Ver'), ('add_customer', 'Añadir'), ('change_customer', 'Editar'), ('delete_customer', 'Eliminar')),
                'default_permissions': (),
            },
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('record_active', models.BooleanField(default=True, verbose_name='Registro activo')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='Fecha de eliminación')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='Fecha')),
                ('title', models.CharField(max_length=100, verbose_name='Título')),
                ('summary', models.CharField(max_length=500, verbose_name='Resumen')),
                ('service_type', models.CharField(choices=[('public', 'Público'), ('commercial', 'Comercial')], default='public', max_length=10, verbose_name='Tipo de Servicio')),
                ('pdf', models.FileField(blank=True, null=True, upload_to='services/pdfs/', verbose_name='Archivo PDF')),
                ('image', models.ImageField(blank=True, null=True, upload_to='services/images/', verbose_name='Imagen')),
                ('code', models.CharField(blank=True, max_length=50, null=True, unique=True, verbose_name='Código del servicio')),
                ('price', models.DecimalField(blank=True, decimal_places=2, help_text='Precio unitario del servicio', max_digits=10, null=True, verbose_name='Precio (CUP)')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_services', to=settings.AUTH_USER_MODEL, verbose_name='Usuario')),
            ],
            options={
                'verbose_name': 'Servicio',
                'verbose_name_plural': 'Servicios',
                'db_table': 'dashboard_service',
                'permissions': (('view_service', 'Ver'), ('add_service', 'Añadir'), ('change_service', 'Editar'), ('delete_service', 'Eliminar')),
                'default_permissions': (),
            },
        ),
        migrations.CreateModel(
            name='ServiceSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('record_active', models.BooleanField(default=True, verbose_name='Registro activo')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='Fecha de eliminación')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('start_date', models.DateTimeField(blank=True, null=True, verbose_name='Fecha de inicio')),
                ('end_date', models.DateTimeField(blank=True, null=True, verbose_name='Fecha de expiración')),
                ('payment_status', models.CharField(choices=[('requested', 'Solicitado'), ('pending', 'Pendiente de pago'), ('paid', 'Pagado'), ('expired', 'Expirado')], default='requested', max_length=20, verbose_name='Estado de pago')),
                ('payment_method', models.CharField(blank=True, choices=[('qr', 'Pago por Código QR'), ('transfer', 'Transferencia Bancaria'), ('presencial', 'Pago Presencial')], max_length=20, null=True, verbose_name='Método de pago')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crm.customer', verbose_name='Cliente')),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crm.service', verbose_name='Servicio')),
            ],
            options={
                'verbose_name': 'Suscripción de servicio',
                'verbose_name_plural': 'Suscripciones de servicios',
                'db_table': 'dashboard_servicesubscription',
                'permissions': (('view_subscription', 'Ver'), ('add_subscription', 'Añadir'), ('change_subscription', 'Editar'), ('delete_subscription', 'Eliminar')),
                'default_permissions': (),
            },
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=state_operations,
            database_operations=[],
        ),
    ]
