from rest_framework import serializers
from .models import MayBienAp, DuLieuMayBienAp, CanhBao, ThietLapCanhBao, DuLieuLuuTru, ThietBi

class MayBienApSerializer(serializers.ModelSerializer):
    class Meta:
        model = MayBienAp
        fields = '__all__'

class DuLieuMayBienApSerializer(serializers.ModelSerializer):
    class Meta:
        model = DuLieuMayBienAp
        fields = '__all__'

    def create(self, validated_data):
        du_lieu = super().create(validated_data)
        canh_bao_noi_dung = du_lieu.kiem_tra_canh_bao()
        for noi_dung in canh_bao_noi_dung:
            CanhBao.objects.create(du_lieu=du_lieu, noi_dung=noi_dung)

        # Lưu dữ liệu vào DuLieuLuuTru khi phút chia hết cho 10
        if du_lieu.thoi_gian.minute % 10 == 0:
            DuLieuLuuTru.objects.create(
                may_bien_ap=du_lieu.may_bien_ap,
                thoi_gian=du_lieu.thoi_gian,
                dien_ap_pha_a=du_lieu.dien_ap_pha_a,
                dien_ap_pha_b=du_lieu.dien_ap_pha_b,
                dien_ap_pha_c=du_lieu.dien_ap_pha_c,
                dong_pha_a=du_lieu.dong_pha_a,
                dong_pha_b=du_lieu.dong_pha_b,
                dong_pha_c=du_lieu.dong_pha_c,
                cong_suat_tac_dung_a=du_lieu.cong_suat_tac_dung_a,
                cong_suat_tac_dung_b=du_lieu.cong_suat_tac_dung_b,
                cong_suat_tac_dung_c=du_lieu.cong_suat_tac_dung_c,
            )
        return du_lieu

class CanhBaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CanhBao
        fields = '__all__'

class ThietLapCanhBaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThietLapCanhBao
        fields = '__all__'

class DuLieuLuuTruSerializer(serializers.ModelSerializer):
    class Meta:
        model = DuLieuLuuTru
        fields = '__all__'

class ThietBiSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThietBi
        fields = '__all__'
