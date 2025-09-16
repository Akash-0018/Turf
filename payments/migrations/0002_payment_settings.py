from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('qr_code', models.ImageField(help_text='QR code image for payments', upload_to='payment_qr/')),
                ('upi_id', models.CharField(help_text='UPI ID for direct payments', max_length=255)),
                ('merchant_name', models.CharField(help_text='Merchant name for UPI payments', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Payment Setting',
                'verbose_name_plural': 'Payment Settings',
            },
        ),
        migrations.AddField(
            model_name='payment',
            name='payment_proof',
            field=models.ImageField(blank=True, null=True, upload_to='payment_proofs/'),
        ),
    ]