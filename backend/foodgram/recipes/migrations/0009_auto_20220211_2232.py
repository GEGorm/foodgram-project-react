# Generated by Django 2.2.16 on 2022-02-11 19:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0008_auto_20220211_0304'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredient',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]