from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('resume/', views.resume, name='resume'),
    path('portfolio/', views.portfolio, name='portfolio'),
    path('blog/', views.blog, name='blog'),
    path('contact/', views.contact, name='contact'),
    
    # --- AUTHENTICATION ---
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('admin-logout/', views.admin_logout_view, name='admin_logout'),
    
    # --- DASHBOARD & ANALYTICS ---
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-analytics/', views.admin_analytics, name='admin_analytics'),

    # Change these paths to use dashboard/ prefixes instead of admin/
    path('admin-resume/', views.admin_resume, name='admin_resume'),
    path('dashboard/resume/<str:item_type>/edit/<int:pk>/', views.edit_resume_item, name='edit_resume_item'),
    path('dashboard/resume/<str:item_type>/delete/<int:pk>/', views.delete_resume_item, name='delete_resume_item'),
    
    # --- BLOG POST MANAGEMENT ---
    # Using 'dashboard/post/' avoids collision with the built-in '/admin/' path
    path('dashboard/post/new/', views.admin_save_post, name='admin_create_post'),
    path('dashboard/post/edit/<int:post_id>/', views.admin_save_post, name='admin_edit_post'),
    path('dashboard/post/delete/<int:post_id>/', views.admin_delete_post, name='admin_delete_post'),
    
    # --- CONTACT MANAGEMENT ---
    path('admin-contacts/', views.admin_contacts, name='admin_contacts'),
    path('admin-contact/<int:contact_id>/', views.admin_contact_detail, name='admin_contact_detail'),
    
    # --- PROJECT MANAGEMENT ---
    path('dashboard/project/', views.admin_project, name='admin_project'),
    path('dashboard/project/add/', views.admin_save_project, name='admin_add_project'),
    path('dashboard/project/edit/<int:project_id>/', views.admin_save_project, name='admin_edit_project'),
    path('dashboard/project/delete/<int:project_id>/', views.admin_delete_project, name='admin_delete_project'),
]