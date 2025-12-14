from django.urls import path
from . import views

urlpatterns = [
    path('import-gis-reviews/', views.GISReviews.as_view(), name='import_gis_reviews'),
    path('import-yandex-reviews/', views.YandexReviews.as_view(), name='import_yandex_reviews'),
]
