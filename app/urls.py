from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('contact/', views.contact, name='contact'),
    path('injuries/', views.injuries, name='injuries'),
    path('shop/', views.shop, name='shop'),
    path('about/', views.about, name='about'),
    path('sign/', views.sign_up_selection_view, name='sign'),
    path('learner-signup/', views.learner_signup_view, name='lsignup'),
    path('mentor-signup/', views.mentor_signup_view, name='msign'),
    path('login/', views.login_view, name='login_view'),
    path('logout/', views.logout_view, name='logout'),
    path('learner-dashboard/', views.learner_dashboard_view, name='learner_dash'),
    path('mentor-dashboard/', views.mentor_dashboard_view, name='mentor_dash'),
    path('bookings/', views.booking_view, name='booking'),
    path('book-session/<int:mentor_id>/', views.book_session_view, name='book_session'),
    path('award-points/<int:session_id>/', views.award_points_view, name='award_points'),
    path('mentors/', views.mentor_profiles_view, name='mentor_profiles'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    
    # --- Fix: Changed name from 'progress_track' to 'progress_tracker' ---
    path('progress/', views.progress_tracker_view, name='progress_tracker'),
    
    path('diet-plans/', views.diet_plans_view, name='diet_plans'),
    path('application-submitted/', views.application_submitted_view, name='application_submitted'),
    path('safety-quiz/', views.safety_quiz_view, name='safety_quiz'),
    path('chat/<int:booking_id>/', views.chat_view, name='chat'),
]