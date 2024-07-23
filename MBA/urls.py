from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MayBienApViewSet, DuLieuMayBienApViewSet, CanhBaoViewSet, ThietLapCanhBaoViewSet, ThietBiViewSet, DuLieuLuuTruViewSet, update_data, export_data, schedule_report, DuLieuMayBienApViewSet, ThietLapCanhBaoByMBAView
from django.urls import re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

router = DefaultRouter()
router.register(r'may-bien-ap', MayBienApViewSet)
router.register(r'du-lieu', DuLieuMayBienApViewSet)
router.register(r'canh-bao', CanhBaoViewSet)
router.register(r'thiet-lap-canh-bao', ThietLapCanhBaoViewSet)
router.register(r'thiet-bi', ThietBiViewSet)
router.register(r'du-lieu-luu-tru', DuLieuLuuTruViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('export-data/', export_data, name='export_data'),  # Thêm đường dẫn cho API export-data
    path('schedule-report/', schedule_report, name='schedule_report'),  # Thêm đường dẫn cho API schedule-report
    path('api/thiet-lap-canh-bao/<int:mba_id>/', ThietLapCanhBaoByMBAView.as_view(), name='thiet_lap_canh_bao_by_mba'),
    path('thiet-bi/by-mba/', ThietBiViewSet.as_view({'get': 'by_mba'}), name='thietbi-by-mba'),
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
