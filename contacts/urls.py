from django.urls import path
from . import views
from . import api_views

app_name = 'contacts'

urlpatterns = [
    # Web Views
    path('', views.ContactListView.as_view(), name='list'),
    path('contact/<int:pk>/', views.ContactDetailView.as_view(), name='detail'),
    path('contact/add/', views.ContactCreateView.as_view(), name='create'),
    path('contact/<int:pk>/edit/', views.ContactUpdateView.as_view(), name='update'),
    path('contact/<int:pk>/delete/', views.ContactDeleteView.as_view(), name='delete'),
    path('import/', views.ContactImportView.as_view(), name='import'),

    # REST API Endpoints
    path('api/contacts/', api_views.ContactListCreateAPIView.as_view(), name='api-list'),
    path('api/contacts/<int:pk>/', api_views.ContactDetailAPIView.as_view(), name='api-detail'),
    path('api/weather/<str:city>/', api_views.WeatherAPIView.as_view(), name='api-weather'),
]
