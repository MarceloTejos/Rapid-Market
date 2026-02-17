from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class Usuario(models.Model):
    ROLES = (
        ('admin', 'Administrador'),
        ('cajero', 'Cajero'),
    )
    

    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    usuario = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=255)
    rol = models.CharField(max_length=20, choices=ROLES)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.usuario})"

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.nombre} - {self.categoria}"

class Venta(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)

class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)


from django.db import models

class Alerta(models.Model):
    TIPO_CHOICES = (
        ('BAJO_STOCK', 'Bajo stock'),
        ('REPOSICION_RECOMENDADA', 'Reposición recomendada'),
        ('TENDENCIA_VENTA', 'Tendencia de venta'),
    )
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE)
    tipo = models.CharField(max_length=40, choices=TIPO_CHOICES)
    mensaje = models.TextField()
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    leida = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.tipo} - {self.producto.nombre} - {self.fecha_generacion:%Y-%m-%d %H:%M}"


class KPIRecord(models.Model):
    fecha = models.DateField()
    quiebres_stock = models.IntegerField(default=0)
    ventas_totales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
