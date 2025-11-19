from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from .models import Log, Producto, Venta, Usuario, Rol, Almacen, Proveedor, Categoria
import logging
import threading

logger = logging.getLogger(__name__)

# Logs de sesión
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    Log.objects.create(
        usuario=user,
        modelo='Sesión',
        accion='login',
        detalles=f'Usuario {user.username} inició sesión desde {request.META.get("REMOTE_ADDR", "IP desconocida")}'
    )
    logger.info(f'Usuario {user.username} inició sesión el {user.last_login}')

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    Log.objects.create(
        usuario=user,
        modelo='Sesión',
        accion='logout',
        detalles=f'Usuario {user.username} cerró sesión'
    )
    logger.info(f'Usuario {user.username} cerró sesión')

# Logs de acciones en modelos
@receiver(post_save, sender=Producto)
def log_producto_change(sender, instance, created, **kwargs):
    accion = 'creó' if created else 'actualizó'
    Log.objects.create(
        user = getattr(threading.current_thread(), 'user', None),  # Asumir None; usa request.user si tienes middleware
        modelo='Producto',
        accion=accion,
        detalles=f'Usuario actualizó producto "{instance.nombre}" (ID: {instance.id}) - Acción: {accion}'
    )
    logger.info(f'Producto "{instance.nombre}" fue {accion} por usuario desconocido')

@receiver(post_delete, sender=Producto)
def log_producto_delete(sender, instance, **kwargs):
    Log.objects.create(
        usuario=None,
        modelo='Producto',
        accion='eliminó',
        detalles=f'Producto "{instance.nombre}" (ID: {instance.id}) fue eliminado'
    )
    logger.info(f'Producto "{instance.nombre}" fue eliminado')

# Repite para otros modelos
@receiver(post_save, sender=Venta)
def log_venta_change(sender, instance, created, **kwargs):
    accion = 'creó' if created else 'actualizó'
    Log.objects.create(
        usuario=instance.usuario,
        modelo='Venta',
        accion=accion,
        detalles=f'Venta ID {instance.id} por {instance.usuario.username} - Total: ${instance.total} - Acción: {accion}'
    )
    logger.info(f'Venta ID {instance.id} fue {accion} por {instance.usuario.username}')

@receiver(post_save, sender=Usuario)
def log_usuario_change(sender, instance, created, **kwargs):
    accion = 'creó' if created else 'actualizó'
    Log.objects.create(
        usuario=None,
        modelo='Usuario',
        accion=accion,
        detalles=f'Usuario "{instance.username}" (ID: {instance.id}) fue {accion}'
    )
    logger.info(f'Usuario "{instance.username}" fue {accion}')

# Agrega más receivers para Rol, Almacen, Proveedor, Categoria si es necesario