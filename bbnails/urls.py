from django.urls import path
from . import views

urlpatterns = [
    # Public Client Routes
    path('', views.home, name='home'),
    path('book/', views.book_appointment, name='book_appointment'),
    path('api/available-slots/', views.get_available_slots, name='get_available_slots'),

    # Staff Admin Portal
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Service Management Actions
    path('admin-dashboard/services/add/', views.add_service, name='add_service'),
    path('admin-dashboard/services/toggle/<int:pk>/', views.toggle_service, name='toggle_service'),
    path('admin-dashboard/services/delete/<int:pk>/', views.delete_service, name='delete_service'),

    # Time Slot Management Actions
    path('admin-dashboard/slots/add/', views.add_slot, name='add_slot'),
    path('admin-dashboard/slots/toggle/<int:pk>/', views.toggle_slot, name='toggle_slot'),
    path('admin-dashboard/slots/delete/<int:pk>/', views.delete_slot, name='delete_slot'),

    # Appointment Status Actions
    path('admin-dashboard/status/<int:pk>/<str:status>/', views.update_status, name='update_status'),
]