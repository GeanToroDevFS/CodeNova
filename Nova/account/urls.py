from django.urls import path
from .views import (
    user_login, user_logout, dashboard,
    lista_usuarios, crear_usuario, editar_usuario, eliminar_usuario,
    lista_proveedores, crear_proveedor, editar_proveedor, eliminar_proveedor,
    lista_categorias, crear_categoria, editar_categoria, eliminar_categoria,
    lista_almacenes, crear_almacen, editar_almacen, eliminar_almacen,
    productos_listar, producto_crear, producto_editar, producto_eliminar,
    roles_listar, roles_crear, roles_editar, roles_eliminar, informes_listar, inventario_completo,
    reporte_usuarios, reporte_proveedores, reporte_almacenes, reporte_categorias, reporte_roles,
    ventas_listar, venta_crear, kardex, reporte_ventas, logs_api,
)

urlpatterns = [
    path('', user_login, name='login'), # La raíz de la app 'account' es el login
    path('dashboard/', dashboard, name='dashboard'),
    path('logout/', user_logout, name='logout'),

    # Productos
    path('productos/', productos_listar, name='productos_listar'),
    path('productos/crear/', producto_crear, name='producto_crear'),
    path('productos/editar/<int:pk>/', producto_editar, name='producto_editar'),
    path('productos/eliminar/<int:pk>/', producto_eliminar, name='producto_eliminar'),

    # Usuarios
    path('usuarios/', lista_usuarios, name='usuarios_listar'),
    path('usuarios/nuevo/', crear_usuario, name='crear_usuario'),
    path('usuarios/editar/<int:pk>/', editar_usuario, name='editar_usuario'),
    path('usuarios/eliminar/<int:pk>/', eliminar_usuario, name='eliminar_usuario'),

    # Almacenes
    path('almacenes/', lista_almacenes, name='almacenes_listar'),
    path('almacenes/nuevo/', crear_almacen, name='crear_almacen'),
    path('almacenes/editar/<int:pk>/', editar_almacen, name='editar_almacen'),
    path('almacenes/eliminar/<int:pk>/', eliminar_almacen, name='eliminar_almacen'),

    # Proveedores
    path('proveedores/', lista_proveedores, name='proveedores_listar'),
    path('proveedores/nuevo/', crear_proveedor, name='crear_proveedor'),
    path('proveedores/editar/<int:pk>/', editar_proveedor, name='editar_proveedor'),
    path('proveedores/eliminar/<int:pk>/', eliminar_proveedor, name='eliminar_proveedor'),

    # Categorías
    path('categorias/', lista_categorias, name='categorias_listar'),
    path('categorias/nuevo/', crear_categoria, name='crear_categoria'),
    path('categorias/editar/<int:pk>/', editar_categoria, name='editar_categoria'),
    path('categorias/eliminar/<int:pk>/', eliminar_categoria, name='eliminar_categoria'),

    # Roles
    path('roles/', roles_listar, name='roles_listar'),
    path('roles/nuevo/', roles_crear, name='roles_crear'),
    path('roles/editar/<int:pk>/', roles_editar, name='roles_editar'),
    path('roles/eliminar/<int:pk>/', roles_eliminar, name='roles_eliminar'),
    
    #Informes
    path('informes/', informes_listar, name='informes_listar'),
    path('informes/inventario/', inventario_completo, name='inventario_completo'),
    path('informes/usuarios/', reporte_usuarios, name='reporte_usuarios'),
    path('informes/proveedores/', reporte_proveedores, name='reporte_proveedores'),
    path('informes/almacenes/', reporte_almacenes, name='reporte_almacenes'),
    path('informes/categorias/', reporte_categorias, name='reporte_categorias'),
    path('informes/roles/', reporte_roles, name='reporte_roles'),  
    
    # Ventas
    path('ventas/', ventas_listar, name='ventas_listar'),
    path('ventas/crear/', venta_crear, name='venta_crear'),
    
    # Kardex
    path('kardex/', kardex, name='kardex'),
    
    # Informes adicionales
    path('informes/ventas/', reporte_ventas, name='reporte_ventas'),
    
    # Logs
    path('api/logs/', logs_api, name='logs_api'),
]
