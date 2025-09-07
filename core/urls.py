from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path("about/", views.about, name="about"),
    path("blog/", views.blog, name="blog"),
    path("blog/<int:pk>/", views.blog_detail, name="blog_detail"),
    path("blog/<int:pk>/like/", views.blog_like, name="blog_like"),
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.logout_view, name="logout"),
    path("contact/", views.contact, name="contact"),
]
