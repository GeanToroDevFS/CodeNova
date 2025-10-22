from django.db import models
from django.contrib.auth.models import AbstractUser 
from django.utils import timezone

class Usuario(AbstractUser):
    rol = models.ForeignKey('Rol', on_delete=models.SET_NULL, null=True, blank=True)
    estado = models.BooleanField(default=True)
    nombres = models.CharField(max_length=100, blank=True, null=True)
    apellidos = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def get_full_name(self):
        if self.nombres and self.apellidos:
            return f"{self.nombres} {self.apellidos}".strip()
        return super().get_full_name()

    def get_short_name(self):
        return self.nombres if self.nombres else super().get_short_name()

    def save(self, *args, **kwargs):
        """
        Ajusta flags de superusuario/empleado solo si el rol es 'Administrador'.
        Otros roles no modifican estos flags para evitar bloquear el login normal.
        """
        try:
            if self.rol and isinstance(self.rol.nombre, str):
                nombre = self.rol.nombre.strip().lower()
                if nombre in ['administrador', 'admin']:
                    self.is_superuser = True
                    self.is_staff = True
                else:
                    # Resetear flags cuando no es administrador
                    self.is_superuser = False
                    self.is_staff = False
        except Exception:
            pass  # Evita romper el guardado si el rol no existe
        super().save(*args, **kwargs)


class Rol(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    permisos = models.TextField(blank=True, default='')  # TextField para strings custom (e.g., 'gestionar_usuarios, productos_leer')

    estado = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

    def get_permisos_list(self):
        if not self.permisos:
            return []
        return [p.strip().lower() for p in self.permisos.split(',') if p.strip()]


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    estado = models.BooleanField(default=True)
    icono = models.CharField(max_length=50, default='tag')

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']


class Proveedor(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    contacto = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    nit = models.CharField(max_length=20, unique=True, blank=True, null=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['nombre']


class Almacen(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    numero = models.CharField(max_length=20, unique=True, blank=True, null=True)
    ubicacion = models.TextField(blank=True, null=True)
    capacidad = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    responsable = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.numero if self.numero else 'N/A'})"

    class Meta:
        verbose_name = 'Almacén'
        verbose_name_plural = 'Almacenes'
        ordering = ['nombre']


class Producto(models.Model):
    UNIDAD_CHOICES = [
        ('kg', 'Kilogramo'),
        ('ml', 'Mililitro'),
        ('litro', 'Litro'),
        ('unidad', 'Unidad'),
    ]
    MONEDA_CHOICES = [
        ('USD', 'Dólar estadounidense'),
        ('COP', 'Peso colombiano'),
        ('EUR', 'Euro'),
    ]

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    moneda = models.CharField(max_length=3, choices=MONEDA_CHOICES, default='COP')
    cantidad = models.PositiveIntegerField(default=0)
    unidad = models.CharField(max_length=20, choices=UNIDAD_CHOICES, default='unidad')
    sku = models.CharField(max_length=100, unique=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True)
    almacen = models.ForeignKey(Almacen, on_delete=models.SET_NULL, null=True, blank=True)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} ({self.sku})"

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']
