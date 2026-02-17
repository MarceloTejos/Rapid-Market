"""
URL configuration for proyecto project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from proyectoAPP import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('login/', views.login_usuario, name='login'),
    path('registro/', views.registro_usuario, name='registro'),
    path('logout/', views.logout, name='logout'),
    path('gproductos/', views.gproductos, name='gproductos'),
    path('realizar_venta/', views.realizar_venta, name='realizar_venta'),
    path("ventas/", views.venta, name="ventas"),

    # URL corregida
    path("boleta_pdf/<int:venta_id>/", views.generar_boleta_pdf, name="generar_boleta_pdf"),

    path('alertas/', views.alertas_reportes, name='alertas_reportes'),
    path('api/alertas/', views.alertas_api, name='alertas_api'),
    path('api/reportes/', views.reportes_api, name='reportes_api'),
    path('api/alerta/marcar/<int:alerta_id>/', views.marcar_leida, name='marcar_alerta'),
]
