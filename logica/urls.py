from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name="inicio"),
    path('login/', views.login_view, name="login"),
    path('logout/', views.logout_view, name="logout"),
    path('register/', views.register_view, name="register"),
    path('ajax/municipios/', views.get_municipios, name='ajax_municipios'),
    path('ajax/circunscripciones/', views.get_circunscripciones, name='ajax_circunscripciones'),
    path('productos_categoría/<int:id>', views.productos_categoría, name="productos_categoría"),
    path('detalle_producto/<int:id>/', views.detalle_producto, name="detalle_producto"),
    path('detalle_producto_sin_log/<int:id>/', views.detalle_producto_sin_log, name="detalle_producto_sin_log"),
    path('producto/<int:producto_id>/agregar-carrito/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('producto/<int:producto_id>/agregar_resena/', views.agregar_resena, name='agregar_resena'),
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
    path('cambiar-contrasena/', views.cambiar_contrasena, name='cambiar_contrasena'),
    path('crear_pedido/', views.crear_pedido, name='crear_pedido'),
    path('detalle_pedido/<int:pedido_id>/', views.detalle_pedido, name='detalle_pedido'),
    path('cancelar_pedido/<int:pedido_id>/', views.cancelar_pedido, name='cancelar_pedido'),
    path('historial_pedidos/', views.historial_pedidos, name='historial_pedidos'),
    path('admin-pedidos/', views.admin_historial_pedidos, name='admin_historial_pedidos'),
    path('admin-pedidos/<int:pedido_id>/', views.admin_detalle_pedido, name='admin_detalle_pedido'),
    path('admin-pedidos/<int:pedido_id>/cambiar_estado/', views.admin_cambiar_estado_pedido, name='admin_cambiar_estado_pedido'),
]