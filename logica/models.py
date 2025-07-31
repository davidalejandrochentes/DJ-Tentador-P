from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
import os
from django.utils.text import slugify

class Provincia(models.Model):
    nombre = models.CharField(max_length=25, blank=False, null=False)

    def __str__(self):
        return self.nombre


class Municipio(models.Model):
    provincia = models.ForeignKey(Provincia, on_delete=models.CASCADE, related_name='municipios', null=False, blank=False)
    nombre = models.CharField(max_length=30, blank=False, null=False)

    def __str__(self):
        return self.nombre


class Zona(models.Model):
    municipio = models.ForeignKey(Municipio, on_delete=models.CASCADE, related_name='circunscripciones', null=False, blank=False)
    nombre = models.CharField(max_length=40, blank=False, null=False)
    costo_envio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Coste de envío", blank=False, null=False)

    def __str__(self):
        return self.nombre


class Usuario(AbstractUser):
    provincia = models.ForeignKey(Provincia, on_delete=models.CASCADE, null=True, blank=True, related_name='usuarios')
    municipio = models.ForeignKey(Municipio, on_delete=models.CASCADE, null=True, blank=True, related_name='usuarios')
    zona = models.ForeignKey(Zona, on_delete=models.CASCADE, null=True, blank=True, related_name='usuarios')
    teléfono = models.CharField(max_length=15, blank=True, null=True)
    dirección = models.CharField(max_length=255, blank=True, null=True)
    COMO_NOS_CONOCIO_CHOICES = [
        ('amigo', 'Por un amigo'),
        ('redes', 'Redes sociales'),
        ('busqueda', 'Búsqueda en internet'),
        ('otros', 'Otros'),
    ]
    cómo_nos_conoció = models.CharField(max_length=10, choices=COMO_NOS_CONOCIO_CHOICES, blank=True, null=True)

    def __str__(self):
        return self.username


class Categoría(models.Model):
    nombre = models.CharField(max_length=50, unique=True, null=False, blank=False)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    imagen = models.ImageField(upload_to='categoría/', null=False, blank=False)
    descripción = models.TextField(null=False, blank=False)
    municipio = models.ForeignKey(Municipio, on_delete=models.CASCADE, related_name='categorías', null=False, blank=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=100, null=False, blank=False)
    descripción = models.TextField(null=False, blank=False)
    descripción_corta = models.TextField(null=False, blank=False)
    precio = models.DecimalField(max_digits=8, decimal_places=2, null=False, blank=False)
    disponible = models.BooleanField(default=True)
    imagen = models.ImageField(upload_to='productos/', null=False, blank=False)
    categoría = models.ForeignKey(Categoría, on_delete=models.SET_NULL, related_name='productos', null=True, blank=True)
    municipio = models.ForeignKey(Municipio, on_delete=models.CASCADE, related_name='productos', null=False, blank=False)
    productos_relacionados = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='relacionados_con',
        verbose_name="Productos relacionados"
    )
    puntuación = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Puntuación (1 a 5)"
    )

    def __str__(self):
        return self.nombre


class Reseña(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='reseñas', null=False, blank=False)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='reseñas', null=False, blank=False)
    aprobada = models.BooleanField(default=False)
    puntuación = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Puntuación (1 a 5)"
    )
    comentario = models.TextField(null=False, blank=False)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'producto')
        ordering = ['-fecha']  # muestra las más recientes primero

    def __str__(self):
        return f"{self.usuario.username} - {self.producto.nombre} ({self.puntuación} estrellas)"


class Carrito(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='carrito')

    def total(self):
        return sum(item.total() for item in self.items.all())

    def __str__(self):
        return f"Carrito de {self.usuario.username}"


class CarritoItem(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('carrito', 'producto')

    def total(self):
        return self.cantidad * self.producto.precio

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"


class Pedido(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('preparando', 'Preparando'),
        ('en_camino', 'En camino'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='pedidos')
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    dirección_entrega = models.CharField(max_length=255)
    costo_envio = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Pedido #{self.id} de {self.usuario.username}"


class PedidoItem(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=8, decimal_places=2)

    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"


#------------------------------------------------------------------------------
#------------------------------------------------------------------------------


@receiver(pre_delete, sender=Producto)
def eliminar_imagen_de_producto(sender, instance, **kwargs):
    # Verificar si el producto tiene una imagen asociada y eliminarla
    if instance.imagen:
        if os.path.isfile(instance.imagen.path):
            os.remove(instance.imagen.path)

@receiver(pre_save, sender=Producto)
def eliminar_imagen_anterior_al_actualizar(sender, instance, **kwargs):
    if not instance.pk:  # El producto es nuevo, no hay imagen anterior que eliminar
        return False

    try:
        producto_anterior = Producto.objects.get(pk=instance.pk)  # Obtener el producto anterior de la base de datos
    except Producto.DoesNotExist:
        return False  # El producto anterior no existe, no hay imagen anterior que eliminar

    if producto_anterior.imagen:  # Verificar si el producto anterior tiene una imagen
        nueva_imagen = instance.imagen
        if producto_anterior.imagen != nueva_imagen:  # Verificar si se ha seleccionado una nueva imagen
            if os.path.isfile(producto_anterior.imagen.path):  # Verificar si el archivo de imagen existe en el sistema de archivos
                os.remove(producto_anterior.imagen.path)


@receiver(pre_delete, sender=Categoría)
def eliminar_imagen_de_categoría(sender, instance, **kwargs):
    # Verificar si la categoría tiene una imagen asociada y eliminarla
    if instance.imagen:
        if os.path.isfile(instance.imagen.path):
            os.remove(instance.imagen.path)

@receiver(pre_save, sender=Categoría)
def eliminar_imagen_anterior_al_actualizar(sender, instance, **kwargs):
    if not instance.pk:  # La Categoría es nuevo, no hay imagen anterior que eliminar
        return False

    try:
        categoría_anterior = Categoría.objects.get(pk=instance.pk)  # Obtener la categoría anterior de la base de datos
    except Categoría.DoesNotExist:
        return False  # La categoría anterior no existe, no hay imagen anterior que eliminar

    if categoría_anterior.imagen:  # Verificar si la categoría anterior tiene una imagen
        nueva_imagen = instance.imagen
        if categoría_anterior.imagen != nueva_imagen:  # Verificar si se ha seleccionado una nueva imagen
            if os.path.isfile(categoría_anterior.imagen.path):  # Verificar si el archivo de imagen existe en el sistema de archivos
                os.remove(categoría_anterior.imagen.path)
