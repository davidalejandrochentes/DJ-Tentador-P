from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.template import context
from .forms import CustomUserCreationForm, ReseñaForm, UsuarioForm
from .models import Producto, Categoría, Reseña, Carrito, CarritoItem, Municipio, Zona, Pedido, PedidoItem
from django.http import JsonResponse
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.urls import reverse
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import models
from django.db import transaction
from django.conf import settings
from telegram import Bot
from telegram.error import TelegramError
import asyncio
import logging

logger = logging.getLogger(__name__)

def enviar_mensaje_telegram(mensaje):
    """Envía un mensaje de Telegram de forma asíncrona con manejo de errores."""
    async def send_message():
        try:
            bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
            await bot.send_message(
                chat_id=settings.TELEGRAM_CHAT_ID, 
                text=mensaje
            )
        except TelegramError as e:
            logger.error(f"Error enviando mensaje de Telegram: {e}")
    
    try:
        asyncio.run(send_message())
    except Exception as e:
        logger.error(f"Error en envío de mensaje de Telegram: {e}")

# Create your views here.
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username').lower()
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('inicio')
            else:
                messages.error(request, "Usuario o contraseña incorrectos.")
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
    form = AuthenticationForm()
    return render(request, 'logica/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('inicio')


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('inicio')
    else:
        form = CustomUserCreationForm()
    return render(request, 'logica/register.html', {'form': form})


def get_municipios(request):
    provincia_id = request.GET.get('provincia_id')
    municipios = Municipio.objects.filter(provincia_id=provincia_id).values('id', 'nombre')
    return JsonResponse(list(municipios), safe=False)


def get_circunscripciones(request):
    municipio_id = request.GET.get('municipio_id')
    circunscripciones = Zona.objects.filter(municipio_id=municipio_id).values('id', 'nombre')
    return JsonResponse(list(circunscripciones), safe=False)    


def inicio(request):
    productos = Producto.objects.filter(disponible=True).order_by('-puntuación', '-id')[:8]
    categorías = Categoría.objects.all().select_related('municipio')
    context = {
        'productos': productos,
        'categorías': categorías
    }
    return render(request, 'logica/index.html', context)


@login_required
def productos_categoría(request, id):
    productos = (
        Producto.objects
        .filter(categoría=id, municipio=request.user.municipio, disponible=True)
        .select_related('categoría')
        .order_by('-puntuación')
    )
    carrito, _ = Carrito.objects.get_or_create(
        usuario=request.user, 
        defaults={'usuario': request.user}
    )
    productos_en_carrito = set(carrito.items.values_list('producto_id', flat=True))
    return render(request, 'logica/productos_categoría.html', {
        'productos': productos,
        'productos_en_carrito': productos_en_carrito,
    })


@login_required
def detalle_producto(request, id):
    producto = get_object_or_404(
        Producto.objects
        .select_related('categoría')
        .prefetch_related('productos_relacionados', 'reseñas'),
        id=id, 
        municipio=request.user.municipio, 
        disponible=True
    )
    reseñas = producto.reseñas.filter(aprobada=True).select_related('usuario')
    relacionados = producto.productos_relacionados.filter(disponible=True)
    carrito, _ = Carrito.objects.get_or_create(
        usuario=request.user, 
        defaults={'usuario': request.user}
    )
    producto_en_carrito = carrito.items.filter(producto=producto).exists()
    return render(request, 'logica/detalles_producto.html', {
        'producto': producto,
        'reseñas': reseñas,
        'relacionados': relacionados,
        'producto_en_carrito': producto_en_carrito
    })


def detalle_producto_sin_log(request, id):
    producto = get_object_or_404(
        Producto.objects
        .select_related('categoría')
        .prefetch_related('productos_relacionados', 'reseñas'),
        id=id, 
        disponible=True
    )
    reseñas = producto.reseñas.filter(aprobada=True).select_related('usuario')
    relacionados = producto.productos_relacionados.filter(disponible=True)
    return render(request, 'logica/detalles_producto_sin_log.html', {
        'producto': producto,
        'reseñas': reseñas,
        'relacionados': relacionados
    })


@login_required
def agregar_resena(request, producto_id):
    producto = get_object_or_404(
        Producto.objects.select_related('categoría'), 
        id=producto_id
    )
    reseña_existente = Reseña.objects.filter(
        usuario=request.user, 
        producto=producto
    ).select_related('usuario', 'producto').first()
    if request.method == 'POST':
        form = ReseñaForm(request.POST, instance=reseña_existente)
        if form.is_valid():
            resena = form.save(commit=False)
            resena.usuario = request.user
            resena.producto = producto
            resena.aprobada = False
            resena.fecha = timezone.now()
            resena.save()
            return redirect('detalle_producto', id=producto.id)
    else:
        form = ReseñaForm(instance=reseña_existente)
    return render(request, 'logica/agregar_resena.html', {
        'form': form,
        'producto': producto,
        'editando': reseña_existente is not None
    })


@login_required
def perfil_usuario(request):
    usuario = request.user
    datos_actualizados = request.GET.get('datos_actualizados') == '1'
    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            return redirect(f"{reverse('perfil_usuario')}?datos_actualizados=1#top")
    else:
        form = UsuarioForm(instance=usuario)
    return render(request, 'logica/perfil_usuario.html', {
        'form': form,
        'datos_actualizados': datos_actualizados,
        'es_admin': usuario.is_staff,
    })



@login_required
def cambiar_contrasena(request):
    if request.method == 'POST':
        password_form = PasswordChangeForm(request.user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            return redirect(f"{reverse('cambiar_contrasena')}?password_actualizada=1#top")
    else:
        password_form = PasswordChangeForm(request.user)

    password_actualizada = request.GET.get('password_actualizada') == '1'
    return render(request, 'logica/cambiar_contrasena.html', {
        'password_form': password_form,
        'password_actualizada': password_actualizada
    })


@login_required
def agregar_al_carrito(request, producto_id):
    producto = get_object_or_404(
        Producto.objects
        .select_related('municipio', 'categoría'),
        id=producto_id, 
        municipio=request.user.municipio, 
        disponible=True
    )
    carrito, _ = Carrito.objects.get_or_create(
        usuario=request.user,
        defaults={'usuario': request.user}
    )
    item_existente = carrito.items.filter(producto=producto).first()
    if item_existente:
        item_existente.cantidad += 1
        item_existente.save()
    else:
        CarritoItem.objects.create(
            carrito=carrito, 
            producto=producto, 
            cantidad=1
        )
    if 'categoria_id' in request.POST:
        return redirect('productos_categoría', id=request.POST['categoria_id'])
    else:
        return redirect('detalle_producto', id=producto_id)


@login_required
def ver_carrito(request):
    carrito, _ = Carrito.objects.get_or_create(
        usuario=request.user,
        defaults={'usuario': request.user}
    )
    if request.method == 'POST':
        if 'actualizar_cantidad' in request.POST:
            item_id = request.POST.get('item_id')
            nueva_cantidad = int(request.POST.get('cantidad', 1))
            item = get_object_or_404(
                CarritoItem.objects.select_related('carrito', 'producto'), 
                id=item_id, 
                carrito=carrito
            )
            item.cantidad = nueva_cantidad
            item.save()
        elif 'eliminar_item' in request.POST:
            item_id = request.POST.get('item_id')
            item = get_object_or_404(
                CarritoItem.objects.select_related('carrito'), 
                id=item_id, 
                carrito=carrito
            )
            item.delete()
    carrito = Carrito.objects.prefetch_related(
        'items__producto'
    ).get(usuario=request.user)
    total = carrito.total()
    costo_envio = (
        request.user.zona.costo_envio 
        if request.user.zona 
        else 0
    )
    total_con_envio = total + costo_envio
    return render(request, 'logica/carrito.html', {
        'carrito': carrito,
        'total': total,
        'costo_envio': costo_envio,
        'total_con_envio': total_con_envio
    })


@login_required
def crear_pedido(request):
    carrito = get_object_or_404(
        Carrito.objects.prefetch_related('items__producto'), 
        usuario=request.user
    )
    if not carrito.items.exists():
        return redirect('ver_carrito')
    costo_envio = (
        request.user.zona.costo_envio 
        if request.user.zona 
        else 0
    )
    pedido = Pedido.objects.create(
        usuario=request.user,
        dirección_entrega=request.user.dirección or '',
        costo_envio=costo_envio,
        total=carrito.total() + costo_envio
    )
    pedido_items = [
        PedidoItem(
            pedido=pedido,
            producto=item_carrito.producto,
            cantidad=item_carrito.cantidad,
            precio_unitario=item_carrito.producto.precio
        ) for item_carrito in carrito.items.all()
    ]
    PedidoItem.objects.bulk_create(pedido_items)
    carrito.items.all().delete()
    
    # Calcular subtotal basado en los elementos del pedido
    subtotal = sum(item.cantidad * item.precio_unitario for item in pedido_items)
    
    mensaje = f"🛍️ *NUEVO PEDIDO* 🛍️\n\n" \
              f"*Detalles del Pedido*\n" \
              f"ID Pedido: {pedido.id}\n" \
              f"Usuario: {request.user.username}\n" \
              f"Nombre: {request.user.first_name}\n" \
              f"Apellidos: {request.user.last_name}\n" \
              f"Teléfono: {request.user.teléfono}\n" \
              f"Dirección de Entrega: {request.user.provincia}, {request.user.municipio}, {request.user.zona}, {pedido.dirección_entrega}\n\n" \
              f"*Productos*:\n"
    for item in pedido_items:
        mensaje += f"- {item.producto.nombre}: " \
                   f"{item.cantidad} x ${item.precio_unitario:.2f} " \
                   f"= ${item.cantidad * item.precio_unitario:.2f}\n"
    mensaje += f"\n*Resumen*:\n" \
               f"Subtotal: ${subtotal:.2f}\n" \
               f"Costo de Envío: ${costo_envio:.2f}\n" \
               f"*Total*: ${pedido.total:.2f}"
    
    enviar_mensaje_telegram(mensaje)
    return redirect('detalle_pedido', pedido_id=pedido.id)


@login_required
def detalle_pedido(request, pedido_id):
    pedido = get_object_or_404(
        Pedido.objects
        .select_related('usuario')
        .prefetch_related('items__producto'),
        id=pedido_id, 
        usuario=request.user
    )
    subtotal = sum(item.cantidad * item.precio_unitario for item in pedido.items.all())
    return render(request, 'logica/detalle_pedido.html', {
        'pedido': pedido,
        'subtotal': subtotal
    })


@login_required
def cancelar_pedido(request, pedido_id):
    pedido = get_object_or_404(
        Pedido.objects.select_related('usuario'), 
        id=pedido_id, 
        usuario=request.user
    )
    if pedido.estado == 'en_camino':
        return redirect('detalle_pedido', pedido_id=pedido.id)
    
    with transaction.atomic():
        pedido.estado = 'cancelado'
        pedido.save(update_fields=['estado'])
    
    # Calcular subtotal basado en los elementos del pedido
    subtotal = sum(item.cantidad * item.precio_unitario for item in pedido.items.all())
    
    # Notificación de Telegram para pedido cancelado
    mensaje = f"❌ *PEDIDO CANCELADO* ❌\n\n" \
              f"*Detalles del Pedido*\n" \
              f"ID Pedido: {pedido.id}\n" \
              f"Usuario: {request.user.username}\n" \
              f"Nombre: {request.user.first_name}\n" \
              f"Apellidos: {request.user.last_name}\n" \
              f"Teléfono: {request.user.teléfono}\n" \
              f"Dirección de Entrega: {request.user.provincia}, {request.user.municipio}, {request.user.zona}, {pedido.dirección_entrega}\n\n"
    
    # Agregar detalles de los productos cancelados
    mensaje += "*Productos Cancelados*:\n"
    for item in pedido.items.all():
        mensaje += f"- {item.producto.nombre}: " \
                   f"{item.cantidad} x ${item.precio_unitario:.2f} " \
                   f"= ${item.cantidad * item.precio_unitario:.2f}\n"
    
    mensaje += f"\n*Resumen*:\n" \
               f"Subtotal: ${subtotal:.2f}\n" \
               f"Costo de Envío: ${pedido.costo_envio:.2f}\n" \
               f"*Total Cancelado*: ${pedido.total:.2f}"
    
    enviar_mensaje_telegram(mensaje)
    return redirect('historial_pedidos')


@login_required
def historial_pedidos(request):
    pedidos_list = (
        Pedido.objects
        .filter(usuario=request.user)
        .select_related('usuario')
        .prefetch_related('items__producto')
        .order_by('-fecha', '-fecha__time')
    )
    page = request.GET.get('page', 1)
    paginator = Paginator(pedidos_list, 20)
    try:
        pedidos = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        pedidos = paginator.page(1)
    total = pedidos_list.count()
    return render(request, 'logica/historial_pedidos.html', {
        'pedidos': pedidos,
        'total': total
    })


@staff_member_required
def admin_historial_pedidos(request):
    pedidos_list = (
        Pedido.objects
        .filter(usuario__municipio=request.user.municipio)
        .select_related('usuario', 'usuario__municipio')
        .prefetch_related('items__producto')
        .order_by('-fecha', '-fecha__time')
    )
    page = request.GET.get('page', 1)
    paginator = Paginator(pedidos_list, 20)  # 20 pedidos por página
    try:
        pedidos = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        pedidos = paginator.page(1)
    total = pedidos_list.count()
    return render(request, 'logica/admin_historial_pedidos.html', {
        'pedidos': pedidos,
        'total': total
    })


@staff_member_required
def admin_detalle_pedido(request, pedido_id):
    pedido = get_object_or_404(
        Pedido.objects
        .select_related('usuario', 'usuario__municipio')
        .prefetch_related('items__producto'),
        id=pedido_id
    )
    subtotal = sum(item.cantidad * item.precio_unitario for item in pedido.items.all())
    return render(request, 'logica/admin_detalle_pedido.html', {
        'pedido': pedido,
        'subtotal': subtotal
    })


@staff_member_required
def admin_cambiar_estado_pedido(request, pedido_id):
    if request.method != 'POST':
        return redirect('admin_historial_pedidos')
    ESTADOS_VALIDOS = ['pendiente', 'preparando', 'en_camino', 'entregado', 'cancelado']
    pedido = get_object_or_404(
        Pedido.objects.select_related('usuario'), 
        id=pedido_id
    )
    nuevo_estado = request.POST.get('estado', '')
    if nuevo_estado in ESTADOS_VALIDOS:
        with transaction.atomic():
            pedido.estado = nuevo_estado
            pedido.save(update_fields=['estado'])
    return redirect('admin_detalle_pedido', pedido_id=pedido.id)