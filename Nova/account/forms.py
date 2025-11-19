from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm, UserChangeForm # Importar formularios de usuario de Django
from .models import Producto, Categoria, Proveedor, Almacen, Rol, Usuario

class LoginForm(forms.Form):
    username = forms.CharField(
        label='Usuario',
        widget=forms.TextInput(attrs={
            'placeholder': 'Nombre de usuario',
            'class': 'login__input',
            'autocomplete': 'username',
            'required': 'required'
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Contraseña',
            'class': 'login__input',
            'autocomplete': 'current-password',
            'required': 'required'
        })
    )

# Usaremos UserCreationForm para crear usuarios y UserChangeForm para editar
# Esto simplifica el manejo de contraseñas y validaciones de Django.
class CustomUserCreationForm(UserCreationForm):
    nombres = forms.CharField(max_length=100, required=True, label='Nombres')
    apellidos = forms.CharField(max_length=100, required=True, label='Apellidos')
    rol = forms.ModelChoiceField(
        queryset=Rol.objects.all(),
        required=True,
        label="Rol"
    )
    estado = forms.BooleanField(required=False, initial=True, label='Activo')

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = UserCreationForm.Meta.fields + ('nombres', 'apellidos', 'email', 'rol', 'estado')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and Usuario.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Ya existe un usuario con este email.")
        return email

    def save(self, commit=True):
        """Crea el usuario con la contraseña cifrada correctamente."""
        user = super().save(commit=False)
        if commit:
            user.save()
        return user




class CustomUserChangeForm(UserChangeForm):
    nombres = forms.CharField(max_length=100, required=True, label='Nombres')
    apellidos = forms.CharField(max_length=100, required=True, label='Apellidos')
    rol = forms.ModelChoiceField(
        queryset=Rol.objects.all(),
        required=True,
        label="Rol"
    )
    estado = forms.BooleanField(required=False, label='Activo')

    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text="Deja en blanco si no deseas cambiarla."
    )

    class Meta(UserChangeForm.Meta):
        model = Usuario
        fields = ('username', 'nombres', 'apellidos', 'email', 'rol', 'estado', 'password')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and Usuario.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Ya existe un usuario con este email.")
        return email

    def save(self, commit=True):
        """Cifra la nueva contraseña o conserva la actual si está vacía."""
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')

        if password:
            user.set_password(password)
        elif self.instance.pk:
            # Mantener la contraseña anterior si no se cambió
            old_user = Usuario.objects.get(pk=self.instance.pk)
            user.password = old_user.password

        if commit:
            user.save()
        return user



class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = '__all__'
        labels = {
            'nombre': 'Nombre del producto',
            'descripcion': 'Descripción',
            'categoria': 'Categoría',
            'precio_unitario': 'Precio unitario',
            'moneda': 'Moneda',
            'cantidad': 'Cantidad',
            'unidad': 'Unidad de medida',
            'sku': 'Código SKU',
            'proveedor': 'Proveedor',
            'almacen': 'Almacén',
            'estado': 'Estado',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej: Detergente'}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Detalles del producto'}),
            'precio_unitario': forms.NumberInput(attrs={'placeholder': 'Ej: 1000.00'}),
            'cantidad': forms.NumberInput(attrs={'placeholder': 'Ej: 50'}),
            'unidad': forms.Select(choices=Producto.UNIDAD_CHOICES),
            'sku': forms.TextInput(attrs={'placeholder': 'Ej: PROD-001'}),
            'estado': forms.Select(choices=[(True, 'Activo'), (False, 'Inactivo')]),
            'moneda': forms.Select(choices=Producto.MONEDA_CHOICES),
        }

class AlmacenForm(forms.ModelForm):
    class Meta:
        model = Almacen
        fields = '__all__'
        labels = {
            'nombre': 'Nombre del almacén',
            'numero': 'Número de identificación',
            'ubicacion': 'Ubicación física',
            'capacidad': 'Capacidad (m²)',
            'responsable': 'Responsable del almacén',
            'estado': 'Estado',
        }
        widgets = {
            'estado': forms.Select(choices=[(True, 'Activo'), (False, 'Inactivo')]),
            'ubicacion': forms.Textarea(attrs={'rows': 2}),
            'capacidad': forms.NumberInput(attrs={'step': '0.01'}),
        }

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = '__all__'
        labels = {
            'nombre': 'Nombre de la empresa',
            'contacto': 'Persona de contacto',
            'telefono': 'Teléfono',
            'email': 'Email',
            'direccion': 'Dirección',
            'nit': 'NIT',
            'estado': 'Estado',
        }
        widgets = {
            'estado': forms.Select(choices=[(True, 'Activo'), (False, 'Inactivo')]),
            'direccion': forms.Textarea(attrs={'rows': 2}),
        }

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        exclude = ['icono']  # 👈 ya no pedirá el campo icono
        labels = {
            'nombre': 'Nombre de la categoría',
            'descripcion': 'Descripción',
            'estado': 'Estado',
        }
        widgets = {
            'estado': forms.Select(choices=[(True, 'Activo'), (False, 'Inactivo')]),
            'descripcion': forms.Textarea(attrs={'rows': 2}),
        }

class RolForm(forms.ModelForm):
    class Meta:
        model = Rol
        fields = ['nombre', 'descripcion', 'permisos']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del rol'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'permisos': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'crear_producto, editar_producto'}),
        }

class VentaForm(forms.Form):
    productos = forms.ModelMultipleChoiceField(queryset=Producto.objects.filter(estado=True), widget=forms.CheckboxSelectMultiple)
    cantidades = forms.CharField(widget=forms.HiddenInput)  # Manejar dinámicamente en template
class KardexForm(forms.Form):
    producto = forms.ModelChoiceField(queryset=Producto.objects.all(), required=False)
