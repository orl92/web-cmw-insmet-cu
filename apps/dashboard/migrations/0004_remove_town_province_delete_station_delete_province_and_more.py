from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0003_alter_earlywarning_options_alter_invoiceitem_options_and_more'),
    ]

    state_operations = [
        migrations.RemoveField(
            model_name='town',
            name='province',
        ),
        migrations.DeleteModel(
            name='Station',
        ),
        migrations.DeleteModel(
            name='Province',
        ),
        migrations.DeleteModel(
            name='Town',
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=state_operations,
            database_operations=[],
        ),
    ]
