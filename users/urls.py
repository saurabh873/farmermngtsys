from django.urls import path
from . import views

urlpatterns = [
   path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create-block/', views.create_block, name='create_block'),
    path('create-user/', views.create_or_edit_user, name='create_user'),
    #path('add-farmer/', views.add_farmer, name='add_farmer'),
    path('list-users/', views.list_users, name='list_users'),
    path('edit-user/<int:user_id>/', views.create_or_edit_user, name='edit_user'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('list-surveyors/', views.list_surveyors, name='list_surveyors'),
    path('delete-farmer/<int:farmer_id>/', views.delete_farmer, name='delete_farmer'),
    path('add-farmer/', views.add_or_edit_farmer, name='add_farmer'),
    path('edit-farmer/<int:farmer_id>/', views.add_or_edit_farmer, name='edit_farmer'),
     path('list-farmers/', views.list_farmers, name='list_farmers'),
    path('profile/',views.profile, name='profile'),




]
