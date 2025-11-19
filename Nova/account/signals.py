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
    user = getattr(threading.current_thread(), 'user', None)
    accion = 'creó' if created else 'actualizó'
    Log.objects.create(
        usuario=user,
        modelo='Producto',
        accion=accion,
        detalles=f'Usuario {user.username if user else "desconocido"} {accion} producto "{instance.nombre}" (ID: {instance.id})'
    )
    logger.info(f'Producto "{instance.nombre}" fue {accion} por {user.username if user else "usuario desconocido"}')

@receiver(post_delete, sender=Producto)
def log_producto_delete(sender, instance, **kwargs):
    user = getattr(threading.current_thread(), 'user', None)
    Log.objects.create(
        usuario=user,
        modelo='Producto',
        accion='eliminó',
        detalles=f'Usuario {user.username if user else "desconocido"} eliminó producto "{instance.nombre}" (ID: {instance.id})'
    )
    logger.info(f'Producto "{instance.nombre}" fue eliminado por {user.username if user else "usuario desconocido"}')

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
    user = getattr(threading.current_thread(), 'user', None)
    accion = 'creó' if created else 'actualizó'
    Log.objects.create(
        usuario=user,
        modelo='Usuario',
        accion=accion,
        detalles=f'Usuario {user.username if user else "desconocido"} {accion} usuario "{instance.username}" (ID: {instance.id})'
    )
    logger.info(f'Usuario "{instance.username}" fue {accion} por {user.username if user else "usuario desconocido"}')

# Agrega más receivers para Rol, Almacen, Proveedor, Categoria si es necesario