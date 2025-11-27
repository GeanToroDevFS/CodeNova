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
            # Logs de exportación (actualizado para acción 'exportar')
            if 'exportar' in request.GET and request.GET['exportar'] == '1':
                # Determinar qué se exportó basado en la URL
                if 'ventas' in request.path:
                    que_exporto = 'reporte de ventas'
                elif 'inventario' in request.path:
                    que_exporto = 'inventario completo'
                elif 'usuarios' in request.path:
                    que_exporto = 'reporte de usuarios'
                elif 'proveedores' in request.path:
                    que_exporto = 'reporte de proveedores'
                elif 'almacenes' in request.path:
                    que_exporto = 'reporte de almacenes'
                elif 'categorias' in request.path:
                    que_exporto = 'reporte de categorías'
                elif 'roles' in request.path:
                    que_exporto = 'reporte de roles'
                else:
                    que_exporto = 'un reporte'
                
                modelo = 'informes'
                accion = 'exportar'
                detalles = f'Usuario {request.user.username} exportó {que_exporto} desde {request.path} (IP: {request.META.get("REMOTE_ADDR", "desconocida")})'
                
                Log.objects.create(
                    usuario=request.user,
                    modelo=modelo,
                    accion=accion,
                    detalles=detalles
                )
                logger.info(detalles)
            
            # Logs para descarga de facturas
            elif 'factura' in request.path:
                # Extraer ID de venta de la URL (e.g., /factura/123/)
                venta_id = request.path.split('/')[-2]  # Asumiendo formato /factura/<id>/
                modelo = 'ventas'
                accion = 'exportar'
                detalles = f'Usuario {request.user.username} descargó factura de venta ID {venta_id} desde {request.path} (IP: {request.META.get("REMOTE_ADDR", "desconocida")})'
                
                Log.objects.create(
                    usuario=request.user,
                    modelo=modelo,
                    accion=accion,
                    detalles=detalles
                )
                logger.info(detalles)
            
            # Logs para todas las acciones en módulos (excluyendo 'api')
            elif any(modulo in request.path for modulo in ['productos', 'usuarios', 'proveedores', 'almacenes', 'categorias', 'roles', 'ventas', 'kardex', 'informes', 'logs']) and 'api' not in request.path:
                if request.method == 'GET':
                    # Todos los accesos GET se registran como 'leer'
                    accion = 'leer'
                    detalles = f'Usuario {request.user.username} leyó lista o filtro en {request.path.split("/")[1]}'
                elif request.method == 'POST':
                    if 'crear' in request.path or 'nuevo' in request.path:
                        accion = 'crear'
                        detalles = f'Usuario {request.user.username} creó en {request.path.split("/")[1]}'
                    elif 'editar' in request.path or 'modificar' in request.path:
                        accion = 'actualizar'
                        detalles = f'Usuario {request.user.username} actualizó en {request.path.split("/")[1]}'
                    elif 'eliminar' in request.path or 'borrar' in request.path:
                        accion = 'eliminar'
                        detalles = f'Usuario {request.user.username} eliminó en {request.path.split("/")[1]}'
                    else:
                        accion = 'leer'  # POST sin acción específica, asumir leer
                        detalles = f'Usuario {request.user.username} realizó acción en {request.path.split("/")[1]}'
                
                # Mapa para modelos consistentes
                modelo_map = {
                    'productos': 'productos',
                    'usuarios': 'usuarios',
                    'proveedores': 'proveedores',
                    'almacenes': 'almacenes',
                    'categorias': 'categorias',
                    'roles': 'roles',
                    'ventas': 'ventas',
                    'kardex': 'kardex',
                    'logs': 'logs',
                    'informes': 'informes',
                }
                modelo = modelo_map.get(request.path.split("/")[1], request.path.split("/")[1])
                
                Log.objects.create(
                    usuario=request.user,
                    modelo=modelo,
                    accion=accion,
                    detalles=detalles
                )
                logger.info(detalles)
        
        return response