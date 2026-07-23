import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '__first__'),
        ('dashboard', '0004_remove_town_province_delete_station_delete_province_and_more'),
    ]

    state_operations = [
        migrations.AlterField(
            model_name='invoice',
            name='customer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invoices', to='crm.customer', verbose_name='Cliente'),
        ),
        migrations.RemoveField(
            model_name='servicesubscription',
            name='customer',
        ),
        migrations.RemoveField(
            model_name='service',
            name='user',
        ),
        migrations.RemoveField(
            model_name='servicesubscription',
            name='service',
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='subscription',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invoice_items', to='crm.servicesubscription'),
        ),
        migrations.AlterField(
            model_name='contract',
            name='subscription',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='contract', to='crm.servicesubscription', verbose_name='Contrato'),
        ),
        migrations.AlterField(
            model_name='certificate',
            name='subscription',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='certificates', to='crm.servicesubscription', verbose_name='Suscripción'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='subscription',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invoices', to='crm.servicesubscription', verbose_name='Suscripción'),
        ),
        migrations.DeleteModel(
            name='Customer',
        ),
        migrations.DeleteModel(
            name='Service',
        ),
        migrations.DeleteModel(
            name='ServiceSubscription',
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=state_operations,
            database_operations=[],
        ),
    ]
