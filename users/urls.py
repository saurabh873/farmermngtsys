from django.urls import path
from users import views
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import*


urlpatterns = [
   path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create-block/', views.create_block, name='create_block'),

    #path('add-farmer/', views.add_farmer, name='add_farmer'),
    path('list-users/', views.list_users, name='list_users'),

    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('list-surveyors/', views.list_surveyors, name='list_surveyors'),
    path('delete-farmer/<int:farmer_id>/', views.delete_farmer, name='delete_farmer'),
    
    path('list-farmers/', views.list_farmers, name='list_farmers'),
    path('profile/',views.profile, name='profile'),
     path('create-user/', views.create_user, name='create_user'),
    path('update-user/<int:user_id>/', views.update_user, name='update_user'),
    path('add-farmer/', views.add_farmer, name='add_farmer'),
    path('edit-farmer/<int:farmer_id>/', views.edit_farmer, name='edit_farmer'),
    path('get_real_time_counts/', views.get_real_time_counts, name='get_real_time_counts'),
   #  path('api/', include(router.urls)),  
    path('api/farmers/', FarmerView.as_view(), name='farmer-api'),



  




    #path('user/<int:user_id>/daily_farmer_count/', views.user_daily_farmer_count, name='user_daily_farmer_count'),
   # path('block/<int:block_id>/daily_farmer_count/', views.block_daily_farmer_count, name='block_daily_farmer_count'),
    





]
