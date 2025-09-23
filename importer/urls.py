from django.urls import path
from . import views

urlpatterns = [
    path('import-gis-reviews/', views.GISReviews.as_view(), name='import_gis_reviews'),
]
