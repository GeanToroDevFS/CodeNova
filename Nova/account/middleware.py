from django.utils.deprecation import MiddlewareMixin
from .models import Log

class LogUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Almacena el usuario en el thread local para usarlo en signals
            import threading
            threading.current_thread().user = request.user

    def process_response(self, request, response):
        # Nueva lógica para logs de exportación (después de procesar la respuesta)
        if hasattr(request, 'user') and request.user.is_authenticated and 'exportar' in request.GET and request.GET['exportar'] == '1':
            # Determinar el tipo de reporte basado en la URL
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
        
        return response