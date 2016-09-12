# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-08-30 05:32
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='BasicMaterial',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('remark', models.TextField(blank=True)),
                ('time_inserted', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=16, unique=True)),
                ('density', models.DecimalField(decimal_places=5, help_text='unit:g/cm3', max_digits=10)),
                ('input_type', models.PositiveSmallIntegerField(choices=[(1, 'by number'), (2, 'by weight percent')], default=1)),
            ],
            options={
                'db_table': 'basic_material',
            },
        ),
        migrations.CreateModel(
            name='BasicMaterialNumCompo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('element_number', models.PositiveSmallIntegerField()),
                ('basic_material', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='num_compo', to='nymph.BasicMaterial')),
            ],
            options={
                'db_table': 'basic_material_num_compo',
            },
        ),
        migrations.CreateModel(
            name='BasicMaterialWgtCompo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weight_percent', models.DecimalField(decimal_places=5, help_text='%', max_digits=10, validators=[django.core.validators.MaxValueValidator(100), django.core.validators.MinValueValidator(0)])),
                ('basic_material', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wgt_compo', to='nymph.BasicMaterial')),
            ],
            options={
                'db_table': 'basic_material_wgt_compo',
            },
        ),
        migrations.CreateModel(
            name='Element',
            fields=[
                ('atomic_num', models.PositiveSmallIntegerField(primary_key=True, serialize=False, verbose_name='Atomic number')),
                ('symbol', models.CharField(max_length=8, unique=True)),
                ('nameCH', models.CharField(max_length=8, verbose_name='Chinese name')),
                ('nameEN', models.CharField(max_length=40, verbose_name='English name')),
            ],
            options={
                'ordering': ['atomic_num'],
                'db_table': 'element',
            },
        ),
        migrations.CreateModel(
            name='Material',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tag', models.SlugField()),
                ('object_id', models.PositiveIntegerField(editable=False)),
                ('content_type', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
            ],
            options={
                'db_table': 'material',
            },
        ),
        migrations.CreateModel(
            name='Mixture',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('remark', models.TextField(blank=True)),
                ('time_inserted', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=16, unique=True)),
            ],
            options={
                'db_table': 'mixture',
            },
        ),
        migrations.CreateModel(
            name='MixtureCompo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weight_percent', models.DecimalField(decimal_places=5, help_text='unit:%', max_digits=10, validators=[django.core.validators.MaxValueValidator(100), django.core.validators.MinValueValidator(0)])),
                ('basic_material', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='nymph.BasicMaterial')),
                ('mixture', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='compo', to='nymph.Mixture')),
            ],
            options={
                'db_table': 'mixture_compo',
            },
        ),
        migrations.CreateModel(
            name='WimsNuclide',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nuclide_name', models.CharField(max_length=30)),
                ('id_wims', models.PositiveIntegerField(blank=True, null=True, unique=True)),
                ('id_self_defined', models.PositiveIntegerField(blank=True, null=True, unique=True)),
                ('amu', models.DecimalField(decimal_places=6, max_digits=9, validators=[django.core.validators.MinValueValidator(0)])),
                ('nf', models.PositiveSmallIntegerField(choices=[(0, '无共振积分表'), (1, '有共振积分表的非裂变核'), (2, '有共振吸收共振积分表的可裂变核'), (3, '有共振吸收和共振裂变共振积分表的可裂变核'), (4, '没有共振积分表的可裂变核')])),
                ('material_type', models.CharField(choices=[('M', '慢化剂'), ('FP', '裂变产物'), ('A', '锕系核素'), ('B', '可燃核素'), ('D', '用于剂量的材料'), ('S', '结构材料和其他'), ('B/FP', '可燃核素 /裂变产物')], max_length=4)),
                ('description', models.CharField(max_length=50)),
                ('element', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='nymph.Element')),
            ],
            options={
                'db_table': 'wims_nuclide',
            },
        ),
        migrations.CreateModel(
            name='WmisElement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
            ],
            options={
                'ordering': ['name'],
                'db_table': 'wmis_element',
            },
        ),
        migrations.CreateModel(
            name='WmisElementComposition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weight_percent', models.DecimalField(decimal_places=6, help_text='unit:%', max_digits=9, validators=[django.core.validators.MaxValueValidator(100), django.core.validators.MinValueValidator(0)])),
                ('wmis_element', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='composition', to='nymph.WmisElement')),
                ('wmis_nuclide', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='nymph.WimsNuclide')),
            ],
            options={
                'db_table': 'wmis_element_composition',
            },
        ),
        migrations.AddField(
            model_name='wmiselement',
            name='wmis_nuclides',
            field=models.ManyToManyField(through='nymph.WmisElementComposition', to='nymph.WimsNuclide'),
        ),
        migrations.AddField(
            model_name='mixture',
            name='basic_materials',
            field=models.ManyToManyField(through='nymph.MixtureCompo', to='nymph.BasicMaterial'),
        ),
        migrations.AddField(
            model_name='basicmaterialwgtcompo',
            name='element',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='nymph.WmisElement'),
        ),
        migrations.AddField(
            model_name='basicmaterialnumcompo',
            name='element',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='nymph.WmisElement'),
        ),
        migrations.AlterOrderWithRespectTo(
            name='basicmaterialwgtcompo',
            order_with_respect_to='basic_material',
        ),
        migrations.AlterOrderWithRespectTo(
            name='basicmaterialnumcompo',
            order_with_respect_to='basic_material',
        ),
    ]
