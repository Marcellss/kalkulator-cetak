from django.urls import path

from . import views

app_name = "kalkulator"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("hitung/", views.hitung_view, name="hitung"),
    path("hitung/<int:pk>/", views.detail, name="detail"),
    path("hitung/<int:pk>/ubah/", views.ubah, name="ubah"),
    path("hitung/<int:pk>/hapus/", views.hapus, name="hapus"),
    path("hitung/<int:pk>/cetak/", views.cetak, name="cetak"),
    path("hitung/<int:pk>/cetak-cust/", views.cetak_cust, name="cetak_cust"),
    path("hitung/<int:pk>/duplikat/", views.duplikat, name="duplikat"),
    path("ongkos-cetak/", views.ongkos_list, name="ongkos_list"),
    path("ongkos-cetak/baru/", views.ongkos_baru, name="ongkos_baru"),
    path("ongkos-cetak/<int:pk>/ubah/", views.ongkos_ubah, name="ongkos_ubah"),
    path("ongkos-cetak/<int:pk>/hapus/", views.ongkos_hapus, name="ongkos_hapus"),
    path("ongkos-cetak/<int:pk>/cetak/", views.ongkos_cetak, name="ongkos_cetak"),
    path("ongkos-cetak/<int:pk>/cetak-cust/", views.ongkos_cetak_cust, name="ongkos_cetak_cust"),
    path("api/ongkos-cetak/", views.api_ongkos, name="api_ongkos"),
    path("preset/", views.preset_list, name="preset_list"),
    path("preset/simpan/", views.preset_baru, name="preset_baru"),
    path("preset/<int:pk>/ubah/", views.preset_form, name="preset_form"),
    path("preset/<int:pk>/simpan/", views.preset_ubah, name="preset_ubah"),
    path("preset/<int:pk>/hapus/", views.preset_hapus, name="preset_hapus"),
    path("kertas/", views.kertas_list, name="kertas_list"),
    path("kertas/baru/", views.kertas_form, name="kertas_baru"),
    path("kertas/<int:pk>/ubah/", views.kertas_form, name="kertas_ubah"),
    path("kertas/<int:pk>/hapus/", views.kertas_hapus, name="kertas_hapus"),
    path("api/hitung/", views.api_hitung, name="api_hitung"),
]
