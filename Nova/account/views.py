from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db.models import Count
from .forms import (
    LoginForm, CustomUserCreationForm, CustomUserChangeForm,
    AlmacenForm, ProveedorForm, CategoriaForm, ProductoForm, RolForm
)
from .models import Usuario, Almacen, Proveedor, Categoria, Producto, Rol
from .decorators import login_required_custom, role_required, _user_has_permission
from account.models import Usuario

# ====================================================
# --- Utilidades internas para Roles/Permisos ---
# ====================================================

def _get_dashboard_modules():
    """Módulos visibles en el dashboard usados en la matriz de permisos."""
    return ['productos', 'usuarios', 'proveedores', 'almacenes', 'categorias', 'roles']


def _get_crud_actions():
    """Acciones CRUD mostradas como columnas en la matriz."""
    return ['crear', 'leer', 'actualizar', 'eliminar']


def _collect_selected_permissions(post_data):
    """
    Extrae de request.POST las claves de permisos seleccionadas.
    Ejemplo de claves esperadas: 'perm_productos_leer'
    Devuelve lista sin 'perm_' (ej: ['productos_leer'])
    """
    perms = []
    for k in post_data.keys():
        if k.startswith('perm_'):
            perms.append(k.replace('perm_', '').strip().lower())
    return sorted(perms)


# ====================================================
# --- Vistas de Autenticación ---
# ====================================================

def user_login(request):
    """Versión final del login con trazas y validaciones completas."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)

            print("=== LOGIN DEBUG ===")
            print(f"Usuario: {username}")
            print(f"Autenticado: {user is not None}")
            if user:
                print(f"estado={user.estado}, is_active={user.is_active}, rol={getattr(user.rol, 'nombre', None)}, rol_activo={getattr(user.rol, 'estado', None)}")
            print("====================")

            if user is not None:
                if not user.estado or not user.is_active:
                    messages.error(request, 'El usuario está inactivo. Contacta con el administrador.')
                    return redirect('login')

                if user.rol and hasattr(user.rol, 'estado') and not getattr(user.rol, 'estado', True):
                    messages.warning(
                        request,
                        f'El rol "{user.rol.nombre}" está inactivo. No tendrás acceso a módulos hasta que se active.'
                    )

                login(request, user)
                messages.success(request, f'¡Bienvenido, {user.username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Credenciales inválidas. Verifica usuario y contraseña.')
    else:
        form = LoginForm()

    return render(request, 'account/login.html', {'form': form})


@login_required_custom
def user_logout(request):
    logout(request)
    messages.info(request, 'Sesión cerrada correctamente.')
    return redirect('login')


@login_required_custom
def dashboard(request):
    # Calcular módulos permitidos basados en permisos de "leer"
    modulos = ['productos', 'usuarios', 'proveedores', 'almacenes', 'categorias', 'roles']
    modulos_permitidos = [modulo for modulo in modulos if _user_has_permission(request.user, modulo, 'leer')]
    
    return render(request, 'account/dashboard.html', {
        'username': request.user.username,
        'rol': request.user.rol,
        'modulos_permitidos': modulos_permitidos  # Nuevo contexto
    })


# ====================================================
# --- CRUD de Usuarios ---
# ====================================================

@login_required_custom
@role_required(module='usuarios', action='leer')
def lista_usuarios(request):
    usuarios = Usuario.objects.all().order_by('username')
    return render(request, 'account/usuarios_listar.html', {
        'usuarios': usuarios,
        'titulo': 'Lista de Usuarios'
    })


@login_required_custom
@role_required(module='usuarios', action='crear')
def crear_usuario(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.set_password(form.cleaned_data['password1'])  # ✅ se cifra explícitamente
            usuario.save()
            messages.success(request, 'Usuario creado exitosamente.')
            return redirect('usuarios_listar')
        else:
            messages.error(request, 'Error al crear el usuario. Revisa los campos.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'account/usuario_form.html', {
        'form': form,
        'titulo': 'Nuevo Usuario',
        'editar': False
    })


@login_required_custom
@role_required(module='usuarios', action='actualizar')
def editar_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario actualizado exitosamente.')
            return redirect('usuarios_listar')
        else:
            messages.error(request, 'Error al actualizar el usuario. Revisa los campos.')
    else:
        form = CustomUserChangeForm(instance=usuario)
    return render(request, 'account/usuario_form.html', {
        'form': form,
        'usuario': usuario,
        'titulo': 'Editar Usuario',
        'editar': True
    })


@login_required_custom
@role_required(module='usuarios', action='eliminar')
def eliminar_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        usuario.delete()
        messages.success(request, f'Usuario "{usuario.username}" eliminado correctamente.')
        return redirect('usuarios_listar')
    return render(request, 'account/usuario_confirmar_eliminar.html', {'usuario': usuario})


# ====================================================
# --- CRUD de Productos ---
# ====================================================

@login_required_custom
@role_required(module='productos', action='leer')
def productos_listar(request):
    productos = Producto.objects.select_related('categoria', 'proveedor', 'almacen').all().order_by('nombre')
    return render(request, 'account/productos_listar.html', {
        'productos': productos,
        'titulo': 'Lista de Productos'
    })


@login_required_custom
@role_required(module='productos', action='crear')
def producto_crear(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto creado exitosamente.')
            return redirect('productos_listar')
        else:
            messages.error(request, 'Error al crear el producto. Por favor, revisa los datos.')
    else:
        form = ProductoForm()
    categorias = Categoria.objects.filter(estado=True)
    proveedores = Proveedor.objects.filter(estado=True)
    almacenes = Almacen.objects.filter(estado=True)
    monedas = Producto.MONEDA_CHOICES
    return render(request, 'account/producto_form.html', {
        'form': form,
        'categorias': categorias,
        'proveedores': proveedores,
        'almacenes': almacenes,
        'monedas': monedas,
        'titulo': 'Nuevo Producto',
        'editar': False
    })


@login_required_custom
@role_required(module='productos', action='actualizar')
def producto_editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado exitosamente.')
            return redirect('productos_listar')
        else:
            messages.error(request, 'Error al actualizar el producto. Por favor, revisa los datos.')
    else:
        form = ProductoForm(instance=producto)
    categorias = Categoria.objects.filter(estado=True)
    proveedores = Proveedor.objects.filter(estado=True)
    almacenes = Almacen.objects.filter(estado=True)
    monedas = Producto.MONEDA_CHOICES
    return render(request, 'account/producto_form.html', {
        'form': form,
        'producto': producto,
        'categorias': categorias,
        'proveedores': proveedores,
        'almacenes': almacenes,
        'monedas': monedas,
        'titulo': 'Editar Producto',
        'editar': True
    })


@login_required_custom
@role_required(module='productos', action='eliminar')
def producto_eliminar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, f'Producto "{producto.nombre}" eliminado correctamente.')
        return redirect('productos_listar')
    return render(request, 'account/producto_confirmar_eliminar.html', {'producto': producto})


# ====================================================
# --- CRUD de Proveedores ---
# ====================================================

@login_required_custom
@role_required(module='proveedores', action='leer')
def lista_proveedores(request):
    proveedores = Proveedor.objects.all().order_by('nombre')
    return render(request, 'account/proveedores_listar.html', {
        'proveedores': proveedores,
        'titulo': 'Lista de Proveedores'
    })


@login_required_custom
@role_required(module='proveedores', action='crear')
def crear_proveedor(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor creado exitosamente.')
            return redirect('proveedores_listar')
    else:
        form = ProveedorForm()
    return render(request, 'account/proveedor_form.html', {
        'form': form,
        'titulo': 'Nuevo Proveedor',
        'editar': False
    })


@login_required_custom
@role_required(module='proveedores', action='actualizar')
def editar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor actualizado exitosamente.')
            return redirect('proveedores_listar')
    else:
        form = ProveedorForm(instance=proveedor)
    return render(request, 'account/proveedor_form.html', {
        'form': form,
        'proveedor': proveedor,
        'titulo': 'Editar Proveedor',
        'editar': True
    })


@login_required_custom
@role_required(module='proveedores', action='eliminar')
def eliminar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        proveedor.delete()
        messages.success(request, f'Proveedor "{proveedor.nombre}" eliminado correctamente.')
        return redirect('proveedores_listar')
    return render(request, 'account/proveedor_confirmar_eliminar.html', {'proveedor': proveedor})


# ====================================================
# --- CRUD de Almacenes ---
# ====================================================

@login_required_custom
@role_required(module='almacenes', action='leer')
def lista_almacenes(request):
    almacenes = Almacen.objects.select_related('responsable').all().order_by('nombre')
    return render(request, 'account/almacenes_listar.html', {
        'almacenes': almacenes,
        'titulo': 'Lista de Almacenes'
    })


@login_required_custom
@role_required(module='almacenes', action='crear')
def crear_almacen(request):
    if request.method == 'POST':
        form = AlmacenForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Almacén creado exitosamente.')
            return redirect('almacenes_listar')
    else:
        form = AlmacenForm()
    return render(request, 'account/almacen_form.html', {
        'form': form,
        'titulo': 'Nuevo Almacén',
        'editar': False
    })


@login_required_custom
@role_required(module='almacenes', action='actualizar')
def editar_almacen(request, pk):
    almacen = get_object_or_404(Almacen, pk=pk)
    if request.method == 'POST':
        form = AlmacenForm(request.POST, instance=almacen)
        if form.is_valid():
            form.save()
            messages.success(request, 'Almacén actualizado exitosamente.')
            return redirect('almacenes_listar')
    else:
        form = AlmacenForm(instance=almacen)
    return render(request, 'account/almacen_form.html', {
        'form': form,
        'almacen': almacen,
        'titulo': 'Editar Almacén',
        'editar': True
    })


@login_required_custom
@role_required(module='almacenes', action='eliminar')
def eliminar_almacen(request, pk):
    almacen = get_object_or_404(Almacen, pk=pk)
    if request.method == 'POST':
        almacen.delete()
        messages.success(request, f'Almacén "{almacen.nombre}" eliminado correctamente.')
        return redirect('almacenes_listar')
    return render(request, 'account/almacen_confirmar_eliminar.html', {'almacen': almacen})


# ====================================================
# --- CRUD de Categorías ---
# ====================================================

@login_required_custom
@role_required(module='categorias', action='leer')
def lista_categorias(request):
    categorias = Categoria.objects.all().order_by('nombre')
    return render(request, 'account/categorias_listar.html', {
        'categorias': categorias,
        'titulo': 'Lista de Categorías'
    })


@login_required_custom
@role_required(module='categorias', action='crear')
def crear_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría creada exitosamente.')
            return redirect('categorias_listar')
    else:
        form = CategoriaForm()
    return render(request, 'account/categoria_form.html', {
        'form': form,
        'titulo': 'Nueva Categoría',
        'editar': False
    })


@login_required_custom
@role_required(module='categorias', action='actualizar')
def editar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría actualizada exitosamente.')
            return redirect('categorias_listar')
    else:
        form = CategoriaForm(instance=categoria)
    return render(request, 'account/categoria_form.html', {
        'form': form,
        'categoria': categoria,
        'titulo': 'Editar Categoría',
        'editar': True
    })


@login_required_custom
@role_required(module='categorias', action='eliminar')
def eliminar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        categoria.delete()
        messages.success(request, f'Categoría "{categoria.nombre}" eliminada correctamente.')
        return redirect('categorias_listar')
    return render(request, 'account/categoria_confirmar_eliminar.html', {'categoria': categoria})


# ====================================================
# --- CRUD de Roles ---
# ====================================================

@login_required_custom
@role_required(module='roles', action='leer')
def roles_listar(request):
    roles = Rol.objects.all().order_by('nombre')
    return render(request, 'account/roles_listar.html', {
        'roles': roles,
        'titulo': 'Lista de Roles'
    })


@login_required_custom
@role_required(module='roles', action='crear')
def roles_crear(request):
    if request.method == 'POST':
        form = RolForm(request.POST)
        if form.is_valid():
            rol = form.save(commit=False)
            selected_perms = _collect_selected_permissions(request.POST)
            rol.permisos = ', '.join(selected_perms)
            # ✅ Guardar estado desde el formulario
            rol.estado = request.POST.get('estado', 'activo') == 'activo'
            rol.save()
            messages.success(request, 'Rol creado exitosamente.')
            return redirect('roles_listar')
    else:
        form = RolForm()

    modulos = _get_dashboard_modules()
    acciones = _get_crud_actions()
    permisos_actuales = set()

    return render(request, 'account/roles_form.html', {
        'form': form,
        'modulos': modulos,
        'acciones': acciones,
        'permisos_actuales': permisos_actuales,
        'titulo': 'Nuevo Rol',
        'editar': False
    })


@login_required_custom
@role_required(module='roles', action='actualizar')
def roles_editar(request, pk):
    rol = get_object_or_404(Rol, pk=pk)
    if request.method == 'POST':
        form = RolForm(request.POST, instance=rol)
        if form.is_valid():
            rol = form.save(commit=False)
            selected_perms = _collect_selected_permissions(request.POST)
            rol.permisos = ', '.join(selected_perms)
            # ✅ Guardar estado desde el formulario
            rol.estado = request.POST.get('estado', 'activo') == 'activo'
            rol.save()
            messages.success(request, 'Rol actualizado exitosamente.')
            return redirect('roles_listar')
    else:
        form = RolForm(instance=rol)

    modulos = _get_dashboard_modules()
    acciones = _get_crud_actions()
    permisos_actuales = set(rol.get_permisos_list())

    return render(request, 'account/roles_form.html', {
        'form': form,
        'rol': rol,
        'modulos': modulos,
        'acciones': acciones,
        'permisos_actuales': permisos_actuales,
        'titulo': 'Editar Rol',
        'editar': True
    })


@login_required_custom
@role_required(module='roles', action='eliminar')
def roles_eliminar(request, pk):
    rol = get_object_or_404(Rol, pk=pk)
    if request.method == 'POST':
        rol.delete()
        messages.success(request, f'Rol "{rol.nombre}" eliminado correctamente.')
        return redirect('roles_listar')
    return render(request, 'account/roles_confirmar_eliminar.html', {'rol': rol})


@login_required_custom
@role_required(module='roles', action='leer')
def matriz_roles(request):
    roles = Rol.objects.all()
    modulos = _get_dashboard_modules()
    acciones = _get_crud_actions()
    matriz = {}
    for rol in roles:
        matriz[rol.id] = {}
        permisos_rol = rol.get_permisos_list()
        for modulo in modulos:
            for accion in acciones:
                permiso = f"{modulo}_{accion}"
                matriz[rol.id][permiso] = permiso in permisos_rol

    return render(request, 'account/roles_matriz.html', {
        'roles': roles,
        'modulos': modulos,
        'acciones': acciones,
        'matriz': matriz,
        'titulo': 'Matriz de Permisos'
    })
