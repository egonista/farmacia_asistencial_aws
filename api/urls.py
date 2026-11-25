"""
URLs de la API REST del Sistema CESFAM Farmacia.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

app_name = 'api'

router = DefaultRouter()
router.register(r'categorias', views.CategoriaMedicamentoViewSet, basename='categoria')
router.register(r'medicamentos', views.MedicamentoViewSet, basename='medicamento')
router.register(r'lotes', views.LoteViewSet, basename='lote')
router.register(r'pacientes', views.PacienteViewSet, basename='paciente')
router.register(r'recetas', views.RecetaViewSet, basename='receta')
router.register(r'dispensaciones', views.DispensacionViewSet, basename='dispensacion')

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]
