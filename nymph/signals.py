from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import BasicMaterial,Mixture,Material,SymbolicMaterial


@receiver(post_save,sender=BasicMaterial)
@receiver(post_save,sender=Mixture)
@receiver(post_save,sender=SymbolicMaterial)
def create_material(sender, instance, created=False, **kwargs):
    if created:
        Material.objects.create(content_object=instance)