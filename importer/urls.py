from django.urls import path
from . import views

urlpatterns = [
    path('import-gis-reviews/', views.GISReviews.as_view(), name='import_gis_reviews'),
    path('import-yandex-reviews/', views.YandexReviews.as_view(), name='import_yandex_reviews'),
    path('import-tg-reviews/', views.TelegramReviews.as_view(), name='import_tg_reviews'),
    path('import-vk-reviews/', views.VKReviews.as_view(), name='import-vk-reviews'),
    path('import-otzovik-reviews/', views.OtzovikReviews.as_view(), name='import-otzovik-reviews'),
    path('import-ok-reviews/', views.OKReviews.as_view(), name='import-ok-reviews'),
]
