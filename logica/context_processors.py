from .models import Carrito

def carrito_context(request):
    if request.user.is_authenticated:
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        return {
            'carrito_cantidad': carrito.items.count()
        }
    return {}