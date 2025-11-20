from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db.models import Count, Sum 
from .forms import (
    LoginForm, CustomUserCreationForm, CustomUserChangeForm,
    AlmacenForm, ProveedorForm, CategoriaForm, ProductoForm, RolForm
)
from .models import Usuario, Almacen, Proveedor, Categoria, Producto, Rol, Venta, DetalleVenta, Kardex, Log
from .decorators import login_required_custom, role_required, _user_has_permission
from account.models import Usuario

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from django.http import FileResponse
from django.http import JsonResponse
from django.utils.timezone import make_aware
from datetime import datetime

# ====================================================
# --- Utilidades internas para Roles/Permisos ---
# ====================================================

def _get_dashboard_modules():
    """Módulos visibles en el dashboard usados en la matriz de permisos."""
    return ['productos', 'usuarios', 'proveedores', 'almacenes', 'categorias', 'roles', 'ventas', 'kardex']


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
    modulos = _get_dashboard_modules() # ← Cambia esto para incluir 'ventas'
    modulos_permitidos = [modulo for modulo in modulos if _user_has_permission(request.user, modulo, 'leer')]
    
    return render(request, 'account/dashboard.html', {
        'username': request.user.username,
        'rol': request.user.rol,
        'modulos_permitidos': modulos_permitidos  # Nuevo contexto
    })


# ====================================================
# --- CRUD de Usuarios ---
# ====================================================

#Listar
@login_required_custom
@role_required(module='usuarios', action='leer')
def lista_usuarios(request):
    usuarios = Usuario.objects.all().order_by('username')
    # Calcular permisos específicos para el usuario
    permisos = {
        'leer': _user_has_permission(request.user, 'usuarios', 'leer'),
        'editar': _user_has_permission(request.user, 'usuarios', 'actualizar'),
        'eliminar': _user_has_permission(request.user, 'usuarios', 'eliminar'),
        'crear': _user_has_permission(request.user, 'usuarios', 'crear'),
    }
    return render(request, 'account/usuarios_listar.html', {
        'usuarios': usuarios,
        'titulo': 'Lista de Usuarios',
        'permisos': permisos,  
    })

#Crear
@login_required_custom
@role_required(module='usuarios', action='crear')
def crear_usuario(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.set_password(form.cleaned_data['password1'])
            usuario.estado = True  # ← FORZAR a activo
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

#Editar
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

#Eliminar
@login_required_custom
@role_required(module='usuarios', action='eliminar')
def eliminar_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        usuario.estado = False # Cambio para no eliminar, solo desactivar
        usuario.save()
        messages.success(request, f'Usuario "{usuario.username}" desactivado correctamente.')
        return redirect('usuarios_listar')
    return render(request, 'account/usuario_confirmar_eliminar.html', {'usuario': usuario})


# ====================================================
# --- CRUD de Productos ---
# ====================================================

#Listar
@login_required_custom
@role_required(module='productos', action='leer')
def productos_listar(request):
    productos = Producto.objects.select_related('categoria', 'proveedor', 'almacen').all().order_by('nombre')
    # Calcular permisos específicos para el usuario
    permisos = {
        'leer': _user_has_permission(request.user, 'productos', 'leer'),
        'editar': _user_has_permission(request.user, 'productos', 'actualizar'),
        'eliminar': _user_has_permission(request.user, 'productos', 'eliminar'),
        'crear': _user_has_permission(request.user, 'productos', 'crear'),
    }
    return render(request, 'account/productos_listar.html', {
        'productos': productos,
        'titulo': 'Lista de Productos',
        'permisos': permisos,
    })

#Crear
@login_required_custom
@role_required(module='productos', action='crear')
def producto_crear(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.estado = True  # ← FORZAR a activo
            producto.save()
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

#Editar
@login_required_custom
@role_required(module='productos', action='actualizar')
def producto_editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.estado = True  # ← FUERZA ACTIVO AL EDITAR (evita cambios accidentales)
            producto.save()
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

#Eliminar
@login_required_custom
@role_required(module='productos', action='eliminar')
def producto_eliminar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.estado = False # Cambio para no eliminar, solo desactivar
        producto.save()
        messages.success(request, f'Producto "{producto.nombre}" desactivado correctamente.')
        return redirect('productos_listar')
    return render(request, 'account/producto_confirmar_eliminar.html', {'producto': producto})


# ====================================================
# --- CRUD de Proveedores ---
# ====================================================

#Listar
@login_required_custom
@role_required(module='proveedores', action='leer')
def lista_proveedores(request):
    proveedores = Proveedor.objects.all().order_by('nombre')
    # Calcular permisos específicos para el usuario
    permisos = {
        'leer': _user_has_permission(request.user, 'proveedores', 'leer'),
        'editar': _user_has_permission(request.user, 'proveedores', 'actualizar'),
        'eliminar': _user_has_permission(request.user, 'proveedores', 'eliminar'),
        'crear': _user_has_permission(request.user, 'proveedores', 'crear'),
    }
    return render(request, 'account/proveedores_listar.html', {
        'proveedores': proveedores,
        'titulo': 'Lista de Proveedores',
        'permisos': permisos,  # Agregado
    })

#Crear
@login_required_custom
@role_required(module='proveedores', action='crear')
def crear_proveedor(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            proveedor = form.save(commit=False)
            proveedor.estado = True  # ← FORZAR a activo
            proveedor.save()
            messages.success(request, 'Proveedor creado exitosamente.')
            return redirect('proveedores_listar')
    else:
        form = ProveedorForm()
    return render(request, 'account/proveedor_form.html', {
        'form': form,
        'titulo': 'Nuevo Proveedor',
        'editar': False
    })

#Editar
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

#Eliminar
@login_required_custom
@role_required(module='proveedores', action='eliminar')
def eliminar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        proveedor.estado = False # Cambio para no eliminar, solo desactivar
        proveedor.save()
        messages.success(request, f'Proveedor "{proveedor.nombre}" desactivado correctamente.')
        return redirect('proveedores_listar')
    return render(request, 'account/proveedor_confirmar_eliminar.html', {'proveedor': proveedor})


# ====================================================
# --- CRUD de Almacenes ---
# ====================================================

#Listar
@login_required_custom
@role_required(module='almacenes', action='leer')
def lista_almacenes(request):
    almacenes = Almacen.objects.select_related('responsable').all().order_by('nombre')
    # Calcular permisos específicos para el usuario
    permisos = {
        'leer': _user_has_permission(request.user, 'almacenes', 'leer'),
        'editar': _user_has_permission(request.user, 'almacenes', 'actualizar'),
        'eliminar': _user_has_permission(request.user, 'almacenes', 'eliminar'),
        'crear': _user_has_permission(request.user, 'almacenes', 'crear'),
    }
    return render(request, 'account/almacenes_listar.html', {
        'almacenes': almacenes,
        'titulo': 'Lista de Almacenes',
        'permisos': permisos,  # Agregado
    })

#Crear
@login_required_custom
@role_required(module='almacenes', action='crear')
def crear_almacen(request):
    if request.method == 'POST':
        form = AlmacenForm(request.POST)
        if form.is_valid():
            almacen = form.save(commit=False)
            almacen.estado = True  # ← FORZAR a activo
            almacen.save()
            messages.success(request, 'Almacén creado exitosamente.')
            return redirect('almacenes_listar')
    else:
        form = AlmacenForm()
    return render(request, 'account/almacen_form.html', {
        'form': form,
        'titulo': 'Nuevo Almacén',
        'editar': False
    })

#Editar
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

#Eliminar
@login_required_custom
@role_required(module='almacenes', action='eliminar')
def eliminar_almacen(request, pk):
    almacen = get_object_or_404(Almacen, pk=pk)
    if request.method == 'POST':
        almacen.estado = False # Cambio para no eliminar, solo desactivar
        almacen.save()
        messages.success(request, f'Almacén "{almacen.nombre}" desactivado correctamente.')
        return redirect('almacenes_listar')
    return render(request, 'account/almacen_confirmar_eliminar.html', {'almacen': almacen})


# ====================================================
# --- CRUD de Categorías ---
# ====================================================

#Listar
@login_required_custom
@role_required(module='categorias', action='leer')
def lista_categorias(request):
    categorias = Categoria.objects.all().order_by('nombre')
    # Calcular permisos específicos para el usuario
    permisos = {
        'leer': _user_has_permission(request.user, 'categorias', 'leer'),
        'editar': _user_has_permission(request.user, 'categorias', 'actualizar'),
        'eliminar': _user_has_permission(request.user, 'categorias', 'eliminar'),
        'crear': _user_has_permission(request.user, 'categorias', 'crear'),
    }
    return render(request, 'account/categorias_listar.html', {
        'categorias': categorias,
        'titulo': 'Lista de Categorías',
        'permisos': permisos,
    })

#Crear
@login_required_custom
@role_required(module='categorias', action='crear')
def crear_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save(commit=False)
            categoria.estado = True  # ← FORZAR a activo
            categoria.save()
            messages.success(request, 'Categoría creada exitosamente.')
            return redirect('categorias_listar')
    else:
        form = CategoriaForm()
    return render(request, 'account/categoria_form.html', {
        'form': form,
        'titulo': 'Nueva Categoría',
        'editar': False
    })

#Editar
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

#Eliminar
@login_required_custom
@role_required(module='categorias', action='eliminar')
def eliminar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        categoria.estado = False # Cambio para no eliminar, solo desactivar
        categoria.save()
        messages.success(request, f'Categoría "{categoria.nombre}" desactivada correctamente.')
        return redirect('categorias_listar')
    return render(request, 'account/categoria_confirmar_eliminar.html', {'categoria': categoria})


# ====================================================
# --- CRUD de Roles ---
# ====================================================

#Listar
@login_required_custom
@role_required(module='roles', action='leer')
def roles_listar(request):
    roles = Rol.objects.all().order_by('nombre')
    # Calcular permisos específicos para el usuario
    permisos = {
        'leer': _user_has_permission(request.user, 'roles', 'leer'),
        'editar': _user_has_permission(request.user, 'roles', 'actualizar'),
        'eliminar': _user_has_permission(request.user, 'roles', 'eliminar'),
        'crear': _user_has_permission(request.user, 'roles', 'crear'),
    }
    return render(request, 'account/roles_listar.html', {
        'roles': roles,
        'titulo': 'Lista de Roles',
        'permisos': permisos, 
    })

#Crear
@login_required_custom
@role_required(module='roles', action='crear')
def roles_crear(request):
    if request.method == 'POST':
        form = RolForm(request.POST)
        if form.is_valid():
            rol = form.save(commit=False)
            selected_perms = _collect_selected_permissions(request.POST)
            rol.permisos = ', '.join(selected_perms)
            rol.estado = True  # ← FORZAR a activo
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

#Editar
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

#Eliminar
@login_required_custom
@role_required(module='roles', action='eliminar')
def roles_eliminar(request, pk):
    rol = get_object_or_404(Rol, pk=pk)
    if request.method == 'POST':
        rol.estado = False # Cambio para no eliminar, solo desactivar
        rol.save()
        messages.success(request, f'Rol "{rol.nombre}" desactivado correctamente.')
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



# ====================================================
# --- Funciones para Reportes ---
# ====================================================
@login_required_custom
@role_required(module='productos', action='leer')  # Asumiendo permisos en productos
def informes_listar(request):
    return render(request, 'account/informes_listar.html', {
        'titulo': 'Módulo de Informes'
    })
    
    
@login_required_custom
@role_required(module='productos', action='leer')
def inventario_completo(request):
    # Leer parámetros de filtros
    nombre = request.GET.get("nombre", "").strip()
    categoria_id = request.GET.get("categoria", "").strip()
    proveedor_id = request.GET.get("proveedor", "").strip()
    estado = request.GET.get("estado", "").strip()
    exportar = request.GET.get("exportar") == "1"
    # Consulta base con productos activos/inactivos
    productos = Producto.objects.select_related('categoria', 'proveedor', 'almacen').all()
    # Aplicar filtros
    if nombre:
        productos = productos.filter(nombre__icontains=nombre)
    if categoria_id:
        productos = productos.filter(categoria__id=categoria_id)
    if proveedor_id:
        productos = productos.filter(proveedor__id=proveedor_id)
    if estado:
        productos = productos.filter(estado=(estado == "activo"))
    # Calcular totales (ej. stock total)
    total_productos = productos.count()
    total_stock = productos.aggregate(total=Sum('cantidad'))['total'] or 0
    consulta_realizada = any([nombre, categoria_id, proveedor_id, estado])
    # Exportar a PDF si se solicita
    if exportar:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        title = Paragraph("Reporte de Inventario Completo", styles['Heading1'])
        elements.append(title)
        data = [['Nombre', 'SKU', 'Categoría', 'Proveedor', 'Stock', 'Estado']]
        for prod in productos:
            data.append([
                prod.nombre,
                prod.sku,
                prod.categoria.nombre if prod.categoria else '-',
                prod.proveedor.nombre if prod.proveedor else '-',
                str(prod.cantidad),
                'Activo' if prod.estado else 'Inactivo'
            ])
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.skyblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)
        doc.build(elements)
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename="inventario_completo.pdf")
    # Datos para filtros en template
    categorias = Categoria.objects.all()
    proveedores = Proveedor.objects.all()
    return render(request, 'account/inventario_completo.html', {
        'productos': productos,
        'consulta_realizada': consulta_realizada,
        'categorias': categorias,
        'proveedores': proveedores,
        'total_productos': total_productos,
        'total_stock': total_stock,
    })

@login_required_custom
@role_required(module='usuarios', action='leer')
def reporte_usuarios(request):
    nombre = request.GET.get("nombre", "").strip()
    estado = request.GET.get("estado", "").strip()
    exportar = request.GET.get("exportar") == "1"
    usuarios = Usuario.objects.all()
    if nombre:
        usuarios = usuarios.filter(username__icontains=nombre)
    if estado:
        usuarios = usuarios.filter(estado=(estado == "activo"))
    total_usuarios = usuarios.count()
    consulta_realizada = any([nombre, estado])
    if exportar:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        title = Paragraph("Reporte de Usuarios", styles['Heading1'])
        elements.append(title)
        data = [['Username', 'Nombres', 'Apellidos', 'Rol', 'Estado']]
        for user in usuarios:
            data.append([
                user.username,
                user.nombres or '-',
                user.apellidos or '-',
                user.rol.nombre if user.rol else '-',
                'Activo' if user.estado else 'Inactivo'
            ])
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.skyblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)
        doc.build(elements)
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename="reporte_usuarios.pdf")
    return render(request, 'account/reporte_usuarios.html', {
        'usuarios': usuarios,
        'consulta_realizada': consulta_realizada,
        'total_usuarios': total_usuarios,
    })

@login_required_custom
@role_required(module='proveedores', action='leer')
def reporte_proveedores(request):
    nombre = request.GET.get("nombre", "").strip()
    estado = request.GET.get("estado", "").strip()
    exportar = request.GET.get("exportar") == "1"
    proveedores = Proveedor.objects.all()
    if nombre:
        proveedores = proveedores.filter(nombre__icontains=nombre)
    if estado:
        proveedores = proveedores.filter(estado=(estado == "activo"))
    total_proveedores = proveedores.count()
    consulta_realizada = any([nombre, estado])
    if exportar:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        title = Paragraph("Reporte de Proveedores", styles['Heading1'])
        elements.append(title)
        data = [['Nombre', 'Contacto', 'Teléfono', 'Email', 'Estado']]
        for prov in proveedores:
            data.append([
                prov.nombre,
                prov.contacto or '-',
                prov.telefono or '-',
                prov.email or '-',
                'Activo' if prov.estado else 'Inactivo'
            ])
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.skyblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)
        doc.build(elements)
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename="reporte_proveedores.pdf")
    return render(request, 'account/reporte_proveedores.html', {
        'proveedores': proveedores,
        'consulta_realizada': consulta_realizada,
        'total_proveedores': total_proveedores,
    })

@login_required_custom
@role_required(module='almacenes', action='leer')
def reporte_almacenes(request):
    nombre = request.GET.get("nombre", "").strip()
    estado = request.GET.get("estado", "").strip()
    exportar = request.GET.get("exportar") == "1"
    almacenes = Almacen.objects.select_related('responsable').all()
    if nombre:
        almacenes = almacenes.filter(nombre__icontains=nombre)
    if estado:
        almacenes = almacenes.filter(estado=(estado == "activo"))
    total_almacenes = almacenes.count()
    consulta_realizada = any([nombre, estado])
    if exportar:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        title = Paragraph("Reporte de Almacenes", styles['Heading1'])
        elements.append(title)
        data = [['Nombre', 'Número', 'Ubicación', 'Responsable', 'Estado']]
        for alm in almacenes:
            data.append([
                alm.nombre,
                alm.numero or '-',
                alm.ubicacion or '-',
                alm.responsable.username if alm.responsable else '-',
                'Activo' if alm.estado else 'Inactivo'
            ])
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.skyblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)
        doc.build(elements)
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename="reporte_almacenes.pdf")
    return render(request, 'account/reporte_almacenes.html', {
        'almacenes': almacenes,
        'consulta_realizada': consulta_realizada,
        'total_almacenes': total_almacenes,
    })

@login_required_custom
@role_required(module='categorias', action='leer')
def reporte_categorias(request):
    nombre = request.GET.get("nombre", "").strip()
    estado = request.GET.get("estado", "").strip()
    exportar = request.GET.get("exportar") == "1"
    categorias = Categoria.objects.all()
    if nombre:
        categorias = categorias.filter(nombre__icontains=nombre)
    if estado:
        categorias = categorias.filter(estado=(estado == "activo"))
    total_categorias = categorias.count()
    consulta_realizada = any([nombre, estado])
    if exportar:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        title = Paragraph("Reporte de Categorías", styles['Heading1'])
        elements.append(title)
        data = [['Nombre', 'Descripción', 'Icono', 'Estado']]
        for cat in categorias:
            data.append([
                cat.nombre,
                cat.descripcion or '-',
                cat.icono,
                'Activo' if cat.estado else 'Inactivo'
            ])
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.skyblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)
        doc.build(elements)
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename="reporte_categorias.pdf")
    return render(request, 'account/reporte_categorias.html', {
        'categorias': categorias,
        'consulta_realizada': consulta_realizada,
        'total_categorias': total_categorias,
    })

@login_required_custom
@role_required(module='roles', action='leer')
def reporte_roles(request):
    nombre = request.GET.get("nombre", "").strip()
    estado = request.GET.get("estado", "").strip()
    exportar = request.GET.get("exportar") == "1"
    roles = Rol.objects.all()
    if nombre:
        roles = roles.filter(nombre__icontains=nombre)
    if estado:
        roles = roles.filter(estado=(estado == "activo"))
    total_roles = roles.count()
    consulta_realizada = any([nombre, estado])
    if exportar:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        title = Paragraph("Reporte de Roles", styles['Heading1'])
        elements.append(title)
        data = [['Nombre', 'Descripción', 'Permisos', 'Estado']]
        for rol in roles:
            data.append([
                rol.nombre,
                rol.descripcion or '-',
                rol.permisos,
                'Activo' if rol.estado else 'Inactivo'
            ])
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.skyblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)
        doc.build(elements)
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename="reporte_roles.pdf")
    return render(request, 'account/reporte_roles.html', {
        'roles': roles,
        'consulta_realizada': consulta_realizada,
        'total_roles': total_roles,
    })
    
# ====================================================
# --- Funciones para Reportes --- lógica para ventas, Kardex y reporte.
# ====================================================

@login_required_custom
@role_required(module='ventas', action='leer')
def ventas_listar(request):
    ventas = Venta.objects.select_related('usuario').prefetch_related('detalleventa_set__producto').all().order_by('-fecha')  # Agrega prefetch para detalles
    permisos = {
        'leer': _user_has_permission(request.user, 'ventas', 'leer'),
        'crear': _user_has_permission(request.user, 'ventas', 'crear'),
    }
    return render(request, 'account/ventas_listar.html', {
        'ventas': ventas,
        'titulo': 'Lista de Ventas',
        'permisos': permisos,
    })

@login_required_custom
@role_required(module='ventas', action='crear')
def venta_crear(request):
    if request.method == 'POST':
        productos_ids = []
        cantidades = []
        for key, value in request.POST.items():
            if key.startswith('productos[') and value:
                productos_ids.append(value)
            elif key.startswith('cantidades[') and value:
                cantidades.append(int(value))
        
        if not productos_ids or not cantidades or len(productos_ids) != len(cantidades):
            messages.error(request, 'Debe agregar al menos un producto con cantidad válida.')
            return redirect('venta_crear')
        
        venta = Venta.objects.create(usuario=request.user, total=0)
        total = 0
        for prod_id, cant in zip(productos_ids, cantidades):
            try:
                prod = Producto.objects.get(id=prod_id)
                stock_anterior = prod.cantidad
                if prod.reducir_stock(cant):
                    precio_en_cop = prod.precio_en_cop()  # Nuevo: precio convertido a COP
                    DetalleVenta.objects.create(venta=venta, producto=prod, cantidad=cant, precio_unitario=precio_en_cop)
                    Kardex.objects.create(
                        producto=prod, 
                        tipo='salida', 
                        cantidad=cant,  # Positivo
                        stock_anterior=stock_anterior, 
                        motivo='venta', 
                        usuario=request.user,
                        fecha=venta.fecha  # ← AGREGAR ESTO: Fuerza la fecha exacta de la venta
                    )
                    total += precio_en_cop * cant  # Suma en COP
                else:
                    messages.error(request, f'Stock insuficiente para {prod.nombre}.')
                    return redirect('venta_crear')
            except Producto.DoesNotExist:
                messages.error(request, 'Producto no encontrado.')
                return redirect('venta_crear')
        venta.total = total
        venta.save()
        messages.success(request, 'Venta realizada exitosamente.')
        return redirect('ventas_listar')
    
    productos = Producto.objects.filter(estado=True)
    return render(request, 'account/venta_form.html', {'productos': productos, 'titulo': 'Nueva Venta'})


@login_required_custom
@role_required(module='productos', action='leer')  # Asumir permisos en productos
def kardex(request):
    producto_id = request.GET.get('producto')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    kardex_entries = Kardex.objects.all().order_by('fecha')  # Ordenar por fecha
    
    if producto_id:
        kardex_entries = kardex_entries.filter(producto_id=producto_id)
    if fecha_inicio:
        kardex_entries = kardex_entries.filter(fecha__date__gte=fecha_inicio)
    if fecha_fin:
        kardex_entries = kardex_entries.filter(fecha__date__lte=fecha_fin)
    productos = Producto.objects.all()
    return render(request, 'account/kardex.html', {
        'kardex_entries': kardex_entries,
        'productos': productos,
        'producto_id': producto_id,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    })

@login_required_custom
@role_required(module='ventas', action='leer')
def reporte_ventas(request):
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    producto_id = request.GET.get('producto')
    exportar = request.GET.get('exportar') == '1'
    ventas = Venta.objects.select_related('usuario').prefetch_related('detalleventa_set__producto').all()
    if fecha_inicio:
        fecha_inicio_aware = make_aware(datetime.strptime(fecha_inicio, '%Y-%m-%d'))
        ventas = ventas.filter(fecha__gte=fecha_inicio_aware)
    if fecha_fin:
        # Para fecha_fin, incluir todo el día agregando 23:59:59
        fecha_fin_aware = make_aware(datetime.strptime(fecha_fin + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
        ventas = ventas.filter(fecha__lte=fecha_fin_aware)
    if producto_id:
        ventas = ventas.filter(detalleventa__producto_id=producto_id).distinct()
    total_ventas = ventas.count()
    consulta_realizada = any([fecha_inicio, fecha_fin, producto_id])
    
    # Crear diccionario de movimientos por venta
    movimientos_por_venta = {}
    for venta in ventas:
        kardex_filter = Kardex.objects.filter(
            producto__in=venta.detalleventa_set.values_list('producto', flat=True),
            fecha__date=venta.fecha.date()  # Solo día, sin hora
        )
        if producto_id:  # Si hay filtro por producto, limita movimientos a ese producto
            kardex_filter = kardex_filter.filter(producto_id=producto_id)
        movimientos_por_venta[venta.id] = kardex_filter.order_by('fecha')
        
        # ← MOVER EL PRINT AQUÍ (después de asignar el valor)
        movimientos = movimientos_por_venta[venta.id]
        print(f"Venta {venta.id}: {movimientos.count()} movimientos")
    
    productos = Producto.objects.all()  # Para el dropdown de productos
    
    if exportar:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title = Paragraph("Reporte de Ventas", styles['Heading1'])
        elements.append(title)
        
        # Tabla de Ventas
        data_ventas = [['Fecha', 'Usuario', 'Productos', 'Total']]
        for v in ventas:
            productos_str = ', '.join([f"{d.producto.nombre} (Cant: {d.cantidad}, Precio: ${d.precio_unitario})" for d in v.detalleventa_set.all()])
            data_ventas.append([v.fecha.strftime('%Y-%m-%d'), v.usuario.username, productos_str, str(v.total)])
        table_ventas = Table(data_ventas)
        table_ventas.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.skyblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table_ventas)
        
        # Espacio
        elements.append(Paragraph("<br/><br/>", styles['Normal']))
        
        # Título de Movimientos
        title_mov = Paragraph("Movimientos de Kardex", styles['Heading2'])
        elements.append(title_mov)
        
        # Tabla de Movimientos
        data_mov = [['Producto', 'Tipo', 'Stock Anterior', 'Cantidad Movida', 'Stock Actual', 'Motivo', 'Fecha']]
        for v in ventas:
            movimientos = movimientos_por_venta.get(v.id, [])
            for m in movimientos:
                data_mov.append([
                    m.producto.nombre, m.tipo, str(m.stock_anterior), str(m.cantidad), str(m.stock_actual()), m.motivo, m.fecha.strftime('%Y-%m-%d %H:%M')
                ])
        if data_mov:
            table_mov = Table(data_mov)
            table_mov.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
            ]))
            elements.append(table_mov)
        doc.build(elements)
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename="reporte_ventas.pdf")
    return render(request, 'account/reporte_ventas.html', {
        'ventas': ventas,
        'movimientos_por_venta': movimientos_por_venta,
        'productos': productos,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'producto_id': producto_id,
        'consulta_realizada': consulta_realizada,
        'total_ventas': total_ventas,
    })
    
@login_required_custom
@role_required(module='ventas', action='actualizar')
def venta_editar(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == 'POST':
        # Lógica simple: permite editar cantidad en detalles (ejemplo básico)
        # Nota: Para producción, valida cambios y actualiza stock/Kardex si es necesario
        for key, value in request.POST.items():
            if key.startswith('cantidades['):
                # Aquí podrías actualizar cantidades, pero simplifica por ahora
                pass
        messages.success(request, 'Venta actualizada exitosamente.')
        return redirect('ventas_listar')
    productos = Producto.objects.filter(estado=True)
    return render(request, 'account/venta_form.html', {'productos': productos, 'venta': venta, 'titulo': 'Editar Venta', 'editar': True})

@login_required_custom
@role_required(module='ventas', action='eliminar')
def venta_eliminar(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == 'POST':
        venta.estado = False  # Desactiva en lugar de eliminar
        venta.save()
        messages.success(request, f'Venta "{venta.id}" desactivada correctamente.')
        return redirect('ventas_listar')
    return render(request, 'account/venta_confirmar_eliminar.html', {'venta': venta})
    
# ====================================================
# --- Funciones para Logs ---
# ====================================================
@login_required_custom
def logs_api(request):
    logs = Log.objects.all().order_by('-fecha')  # Sin límite, todos los logs
    data = [{'detalles': log.detalles, 'fecha': str(log.fecha)} for log in logs]
    return JsonResponse(data, safe=False)