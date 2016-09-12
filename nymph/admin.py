from django.contrib import admin
from django.contrib.contenttypes.admin import GenericInlineModelAdmin, GenericTabularInline
from django.template.response import TemplateResponse
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import *
from django.conf.urls import url
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


# Define an inline admin descriptor for Employee model
# which acts a bit like a singleton
class UserProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'profile'


# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# Register your models here.
class NymphAdminSite(admin.AdminSite):
    site_title = "NYMPH"
    site_header = 'NYMPH'
    site_url = '/admin'
    index_title = 'Database Management'
    empty_value_display = 'unknown'


admin_site = NymphAdminSite(name='NYMPH', )
########################################################################################################################
# nuclide, element, material, material transection
########################################################################################################################
admin_site.register([Material,SymbolicMaterial,Fuel])


class ElementAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['atomic_num', 'symbol']}),
        ('Element information', {'fields': ['nameCH', 'nameEN'], 'classes': ['collapse']})
    ]
    search_fields = ('=symbol',)
    readonly_fields = ('atomic_num', 'symbol', 'nameCH', 'nameEN')
    list_display = ('atomic_num', 'symbol', 'nameCH', 'nameEN',)
    list_display_links = ('atomic_num', 'symbol', 'nameCH', 'nameEN')


admin_site.register(Element, ElementAdmin)


class WimsNuclideAdmin(ImportExportModelAdmin):
    list_display = (
        '__str__', 'element', 'id_wims', 'id_self_defined', 'amu', 'nf', 'material_type', 'description', 'res_trig',
        'dep_trig')
    ordering = ('element__atomic_num',)
    list_filter = ('nf', 'material_type',)
    search_fields = ('=id_wims', '=element__symbol', '=id_self_defined')
    raw_id_fields = ('element',)


admin_site.register(WimsNuclide, WimsNuclideAdmin)


class WmisElementCompositionInline(admin.TabularInline):
    model = WmisElementComposition
    extra = 0


class WmisElementAdmin(ImportExportModelAdmin):
    inlines = [WmisElementCompositionInline, ]
    list_display = ('__str__', 'get_nuclide_num',)
    search_fields = ('name',)


admin_site.register(WmisElement, WmisElementAdmin)


class BasicMaterialNumCompoInline(admin.TabularInline):
    model = BasicMaterialNumCompo
    extra = 2


class BasicMaterialWgtCompoInline(admin.TabularInline):
    model = BasicMaterialWgtCompo
    extra = 2


class BasicMaterialAdmin(admin.ModelAdmin):
    inlines = [BasicMaterialNumCompoInline, BasicMaterialWgtCompoInline]


admin_site.register(BasicMaterial, BasicMaterialAdmin)


class MixtureCompoInline(admin.TabularInline):
    model = MixtureCompo


class MixtureAdmin(admin.ModelAdmin):
    inlines = [MixtureCompoInline, ]

admin_site.register(Mixture, MixtureAdmin)


########################################################################################################################
# calculation
########################################################################################################################
class EgretFollowCaseInline(admin.TabularInline):
    model = EgretFollowCase


class EgretFollowTaskAdmin(admin.ModelAdmin):
    inlines = [EgretFollowCaseInline]
admin_site.register(EgretFollowTask, EgretFollowTaskAdmin)

class EgretSequenceCaseInline(admin.TabularInline):
    model = EgretSequenceCase

class EgretSequenceTaskAdmin(admin.ModelAdmin):
    inlines = [EgretSequenceCaseInline]
admin_site.register(EgretSequenceTask, EgretSequenceTaskAdmin)