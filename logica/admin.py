from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Provincia, Municipio, Usuario, Zona, 
    Categoría, Producto, Carrito, CarritoItem, 
    Pedido, PedidoItem, Reseña
)

# Register your models here.

# Modelos ya registrados anteriormente
@admin.register(Provincia)
class ProvinciaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Municipio)
class MunicipioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'provincia')
    list_filter = ('provincia',)
    search_fields = ('nombre', 'provincia__nombre')

@admin.register(Zona)
class ZonaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'municipio', 'costo_envio')
    list_filter = ('municipio', 'municipio__provincia')
    search_fields = ('nombre', 'municipio__nombre', 'municipio__provincia__nombre')

@admin.register(Usuario)
class CustomUsuarioAdmin(UserAdmin):
    model = Usuario
    list_display = ('username','first_name', 'last_name', 'teléfono', 'provincia', 'municipio', 'zona')
    list_filter = ('provincia', 'municipio', 'zona')
    fieldsets = UserAdmin.fieldsets + (
        ('Información Adicional', {
            'fields': ('provincia', 'municipio', 'zona', 'teléfono', 'dirección', 'cómo_nos_conoció')
        }),
    )

# Modelos nuevos
@admin.register(Categoría)
class CategoríaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'slug', 'municipio')
    prepopulated_fields = {'slug': ('nombre',)}
    list_filter = ('municipio',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'disponible', 'categoría', 'municipio')
    list_filter = ('disponible', 'categoría', 'municipio')
    search_fields = ('nombre', 'descripción')

@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ('usuario',)

@admin.register(CarritoItem)
class CarritoItemAdmin(admin.ModelAdmin):
    list_display = ('carrito', 'producto', 'cantidad')
    list_filter = ('carrito', 'producto')

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'fecha', 'estado', 'total')
    list_filter = ('estado', 'fecha')
    search_fields = ('usuario__username', 'dirección_entrega')

@admin.register(PedidoItem)
class PedidoItemAdmin(admin.ModelAdmin):
    list_display = ('pedido', 'producto', 'cantidad', 'precio_unitario')
    list_filter = ('pedido', 'producto')

@admin.register(Reseña)
class ReseñaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'producto', 'puntuación', 'aprobada', 'fecha')
    list_filter = ('puntuación', 'fecha')
    search_fields = ('comentario',)
