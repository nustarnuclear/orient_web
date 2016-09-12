# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-08-31 05:50
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nymph', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssemblyPosition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('row', models.PositiveSmallIntegerField()),
                ('column', models.PositiveSmallIntegerField()),
                ('position_type', models.PositiveSmallIntegerField(choices=[(1, 'fuel element'), (2, 'guide tube'), (3, 'instrument tube')], default=1)),
            ],
            options={
                'db_table': 'assembly_position',
            },
        ),
        migrations.CreateModel(
            name='AssemblyPositionPattern',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('remark', models.TextField(blank=True)),
                ('time_inserted', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('side_pin_num', models.PositiveSmallIntegerField()),
                ('guide_tube_type', models.PositiveSmallIntegerField(choices=[(1, '1*1'), (2, '2*2')], default=1)),
            ],
            options={
                'db_table': 'assembly_position_pattern',
            },
        ),
        migrations.CreateModel(
            name='ReactorPosition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('row', models.PositiveSmallIntegerField()),
                ('column', models.PositiveSmallIntegerField()),
            ],
            options={
                'db_table': 'reactor_position',
            },
        ),
        migrations.CreateModel(
            name='ReactorPositionPattern',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('remark', models.TextField(blank=True)),
                ('time_inserted', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('side_ass_num', models.PositiveSmallIntegerField()),
            ],
            options={
                'db_table': 'reactor_position_pattern',
            },
        ),
        migrations.AddField(
            model_name='reactorposition',
            name='pattern',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='nymph.ReactorPositionPattern'),
        ),
        migrations.AddField(
            model_name='assemblyposition',
            name='pattern',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='nymph.AssemblyPositionPattern'),
        ),
    ]