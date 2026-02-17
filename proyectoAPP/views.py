from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.template.loader import render_to_string
from .models import Usuario, Producto
from functools import wraps
from django.http import HttpResponse, JsonResponse
from datetime import datetime, date
from xhtml2pdf import pisa
from .models import Producto, Venta, DetalleVenta, Usuario, Alerta
from django.db.models import Sum, F
from .utils.forecast import monthly_sales_by_product, expected_sales_same_month_last_year


def inicio(request):
    return render(request, 'inicio.html', {
        'usuario_nombre': request.session.get('usuario_nombre')
    })

# Login
def login_usuario(request):
    if request.method == 'POST':
        usuario_input = request.POST.get('usuario')
        password_input = request.POST.get('password')

        try:
            usuario = Usuario.objects.get(usuario=usuario_input)
        except Usuario.DoesNotExist:
            messages.error(request, 'Usuario no encontrado.')
            return redirect('login')

        # Verificar contraseña
        if usuario.check_password(password_input):
            request.session['usuario_id'] = usuario.id
            request.session['usuario_nombre'] = usuario.nombre
            request.session['usuario_rol'] = usuario.rol

            messages.success(request, f'Bienvenido {usuario.nombre} 👋')
            return redirect('inicio')
        else:
            messages.error(request, 'Contraseña incorrecta.')
            return redirect('login')
    return render(request, 'login.html')

# Logout
def logout(request):

    request.session.flush()
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('inicio')

def login_requerido(func):
    def wrapper(request, *args, **kwargs):
        if 'usuario_id' not in request.session:
            messages.error(request, 'Debes iniciar sesión primero.')
            return redirect('login')
        return func(request, *args, **kwargs)
    return wrapper

def rol_requerido(*roles_permitidos):
    @wraps(roles_permitidos)
    def decorador(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            rol = request.session.get('usuario_rol')

            if not rol:
                messages.error(request, "Debes iniciar sesión.")
                return redirect('login')

            if rol not in roles_permitidos:
                messages.error(request, "No tienes permisos para acceder a esta sección.")
                return redirect('inicio')

            return func(request, *args, **kwargs)
        return wrapper
    return decorador

@login_requerido
@rol_requerido('admin')
def registro_usuario(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        usuario = request.POST.get('usuario')
        password = request.POST.get('password')
        rol = request.POST.get('rol')

        # Validar que el usuario no exista
        if Usuario.objects.filter(usuario=usuario).exists():
            messages.error(request, 'El nombre de usuario ya existe.')
            return redirect('registro')

        # Crear usuario y encriptar contraseña
        nuevo_usuario = Usuario(
            nombre=nombre,
            apellido=apellido,
            usuario=usuario,
            rol=rol
        )
        nuevo_usuario.set_password(password)
        nuevo_usuario.save()

        messages.success(request, f'Usuario "{usuario}" registrado correctamente.')
        return redirect('registro')

    return render(request, 'registro.html')

@login_requerido
@rol_requerido('admin')
def gproductos(request):
    # AGREGAR PRODUCTO
    if request.method == 'POST' and request.POST.get('action') == 'add':
        nombre = request.POST.get('nombre')
        categoria = request.POST.get('categoria')
        precio = request.POST.get('precio')
        stock = request.POST.get('stock')

        if not nombre or not categoria or not precio or not stock:
            messages.error(request, 'Todos los campos son obligatorios.')
        else:
            Producto.objects.create(
                nombre=nombre,
                categoria=categoria,
                precio=precio,
                stock=stock
            )
            messages.success(request, f'Producto "{nombre}" agregado correctamente.')
        return redirect('gproductos')

    # EDITAR PRODUCTO
    if request.method == 'POST' and request.POST.get('action') == 'edit':
        producto_id = request.POST.get('producto_id')
        producto = get_object_or_404(Producto, id=producto_id)
        producto.nombre = request.POST.get('nombre')
        producto.categoria = request.POST.get('categoria')
        producto.precio = request.POST.get('precio')
        producto.stock = request.POST.get('stock')
        producto.save()
        messages.success(request, f'Producto "{producto.nombre}" editado correctamente.')
        return redirect('gproductos')

    # ELIMINAR PRODUCTO
    if request.method == 'POST' and request.POST.get('action') == 'delete':
        producto_id = request.POST.get('producto_id')
        producto = get_object_or_404(Producto, id=producto_id)
        producto.delete()
        messages.success(request, f'Producto "{producto.nombre}" eliminado correctamente.')
        return redirect('gproductos')

    # Mostrar productos
    productos = Producto.objects.all()
    return render(request, 'gproductos.html', {'productos': productos})

@login_requerido
def realizar_venta(request):
    # Recupera y elimina el ID de la venta de la sesión.
    venta_pdf_id = request.session.pop("venta_pdf_id", None) 
    
    # Limpia el indicador de formulario 
    venta_limpia = request.session.pop("venta_limpia", False)

    productos = Producto.objects.all()

    return render(request, "realizar_venta.html", {
        "productos": productos,
        "usuario_nombre": request.session.get("usuario_nombre"),
        "venta_limpia": venta_limpia,
        #Pasa el ID al template para que JavaScript pueda usarlo
        "venta_pdf_id": venta_pdf_id, 
    })


def generar_boleta_pdf(request, venta_id):

    try:
        venta = Venta.objects.get(id=venta_id)
    except Venta.DoesNotExist:
        return HttpResponse("Venta no encontrada", status=404)
        
    detalle = DetalleVenta.objects.filter(venta=venta)

    data = {
        "fecha": venta.fecha,
        "usuario": venta.usuario.nombre,
        "detalle": detalle,
        "total": venta.total,
    }

    html = render_to_string("boleta_pdf.html", data)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="boleta_{venta_id}.pdf"' 

    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse("Error al generar PDF")

    return response

def venta(request):
    if request.method != "POST":
        return redirect("realizar_venta")

    productos_ids = request.POST.getlist("producto_id[]")
    cantidades = request.POST.getlist("cantidad[]")
    precios = request.POST.getlist("precio_unitario[]")
    total = request.POST.get("total")

    usuario = Usuario.objects.get(id=request.session.get('usuario_id'))

    try:
        total = float(total)
    except (TypeError, ValueError):
        messages.error(request, "El total de la venta no es válido.")
        return redirect("realizar_venta")

    # Crear la venta inicialmente
    venta = Venta.objects.create(usuario=usuario, total=total)
    venta_exitosa = True

    for i in range(len(productos_ids)):
        producto = Producto.objects.get(id=productos_ids[i])
        cantidad = int(cantidades[i])
        precio = float(precios[i])
        subtotal = cantidad * precio

        #Validación de stock
        if producto.stock < cantidad:
            messages.error(request, f"No hay suficiente stock de {producto.nombre}. Disponible: {producto.stock} uds.")
            venta.delete() #Eliminar la venta incompleta
            venta_exitosa = False
            return redirect("realizar_venta")

        #Crear detalle y descontar stock
        DetalleVenta.objects.create(
            venta=venta,
            producto=producto,
            cantidad=cantidad,
            precio_unitario=precio,
            subtotal=subtotal
        )

        producto.stock -= cantidad
        producto.save()

    if venta_exitosa:
        request.session["venta_pdf_id"] = venta.id
        request.session["venta_limpia"] = True 
        messages.success(request, "Venta realizada con éxito.")

    return redirect("realizar_venta")

def alertas_reportes(request):
    
    return render(request, 'alertas_reportes.html', {
        'usuario_nombre': request.session.get('usuario_nombre')
    })


def alertas_api(request):
    UMBRAL_BAJO_STOCK = 5

    
    guardadas = Alerta.objects.order_by('-fecha_generacion')[:50]
    guardadas_list = [
        {
            'id': a.id,
            'producto': a.producto.nombre,
            'tipo': a.tipo,
            'mensaje': a.mensaje,
            'fecha': a.fecha_generacion.strftime("%Y-%m-%d %H:%M"),
            'leida': a.leida
        } for a in guardadas
    ]

    bajo_stock = []
    productos = Producto.objects.all().values('id','nombre','stock')
    for p in productos:
        if p['stock'] <= UMBRAL_BAJO_STOCK:
            bajo_stock.append({
                'producto_id': p['id'],
                'producto': p['nombre'],
                'tipo': 'BAJO_STOCK',
                'mensaje': f'Stock bajo ({p["stock"]} unidades). Revisar reposición.'
            })

    # Calcular ventas históricas y predecir mes próximo
    detalles = DetalleVenta.objects.select_related('venta','producto').all()
    product_month_map = monthly_sales_by_product(detalles)


    today = date.today()
    if today.month == 12:
        target_year = today.year + 1
        target_month = 1
    else:
        target_year = today.year
        target_month = today.month + 1

    recomendaciones = []
    for p in Producto.objects.all():
        esperado = expected_sales_same_month_last_year(product_month_map, p.id, target_year, target_month)
        stock_val = (p.stock or 0) * float(p.precio)
        if esperado > max( (stock_val * 0.6), 0 ):  
            recomendaciones.append({
                'producto_id': p.id,
                'producto': p.nombre,
                'esperado_monto': round(esperado,2),
                'stock_actual': p.stock,
                'mensaje': f'Se espera vender ${esperado:.0f} en el mes próximo. Recomendar reposición.'
            })

    return JsonResponse({
        'guardadas': guardadas_list,
        'dinamicas_bajo_stock': bajo_stock,
        'recomendaciones_ia': recomendaciones
    }, safe=False)


def reportes_api(request):
    from django.db.models.functions import TruncMonth
    qs = DetalleVenta.objects.annotate(month=TruncMonth('venta__fecha')).values('month').annotate(total=Sum('subtotal')).order_by('month')
    data = []
    for r in qs:
        data.append({
            'month': r['month'].strftime("%Y-%m"),
            'total': float(r['total'] or 0)
        })
    return JsonResponse({'series': data})


def marcar_leida(request, alerta_id):
    if request.method == 'POST':
        a = Alerta.objects.filter(id=alerta_id).first()
        if a:
            a.leida = True
            a.save()
            return JsonResponse({'ok': True})
    return JsonResponse({'ok': False}, status=400)
