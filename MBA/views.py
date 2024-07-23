import io
from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from asgiref.sync import async_to_sync
from django.http import HttpResponse
from rest_framework import status
from django.utils.timezone import make_naive
from django.core.mail import EmailMessage
import pandas as pd
import xlsxwriter
import datetime
from .models import MayBienAp, DuLieuMayBienAp, CanhBao, ThietLapCanhBao, DuLieuLuuTru, ThietBi
from .serializers import MayBienApSerializer, DuLieuMayBienApSerializer, CanhBaoSerializer, ThietLapCanhBaoSerializer, DuLieuLuuTruSerializer, ThietBiSerializer
from django.utils import timezone
import os
import logging
from io import BytesIO

class MayBienApViewSet(viewsets.ModelViewSet):
    queryset = MayBienAp.objects.all()
    serializer_class = MayBienApSerializer
    parser_classes = (MultiPartParser, FormParser)

    @action(detail=True, methods=['post'])
    def upload_image(self, request, pk=None):
        may_bien_ap = self.get_object()
        may_bien_ap.hinh_anh = request.FILES.get('hinh_anh')
        may_bien_ap.save()
        return Response({'status': 'hình ảnh đã được cập nhật'})

class DuLieuMayBienApViewSet(viewsets.ModelViewSet):
    queryset = DuLieuMayBienAp.objects.all()
    serializer_class = DuLieuMayBienApSerializer

class CanhBaoViewSet(viewsets.ModelViewSet):
    queryset = CanhBao.objects.all()
    serializer_class = CanhBaoSerializer

class ThietLapCanhBaoViewSet(viewsets.ModelViewSet):
    queryset = ThietLapCanhBao.objects.all()
    serializer_class = ThietLapCanhBaoSerializer
    @action(detail=False, methods=['get'])
    def by_mba(self, request):
        may_bien_ap_id = request.query_params.get('may_bien_ap', None)
        if may_bien_ap_id is not None:
            devices = ThietBi.objects.filter(may_bien_ap_id=may_bien_ap_id)
            serializer = ThietBiSerializer(devices, many=True)
            return Response(serializer.data)
        else:
            return Response({"detail": "may_bien_ap parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

class DuLieuLuuTruViewSet(viewsets.ModelViewSet):
    queryset = DuLieuLuuTru.objects.all()
    serializer_class = DuLieuLuuTruSerializer

class ThietBiViewSet(viewsets.ModelViewSet):
    queryset = ThietBi.objects.all()
    serializer_class = ThietBiSerializer

    def get_queryset(self):
        queryset = ThietBi.objects.all()
        may_bien_ap = self.request.query_params.get('may_bien_ap', None)
        if may_bien_ap is not None:
            queryset = queryset.filter(may_bien_ap=may_bien_ap)
        return queryset

    @action(detail=True, methods=['post'])
    def dieu_khien(self, request, pk=None):
        thiet_bi = self.get_object()
        thiet_bi.trang_thai = not thiet_bi.trang_thai
        thiet_bi.save()
        return Response({'status': 'thiết bị đã được điều khiển', 'trang_thai': thiet_bi.trang_thai})

@api_view(['POST'])
def update_data(request):
    data = request.data
    serializer = DuLieuMayBienApSerializer(data=data)
    if serializer.is_valid():
        new_data = serializer.save()

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'data_group', {
                'type': 'data_update',
                'message': {
                    'dien_ap_pha_a': new_data.dien_ap_pha_a,
                    'dien_ap_pha_b': new_data.dien_ap_pha_b,
                    'dien_ap_pha_c': new_data.dien_ap_pha_c,
                    'dong_pha_a': new_data.dong_pha_a,
                    'dong_pha_b': new_data.dong_pha_b,
                    'dong_pha_c': new_data.dong_pha_c,
                    'cong_suat_tac_dung_a': new_data.cong_suat_tac_dung_a,
                    'cong_suat_tac_dung_b': new_data.cong_suat_tac_dung_b,
                    'cong_suat_tac_dung_c': new_data.cong_suat_tac_dung_c,
                    'may_bien_ap': new_data.may_bien_ap.id,
                }
            }
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Thiết lập logger
logger = logging.getLogger(__name__)

def safe_unicode(value):
    try:
        return str(value)
    except UnicodeDecodeError:
        return value.decode('utf-8')

def schedule_report(email, start_date, end_date, selected_mba, selected_data_options):
    file_path = 'report.xlsx'

    with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
        for mba_id in selected_mba:
            mba = MayBienAp.objects.get(id=mba_id)
            data_options = [field for field in selected_data_options if field != 'canh_bao' and field != 'thiet_bi_dieu_khien']
            data = DuLieuMayBienAp.objects.filter(
                may_bien_ap=mba,
                thoi_gian__range=(start_date, end_date)
            ).values(*data_options)

            df = pd.DataFrame(list(data))
            if 'thoi_gian' in df.columns:
                df['thoi_gian'] = df['thoi_gian'].apply(lambda x: x.replace(tzinfo=None))
            df.to_excel(writer, sheet_name=mba.ten, index=False)

            if 'canh_bao' in selected_data_options:
                canh_bao_data = CanhBao.objects.filter(
                    du_lieu__may_bien_ap=mba,
                    thoi_gian__range=(start_date, end_date)
                ).values('noi_dung', 'thoi_gian')
                canh_bao_df = pd.DataFrame(list(canh_bao_data))
                if 'thoi_gian' in canh_bao_df.columns:
                    canh_bao_df['thoi_gian'] = canh_bao_df['thoi_gian'].apply(lambda x: x.replace(tzinfo=None))
                canh_bao_df.to_excel(writer, sheet_name=f"{mba.ten}_CanhBao", index=False)

            if 'thiet_bi_dieu_khien' in selected_data_options:
                thiet_bi_data = ThietBi.objects.filter(may_bien_ap=mba).values('ten', 'trang_thai')
                thiet_bi_df = pd.DataFrame(list(thiet_bi_data))
                thiet_bi_df.to_excel(writer, sheet_name=f"{mba.ten}_ThietBi", index=False)

    email_message = EmailMessage(
        'Báo cáo tự động',
        'Báo cáo tự động theo yêu cầu của bạn.',
        'from@example.com',
        [email]
    )
    email_message.attach_file(file_path)
    try:
        email_message.send()
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise

@api_view(['POST'])
def export_data(request):
    mode = request.data.get('mode')
    start_date = request.data.get('startDate')
    end_date = request.data.get('endDate')
    selected_mba = request.data.get('selectedMBA')
    selected_data_options = request.data.get('selectedDataOptions')

    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S.%fZ')
    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S.%fZ')

    if mode == "Tự động":
        email = request.data.get('email')
        schedule_report(email, start_date, end_date, selected_mba, selected_data_options)
        return Response({'status': 'Report scheduled to be sent via email'}, status=status.HTTP_200_OK)
    else:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for mba_id in selected_mba:
                mba = MayBienAp.objects.get(id=mba_id)
                data_options = [field for field in selected_data_options if field != 'canh_bao' and field != 'thiet_bi_dieu_khien']
                data = DuLieuMayBienAp.objects.filter(
                    may_bien_ap=mba,
                    thoi_gian__range=(start_date, end_date)
                ).values(*data_options)

                df = pd.DataFrame(list(data))
                if 'thoi_gian' in df.columns:
                    df['thoi_gian'] = df['thoi_gian'].apply(lambda x: x.replace(tzinfo=None))
                df.to_excel(writer, sheet_name=mba.ten, index=False)

                if 'canh_bao' in selected_data_options:
                    canh_bao_data = CanhBao.objects.filter(
                        du_lieu__may_bien_ap=mba,
                        thoi_gian__range=(start_date, end_date)
                    ).values('noi_dung', 'thoi_gian')
                    canh_bao_df = pd.DataFrame(list(canh_bao_data))
                    if 'thoi_gian' in canh_bao_df.columns:
                        canh_bao_df['thoi_gian'] = canh_bao_df['thoi_gian'].apply(lambda x: x.replace(tzinfo=None))
                    canh_bao_df.to_excel(writer, sheet_name=f"{mba.ten}_CanhBao", index=False)

                if 'thiet_bi_dieu_khien' in selected_data_options:
                    thiet_bi_data = ThietBi.objects.filter(may_bien_ap=mba).values('ten', 'trang_thai')
                    thiet_bi_df = pd.DataFrame(list(thiet_bi_data))
                    thiet_bi_df.to_excel(writer, sheet_name=f"{mba.ten}_ThietBi", index=False)

        output.seek(0)
        response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=report.xlsx'
        return response


class DuLieuMayBienApViewSet(viewsets.ModelViewSet):
    queryset = DuLieuMayBienAp.objects.all()
    serializer_class = DuLieuMayBienApSerializer

    @action(detail=False, methods=['get'], url_path='may-bien-ap/(?P<mba_id>[^/.]+)')
    def get_by_mba(self, request, mba_id=None):
        try:
            data = DuLieuMayBienAp.objects.filter(may_bien_ap=mba_id)
            serializer = DuLieuMayBienApSerializer(data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except DuLieuMayBienAp.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class ThietLapCanhBaoByMBAView(APIView):

    def get(self, request, mba_id):
        try:
            thiet_lap = ThietLapCanhBao.objects.get(may_bien_ap=mba_id)
            serializer = ThietLapCanhBaoSerializer(thiet_lap)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ThietLapCanhBao.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def post(self, request, mba_id):
        try:
            thiet_lap = ThietLapCanhBao.objects.get(may_bien_ap=mba_id)
        except ThietLapCanhBao.DoesNotExist:
            thiet_lap = ThietLapCanhBao(may_bien_ap_id=mba_id)

        serializer = ThietLapCanhBaoSerializer(thiet_lap, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


