from django.utils.deprecation import MiddlewareMixin

class LogUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Almacena el usuario en el thread local para usarlo en signals
            import threading
            threading.current_thread().user = request.user