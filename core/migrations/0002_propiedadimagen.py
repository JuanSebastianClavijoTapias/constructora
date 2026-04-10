from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PropiedadImagen',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('imagen', models.ImageField(upload_to='propiedades/')),
                ('creada_en', models.DateTimeField(auto_now_add=True)),
                ('propiedad', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='imagenes', to='core.propiedad')),
            ],
            options={
                'ordering': ['creada_en', 'id'],
            },
        ),
    ]