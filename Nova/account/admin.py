from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django import forms
from .models import Usuario, Rol, Categoria, Proveedor, Almacen, Producto, Venta, DetalleVenta, Kardex, Log 

class RolAdminForm(forms.ModelForm):
    class Meta:
        model = Rol
        fields = '__all__'
        widgets = {
            'permisos': forms.Textarea(attrs={'rows': 3, 'placeholder': 'E.g., gestionar_usuarios, productos_leer'}),
        }

@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    form = RolAdminForm
    list_display = ['nombre', 'descripcion_preview', 'creado_en']
    list_filter = ['creado_en']
    search_fields = ['nombre', 'descripcion']
    readonly_fields = ['creado_en', 'actualizado_en']

    def descripcion_preview(self, obj):
        return (obj.descripcion[:50] + '...') if len(obj.descripcion or '') > 50 else (obj.descripcion or '')
    descripcion_preview.short_description = 'Descripción'

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ['username', 'email', 'nombres', 'apellidos', 'rol', 'estado', 'is_superuser', 'date_joined']
    list_filter = ['rol', 'estado', 'is_superuser', 'is_staff', 'date_joined']
    search_fields = ['username', 'email', 'nombres', 'apellidos']
    fieldsets = UserAdmin.fieldsets + (
        ('Información Adicional', {'fields': ('nombres', 'apellidos', 'rol', 'estado')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información Adicional', {'fields': ('nombres', 'apellidos', 'rol', 'estado', 'password1', 'password2')}),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if change and obj.pk:
            obj.save(update_fields=['is_superuser', 'is_staff'])  # Trigger para actualizar basado en rol

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'estado', 'icono']
    list_filter = ['estado']
    search_fields = ['nombre', 'descripcion']

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'nit', 'estado', 'contacto']
    list_filter = ['estado']
    search_fields = ['nombre', 'nit', 'contacto', 'email']

@admin.register(Almacen)
class AlmacenAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'numero', 'responsable', 'estado']
    list_filter = ['estado']
    search_fields = ['nombre', 'numero', 'ubicacion']
    raw_id_fields = ['responsable']

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'sku', 'categoria', 'precio_unitario', 'moneda', 'cantidad', 'estado']
    list_filter = ['categoria', 'proveedor', 'almacen', 'moneda', 'estado', 'fecha_creacion']
    search_fields = ['nombre', 'sku', 'descripcion']
    raw_id_fields = ['categoria', 'proveedor', 'almacen']
    readonly_fields = ['fecha_creacion', 'fecha_modificacion']


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'fecha', 'total']

@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    list_display = ['venta', 'producto', 'cantidad', 'precio_unitario']

@admin.register(Kardex)
class KardexAdmin(admin.ModelAdmin):
    list_display = ['producto', 'tipo', 'cantidad', 'fecha', 'motivo']

@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'modelo', 'accion', 'fecha']