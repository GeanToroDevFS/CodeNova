from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def health_check(request):
    """Endpoint simple para verificar que la app funciona"""
    return HttpResponse("OK - App is running")

def simple_login(request):
    """Login simplificado para testing"""
    from django.contrib.auth import authenticate, login
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return HttpResponse(f"Logged in as {username}")
        return HttpResponse("Login failed")
    return HttpResponse('''
        <form method="post">
            <input name="username" placeholder="Username">
            <input name="password" type="password" placeholder="Password">
            <button type="submit">Login</button>
        </form>
    ''')