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
        modelo='logs',  # Cambiado a módulo principal
        accion='login',
        detalles=f'Usuario {user.username} inició sesión desde {request.META.get("REMOTE_ADDR", "IP desconocida")}'
    )
    logger.info(f'Usuario {user.username} inició sesión el {user.last_login}')

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    Log.objects.create(
        usuario=user,
        modelo='logs',  # Cambiado a módulo principal
        accion='logout',
        detalles=f'Usuario {user.username} cerró sesión'
    )
    logger.info(f'Usuario {user.username} cerró sesión')

# Logs para Producto
@receiver(post_save, sender=Producto)
def log_producto_change(sender, instance, created, **kwargs):
    user = getattr(threading.current_thread(), 'user', None)
    accion = 'crear' if created else 'actualizar'
    Log.objects.create(
        usuario=user,
        modelo='productos',  # Cambiado a módulo principal
        accion=accion,
        detalles=f'Usuario {user.username if user else "desconocido"} {accion} producto "{instance.nombre}" (ID: {instance.id})'
    )
    logger.info(f'Producto "{instance.nombre}" fue {accion} por {user.username if user else "usuario desconocido"}')

@receiver(post_delete, sender=Producto)
def log_producto_delete(sender, instance, **kwargs):
    user = getattr(threading.current_thread(), 'user', None)
    Log.objects.create(
        usuario=user,
        modelo='productos',  # Cambiado a módulo principal
        accion='eliminar',
        detalles=f'Usuario {user.username if user else "desconocido"} eliminó producto "{instance.nombre}" (ID: {instance.id})'
    )
    logger.info(f'Producto "{instance.nombre}" fue eliminado por {user.username if user else "usuario desconocido"}')

# Logs para Venta
@receiver(post_save, sender=Venta)
def log_venta_change(sender, instance, created, **kwargs):
    accion = 'crear' if created else 'actualizar'
    Log.objects.create(
        usuario=instance.usuario,
        modelo='ventas',  # Cambiado a módulo principal
        accion=accion,
        detalles=f'Venta ID {instance.id} por {instance.usuario.username} - Total: ${instance.total} - Acción: {accion}'
    )
    logger.info(f'Venta ID {instance.id} fue {accion} por {instance.usuario.username}')

@receiver(post_delete, sender=Venta)
def log_venta_delete(sender, instance, **kwargs):
    user = getattr(threading.current_thread(), 'user', None)
    Log.objects.create(
        usuario=user,
        modelo='ventas',  # Cambiado a módulo principal
        accion='eliminar',
        detalles=f'Usuario {user.username if user else "desconocido"} eliminó venta ID {instance.id}'
    )
    logger.info(f'Venta ID {instance.id} fue eliminada por {user.username if user else "usuario desconocido"}')

# Logs para Usuario
@receiver(post_save, sender=Usuario)
def log_usuario_change(sender, instance, created, **kwargs):
    user = getattr(threading.current_thread(), 'user', None)
    accion = 'crear' if created else 'actualizar'
    Log.objects.create(
        usuario=user,
        modelo='usuarios',  # Cambiado a módulo principal
        accion=accion,
        detalles=f'Usuario {user.username if user else "desconocido"} {accion} usuario "{instance.username}" (ID: {instance.id})'
    )
    logger.info(f'Usuario "{instance.username}" fue {accion} por {user.username if user else "usuario desconocido"}')

@receiver(post_delete, sender=Usuario)
def log_usuario_delete(sender, instance, **kwargs):
    user = getattr(threading.current_thread(), 'user', None)
    Log.objects.create(
        usuario=user,
        modelo='usuarios',  # Cambiado a módulo principal
        accion='eliminar',
        detalles=f'Usuario {user.username if user else "desconocido"} eliminó usuario "{instance.username}" (ID: {instance.id})'
    )
    logger.info(f'Usuario "{instance.username}" fue eliminado por {user.username if user else "usuario desconocido"}')

# Logs para Rol
@receiver(post_save, sender=Rol)
def log_rol_change(sender, instance, created, **kwargs):
    user = getattr(threading.current_thread(), 'user', None)
    accion = 'crear' if created else 'actualizar'
    Log.objects.create(
        usuario=user,
        modelo='roles',  # Cambiado a módulo principal
        accion=accion,
        detalles=f'Usuario {user.username if user else "desconocido"} {accion} rol "{instance.nombre}" (ID: {instance.id})'
    )
    logger.info(f'Rol "{instance.nombre}" fue {accion} por {user.username if user else "usuario desconocido"}')

@receiver(post_delete, sender=Rol)
def log_rol_delete(sender, instance, **kwargs):
    user = getattr(threading.current_thread(), 'user', None)
    Log.objects.create(
        usuario=user,
        modelo='roles',  # Cambiado a módulo principal
        accion='eliminar',
        detalles=f'Usuario {user.username if user else "desconocido"} eliminó rol "{instance.nombre}" (ID: {instance.id})'
    )
    logger.info(f'Rol "{instance.nombre}" fue eliminado por {user.username if user else "usuario desconocido"}')

# Logs para Almacen
@receiver(post_save, sender=Almacen)
def log_almacen_change(sender, instance, created, **kwargs):
    user = getattr(threading.current_thread(), 'user', None)
    accion = 'crear' if created else 'actualizar'
    Log.objects.create(
        usuario=user,
        modelo='almacenes',  # Cambiado a módulo principal
        accion=accion,
        detalles=f'Usuario {user.username if user else "desconocido"} {accion} almacén "{instance.nombre}" (ID: {instance.id})'
    )
    logger.info(f'Almacén "{instance.nombre}" fue {accion} por {user.username if user else "usuario desconocido"}')

@receiver(post_delete, sender=Almacen)
def log_almacen_delete(sender, instance, **kwargs):
    user = getattr(threading.current_thread(), 'user', None)
    Log.objects.create(
        usuario=user,
        modelo='almacenes',  # Cambiado a módulo principal
        accion='eliminar',
        detalles=f'Usuario {user.username if user else "desconocido"} eliminó almacén "{instance.nombre}" (ID: {instance.id})'
    )
    logger.info(f'Almacén "{instance.nombre}" fue eliminado por {user.username if user else "usuario desconocido"}')

# Logs para Proveedor
@receiver(post_save, sender=Proveedor)
def log_proveedor_change(sender, instance, created, **kwargs):
    user = getattr(threading.current_thread(), 'user', None)
    accion = 'crear' if created else 'actualizar'
    Log.objects.create(
        usuario=user,
        modelo='proveedores',  # Cambiado a módulo principal
        accion=accion,
        detalles=f'Usuario {user.username if user else "desconocido"} {accion} proveedor "{instance.nombre}" (ID: {instance.id})'
    )
    logger.info(f'Proveedor "{instance.nombre}" fue {accion} por {user.username if user else "usuario desconocido"}')

@receiver(post_delete, sender=Proveedor)
def log_proveedor_delete(sender, instance, **kwargs):
    user = getattr(threading.current_thread(), 'user', None)
    Log.objects.create(
        usuario=user,
        modelo='proveedores',  # Cambiado a módulo principal
        accion='eliminar',
        detalles=f'Usuario {user.username if user else "desconocido"} eliminó proveedor "{instance.nombre}" (ID: {instance.id})'
    )
    logger.info(f'Proveedor "{instance.nombre}" fue eliminado por {user.username if user else "usuario desconocido"}')

# Logs para Categoria
@receiver(post_save, sender=Categoria)
def log_categoria_change(sender, instance, created, **kwargs):
    user = getattr(threading.current_thread(), 'user', None)
    accion = 'crear' if created else 'actualizar'
    Log.objects.create(
        usuario=user,
        modelo='categorias',  # Cambiado a módulo principal
        accion=accion,
        detalles=f'Usuario {user.username if user else "desconocido"} {accion} categoría "{instance.nombre}" (ID: {instance.id})'
    )
    logger.info(f'Categoría "{instance.nombre}" fue {accion} por {user.username if user else "usuario desconocido"}')

@receiver(post_delete, sender=Categoria)
def log_categoria_delete(sender, instance, **kwargs):
    user = getattr(threading.current_thread(), 'user', None)
    Log.objects.create(
        usuario=user,
        modelo='categorias',  # Cambiado a módulo principal
        accion='eliminar',
        detalles=f'Usuario {user.username if user else "desconocido"} eliminó categoría "{instance.nombre}" (ID: {instance.id})'
    )
    logger.info(f'Categoría "{instance.nombre}" fue eliminada por {user.username if user else "usuario desconocido"}')