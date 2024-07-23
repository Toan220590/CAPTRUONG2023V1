from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

class MayBienAp(models.Model):
    ten = models.CharField(max_length=100)
    vi_tri = models.CharField(max_length=100)
    kinh_do = models.FloatField()
    vi_do = models.FloatField()
    cong_suat = models.FloatField()  # Công suất máy biến áp
    uc = models.FloatField()  # Điện áp danh định cuộn dây thứ cấp
    uh = models.FloatField()  # Điện áp danh định cuộn dây sơ cấp
    ton_hao_khong_tai = models.FloatField()  # Tổn hao không tải
    ton_hao_ngan_mach = models.FloatField()  # Tổn hao ngắn mạch
    un_phan_tram = models.FloatField()  # Điện áp ngắn mạch (%)
    i0_phan_tram = models.FloatField()  # Dòng không tải (%)
    hinh_anh = models.ImageField(upload_to='images/', null=True, blank=True)  # Thêm trường hình ảnh
    su_co = models.BooleanField(default=False)  # Trường trạng thái sự cố

    def __str__(self):
        return self.ten

class ThietLapCanhBao(models.Model):
    may_bien_ap = models.OneToOneField(MayBienAp, on_delete=models.CASCADE)
    dong_canh_bao = models.FloatField(default=100)
    dien_ap_thap = models.FloatField(default=210)
    dien_ap_cao = models.FloatField(default=240)

    def __str__(self):
        return f"Thiết lập cảnh báo cho {self.may_bien_ap.ten}"

class DuLieuMayBienAp(models.Model):
    may_bien_ap = models.ForeignKey(MayBienAp, on_delete=models.CASCADE)
    thoi_gian = models.DateTimeField(auto_now_add=True)
    dien_ap_pha_a = models.FloatField()
    dien_ap_pha_b = models.FloatField()
    dien_ap_pha_c = models.FloatField()
    dong_pha_a = models.FloatField()
    dong_pha_b = models.FloatField()
    dong_pha_c = models.FloatField()
    cong_suat_tac_dung_a = models.FloatField()  # Công suất tác dụng pha A
    cong_suat_tac_dung_b = models.FloatField()  # Công suất tác dụng pha B
    cong_suat_tac_dung_c = models.FloatField()  # Công suất tác dụng pha C


    def __str__(self):
        return f"Dữ liệu của {self.may_bien_ap.ten} tại {self.thoi_gian}"

    def kiem_tra_canh_bao(self):
        thiet_lap = ThietLapCanhBao.objects.get(may_bien_ap=self.may_bien_ap)
        canh_bao = []
        su_co = False

        if self.dong_pha_a > thiet_lap.dong_canh_bao:
            canh_bao.append(f"Quá dòng pha A của {self.may_bien_ap.ten}")
            su_co = True
        if self.dong_pha_b > thiet_lap.dong_canh_bao:
            canh_bao.append(f"Quá dòng pha B của {self.may_bien_ap.ten}")
            su_co = True
        if self.dong_pha_c > thiet_lap.dong_canh_bao:
            canh_bao.append(f"Quá dòng pha C của {self.may_bien_ap.ten}")
            su_co = True
        if self.dien_ap_pha_a < thiet_lap.dien_ap_thap or self.dien_ap_pha_a > thiet_lap.dien_ap_cao:
            canh_bao.append(f"Thấp áp hoặc quá áp pha A của {self.may_bien_ap.ten}")
            su_co = True
        if self.dien_ap_pha_b < thiet_lap.dien_ap_thap or self.dien_ap_pha_b > thiet_lap.dien_ap_cao:
            canh_bao.append(f"Thấp áp hoặc quá áp pha B của {self.may_bien_ap.ten}")
            su_co = True
        if self.dien_ap_pha_c < thiet_lap.dien_ap_thap or self.dien_ap_pha_c > thiet_lap.dien_ap_cao:
            canh_bao.append(f"Thấp áp hoặc quá áp pha C của {self.may_bien_ap.ten}")
            su_co = True

        # Cập nhật trường su_co của MayBienAp
        self.may_bien_ap.su_co = su_co
        self.may_bien_ap.save()

        return canh_bao


class CanhBao(models.Model):
    du_lieu = models.ForeignKey(DuLieuMayBienAp, on_delete=models.CASCADE)
    noi_dung = models.CharField(max_length=255)
    thoi_gian = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cảnh báo: {self.noi_dung} tại {self.thoi_gian}"

class DuLieuLuuTru(models.Model):
    may_bien_ap = models.ForeignKey(MayBienAp, on_delete=models.CASCADE)
    thoi_gian = models.DateTimeField()
    dien_ap_pha_a = models.FloatField()
    dien_ap_pha_b = models.FloatField()
    dien_ap_pha_c = models.FloatField()
    dong_pha_a = models.FloatField()
    dong_pha_b = models.FloatField()
    dong_pha_c = models.FloatField()
    cong_suat_tac_dung_a = models.FloatField()
    cong_suat_tac_dung_b = models.FloatField()
    cong_suat_tac_dung_c = models.FloatField()

    def __str__(self):
        return f"Dữ liệu lưu trữ của {self.may_bien_ap.ten} tại {self.thoi_gian}"

class ThietBi(models.Model):
    may_bien_ap = models.ForeignKey(MayBienAp, on_delete=models.CASCADE)
    ten = models.CharField(max_length=100)
    trang_thai = models.BooleanField(default=False)

    def __str__(self):
        return f"Thiết bị {self.ten} của {self.may_bien_ap.ten}"

# Signal to delete old data
@receiver(post_save, sender=DuLieuMayBienAp)
def delete_old_data(sender, instance, **kwargs):
    one_month_ago = timezone.now() - timedelta(days=30)
    DuLieuMayBienAp.objects.filter(thoi_gian__lt=one_month_ago).delete()
