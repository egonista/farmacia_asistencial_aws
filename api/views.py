"""
Vistas API REST del Sistema CESFAM Farmacia (CRUD completo + JWT).
"""
from rest_framework import viewsets, serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, BasePermission, AllowAny
from rest_framework.response import Response

from core.models import Paciente
from farmacia.models import Medicamento, Lote, CategoriaMedicamento
from dispensacion.models import Receta, Dispensacion


class EsPersonalFarmaciaOAdmin(BasePermission):
    """
    Bloquea con HTTP 403 Forbidden al Personal Clínico en endpoints de
    pacientes, recetas, dispensaciones y lotes internos de bodega.
    """
    message = 'El Personal Clínico solo tiene acceso de consulta al catálogo de medicamentos.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.rol in ('admin', 'quimico', 'tecnico')
        )


class CategoriaMedicamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaMedicamento
        fields = '__all__'


class MedicamentoSerializer(serializers.ModelSerializer):
    stock_total = serializers.ReadOnlyField()
    en_quiebre = serializers.ReadOnlyField()
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)

    class Meta:
        model = Medicamento
        fields = '__all__'

    def validate(self, attrs):
        stock_min = attrs.get('stock_minimo', getattr(self.instance, 'stock_minimo', 0))
        stock_max = attrs.get('stock_maximo', getattr(self.instance, 'stock_maximo', 0))
        if stock_min > stock_max:
            raise serializers.ValidationError({
                'stock_minimo': 'El stock mínimo no puede ser mayor que el stock máximo.'
            })
        return attrs


class LoteSerializer(serializers.ModelSerializer):
    dias_para_vencer = serializers.ReadOnlyField()
    alerta_vencimiento = serializers.ReadOnlyField()

    class Meta:
        model = Lote
        fields = '__all__'

    def validate_cantidad_actual(self, value):
        if value < 0:
            raise serializers.ValidationError('La cantidad actual no puede ser negativa.')
        return value


class PacienteSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.ReadOnlyField()

    class Meta:
        model = Paciente
        fields = '__all__'


class RecetaSerializer(serializers.ModelSerializer):
    esta_vigente = serializers.ReadOnlyField()

    class Meta:
        model = Receta
        fields = '__all__'

    def validate(self, attrs):
        emision = attrs.get('fecha_emision', getattr(self.instance, 'fecha_emision', None))
        vencimiento = attrs.get('fecha_vencimiento', getattr(self.instance, 'fecha_vencimiento', None))
        if emision and vencimiento and vencimiento < emision:
            raise serializers.ValidationError({
                'fecha_vencimiento': 'La fecha de vencimiento no puede ser anterior a la emisión.'
            })
        return attrs


class DispensacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dispensacion
        fields = '__all__'


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Endpoint público de salud para monitoreo y pruebas de API Gateway."""
    return Response({'status': 'ok', 'service': 'cesfam-farmacia-api'}, status=status.HTTP_200_OK)


class CategoriaMedicamentoViewSet(viewsets.ModelViewSet):
    queryset = CategoriaMedicamento.objects.all()
    serializer_class = CategoriaMedicamentoSerializer
    permission_classes = [IsAuthenticated]


class MedicamentoViewSet(viewsets.ModelViewSet):
    queryset = Medicamento.objects.filter(activo=True).select_related('categoria')
    serializer_class = MedicamentoSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['categoria', 'es_controlado', 'activo']
    search_fields = ['codigo', 'nombre_generico', 'nombre_comercial']


class LoteViewSet(viewsets.ModelViewSet):
    queryset = Lote.objects.filter(activo=True).order_by('fecha_vencimiento')
    serializer_class = LoteSerializer
    permission_classes = [IsAuthenticated, EsPersonalFarmaciaOAdmin]
    filterset_fields = ['medicamento', 'ubicacion', 'activo']


class PacienteViewSet(viewsets.ModelViewSet):
    queryset = Paciente.objects.filter(activo=True)
    serializer_class = PacienteSerializer
    permission_classes = [IsAuthenticated, EsPersonalFarmaciaOAdmin]
    search_fields = ['rut', 'nombres', 'apellido_paterno']


class RecetaViewSet(viewsets.ModelViewSet):
    queryset = Receta.objects.all()
    serializer_class = RecetaSerializer
    permission_classes = [IsAuthenticated, EsPersonalFarmaciaOAdmin]
    filterset_fields = ['estado', 'tipo', 'paciente']


class DispensacionViewSet(viewsets.ModelViewSet):
    queryset = Dispensacion.objects.all()
    serializer_class = DispensacionSerializer
    permission_classes = [IsAuthenticated, EsPersonalFarmaciaOAdmin]
