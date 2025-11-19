from django.utils.deprecation import MiddlewareMixin
from .models import Log
import logging

logger = logging.getLogger(__name__)

class LogUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Almacena el usuario en el thread local para usarlo en signals
            import threading
            threading.current_thread().user = request.user

    def process_response(self, request, response):
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Logs de exportación (ya existente)
            if 'exportar' in request.GET and request.GET['exportar'] == '1':
                if 'ventas' in request.path:
                    modelo = 'Exportación'
                    detalles = f'Usuario {request.user.username} exportó reporte de ventas'
                elif 'inventario' in request.path:
                    modelo = 'Exportación'
                    detalles = f'Usuario {request.user.username} exportó inventario completo'
                elif 'usuarios' in request.path:
                    modelo = 'Exportación'
                    detalles = f'Usuario {request.user.username} exportó reporte de usuarios'
                elif 'proveedores' in request.path:
                    modelo = 'Exportación'
                    detalles = f'Usuario {request.user.username} exportó reporte de proveedores'
                elif 'almacenes' in request.path:
                    modelo = 'Exportación'
                    detalles = f'Usuario {request.user.username} exportó reporte de almacenes'
                elif 'categorias' in request.path:
                    modelo = 'Exportación'
                    detalles = f'Usuario {request.user.username} exportó reporte de categorías'
                elif 'roles' in request.path:
                    modelo = 'Exportación'
                    detalles = f'Usuario {request.user.username} exportó reporte de roles'
                else:
                    modelo = 'Exportación'
                    detalles = f'Usuario {request.user.username} exportó un reporte'
                
                Log.objects.create(
                    usuario=request.user,
                    modelo=modelo,
                    accion='exportó',
                    detalles=detalles
                )
                logger.info(detalles)
            
            # Logs para todas las acciones en módulos (nuevo)
            elif any(modulo in request.path for modulo in ['productos', 'usuarios', 'proveedores', 'almacenes', 'categorias', 'roles', 'ventas', 'kardex', 'informes']):
                if request.method == 'GET':
                    if 'crear' in request.path or 'nuevo' in request.path:
                        accion = 'accedió a crear'
                        detalles = f'Usuario {request.user.username} accedió a crear en {request.path.split("/")[1]}'
                    elif 'editar' in request.path or 'modificar' in request.path:
                        accion = 'accedió a editar'
                        detalles = f'Usuario {request.user.username} accedió a editar en {request.path.split("/")[1]}'
                    elif 'eliminar' in request.path or 'borrar' in request.path:
                        accion = 'accedió a eliminar'
                        detalles = f'Usuario {request.user.username} accedió a eliminar en {request.path.split("/")[1]}'
                    else:
                        accion = 'leyó'
                        detalles = f'Usuario {request.user.username} leyó lista o filtro en {request.path.split("/")[1]}'
                elif request.method == 'POST':
                    if 'crear' in request.path or 'nuevo' in request.path:
                        accion = 'creó'
                        detalles = f'Usuario {request.user.username} creó en {request.path.split("/")[1]}'
                    elif 'editar' in request.path or 'modificar' in request.path:
                        accion = 'actualizó'
                        detalles = f'Usuario {request.user.username} actualizó en {request.path.split("/")[1]}'
                    elif 'eliminar' in request.path or 'borrar' in request.path:
                        accion = 'eliminó'
                        detalles = f'Usuario {request.user.username} eliminó en {request.path.split("/")[1]}'
                    else:
                        accion = 'realizó acción'
                        detalles = f'Usuario {request.user.username} realizó acción POST en {request.path.split("/")[1]}'
                
                Log.objects.create(
                    usuario=request.user,
                    modelo=request.path.split("/")[1].capitalize(),  # e.g., 'Productos'
                    accion=accion,
                    detalles=detalles
                )
                logger.info(detalles)
        
        return response