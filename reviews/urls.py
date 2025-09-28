from django.urls import path
from . import views

urlpatterns = [
    path('institutions/', views.InstitutionList.as_view(), name='institution-list'),
    path('institutions/<int:pk>/', views.InstitutionDetail.as_view(), name='institution-detail'),
    path('events/', views.EventList.as_view(), name='event-list'),
    path('events/<int:pk>/', views.EventDetail.as_view(), name='event-detail'),
    path('reviews/', views.ReviewList.as_view(), name='review-list'),
    path('reviews/<int:pk>/', views.ReviewDetail.as_view(), name='review-detail'),
    path('reviews/search/', views.ReviewSearch.as_view(), name='review-search'),
]
