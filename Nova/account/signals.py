from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Log, Producto, Venta  # Importa modelos relevantes

@receiver(post_save, sender=Producto)
def log_producto_change(sender, instance, created, **kwargs):
    accion = 'create' if created else 'update'
    Log.objects.create(
        usuario=None,  # Asumir None si no hay request.user; ajustar si usas middleware
        modelo='Producto',
        accion=accion,
        detalles=f'Producto {instance.nombre} {accion}d'
    )

@receiver(post_delete, sender=Producto)
def log_producto_delete(sender, instance, **kwargs):
    Log.objects.create(
        usuario=None,
        modelo='Producto',
        accion='delete',
        detalles=f'Producto {instance.nombre} deleted'
    )

# Repite para otros modelos como Venta, Kardex si es necesario