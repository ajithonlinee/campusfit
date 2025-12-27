from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from .models import User, Learner, Mentor, Booking, DietPlan, Message
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Sum, F, ExpressionWrapper, fields
from django.db.models.functions import Cast
from django.db.models.expressions import RawSQL
from django.contrib import messages
from django.db import IntegrityError, connection
from .forms import LearnerSignUpForm, MentorSignUpForm
from .ai_diet_utils import generate_smart_diet_plan # <--- Imported new utility

# --- ML IMPORTS ---
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import linear_kernel
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

def home_view(request):
    return render(request, 'home.html')
def contact(request):
    return render(request, 'contact.html')
def injuries(request):
    return render(request, 'injuries.html')
def shop(request):
    return render(request, 'shop.html')
def about(request):
    return render(request, 'about.html')
def sign_up_selection_view(request):
    return render(request, 'sign.html')

def learner_signup_view(request):
    if request.method == 'POST':
        form = LearnerSignUpForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password'])
                user.role = 'learner'
                user.username = form.cleaned_data['email']
                user.save()
                Learner.objects.create(
                    user=user,
                    roll_number=request.POST.get('roll_number'),
                    goal=request.POST.get('goal')
                )
                login(request, user)
                return redirect('learner_dash')
            except IntegrityError:
                messages.error(request, 'This email is already registered. Please use a different one.')
                return render(request, 'lsign.html', {'form': form})
    else:
        form = LearnerSignUpForm()
    return render(request, 'lsign.html', {'form': form})

def mentor_signup_view(request):
    if request.method == 'POST':
        form = MentorSignUpForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password'])
                user.role = 'mentor'
                user.username = form.cleaned_data['email']
                user.save()
                Mentor.objects.create(
                    user=user,
                    experience=request.POST.get('experience'),
                    specialization=request.POST.get('specialization'),
                    application_text=request.POST.get('application_text'),
                    bio=request.POST.get('bio'),
                    form_check_video_url=request.POST.get('form_check_video_url'),
                    has_first_aid_certification='has_first_aid_certification' in request.POST,
                    status='pending'
                )
                login(request, user)
                return redirect('safety_quiz')
            except IntegrityError:
                messages.error(request, 'This email is already registered. Please use a different one.')
                return render(request, 'msign.html', {'form': form})
    else:
        form = MentorSignUpForm()
    return render(request, 'msign.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is None:
            messages.error(request, "Invalid email or password.")
            return redirect('login_view')
        if user.role == 'mentor' and user.mentor.status != 'approved':
            messages.error(request, "Your mentor application is still under review or was not approved.")
            return redirect('login_view')
        login(request, user)
        if user.role == 'learner':
            return redirect('learner_dash')
        elif user.role == 'mentor':
            return redirect('mentor_dash')
        elif user.is_staff:
            return redirect('/admin/')
        else:
            return redirect('home')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

def get_end_time_expression():
    if connection.vendor == 'sqlite':
        sql = "datetime(session_date, '+' || duration || ' minutes')"
    else:
        sql = "session_date + INTERVAL duration MINUTE"
    return ExpressionWrapper(RawSQL(sql, []), output_field=fields.DateTimeField())

@login_required
def learner_dashboard_view(request):
    learner = request.user.learner
    all_mentors = Mentor.objects.filter(status='approved')
    recommended_mentors = []

    if all_mentors.exists() and ML_AVAILABLE:
        try:
            mentor_descriptions = [f"{m.specialization} {m.bio}" for m in all_mentors]
            goal_map = {
                'weight_loss': "Help me lose weight and burn fat cardio high intensity workout diet",
                'muscle_gain': "Build muscle mass hypertrophy strength lifting bodybuilding",
                'stamina': "Increase endurance stamina running cardio conditioning aerobic",
                'flexibility': "Improve flexibility yoga stretching mobility balance",
                'sports': "Sports performance agility speed athletic training competition",
                'rehabilitation': "Injury recovery rehabilitation physiotherapy safe low impact",
            }
            learner_query = goal_map.get(learner.goal, learner.goal)
            mentor_descriptions.append(learner_query)

            tfidf = TfidfVectorizer(stop_words='english')
            tfidf_matrix = tfidf.fit_transform(mentor_descriptions)
            cosine_sim = linear_kernel(tfidf_matrix[-1], tfidf_matrix[:-1])
            
            sim_scores = list(enumerate(cosine_sim[0]))
            sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
            
            for i, score in sim_scores[:3]:
                recommended_mentors.append(all_mentors[i])
        except Exception as e:
            print(f"ML Recommendation Error: {e}")
            recommended_mentors = Mentor.objects.filter(
                status='approved', 
                specialization__icontains=learner.goal.replace('_', ' ')
            ).order_by('-points')[:3]
    else:
        recommended_mentors = Mentor.objects.filter(
            status='approved', 
            specialization__icontains=learner.goal.replace('_', ' ')
        ).order_by('-points')[:3]

    upcoming_session_count = Booking.objects.annotate(
        end_time=get_end_time_expression()
    ).filter(learner=learner, end_time__gte=timezone.now()).count()
    
    completed_sessions = Booking.objects.filter(learner=learner, status='completed')
    
    context = {
        'learner': learner,
        'recommended_mentors': recommended_mentors,
        'upcoming_session_count': upcoming_session_count,
        'completed_session_count': completed_sessions.count(),
        'points_given_to_mentors': completed_sessions.aggregate(total=Sum('points_awarded'))['total'] or 0,
    }
    return render(request, 'learner_dash.html', context)

@login_required
def mentor_dashboard_view(request):
    mentor = request.user.mentor
    upcoming_bookings = Booking.objects.annotate(
        end_time=get_end_time_expression()
    ).filter(mentor=mentor, end_time__gte=timezone.now()).order_by('session_date')
    context = {'mentor': mentor, 'upcoming_bookings': upcoming_bookings}
    return render(request, 'mentor_dash.html', context)

@login_required
def booking_view(request):
    user = request.user
    now = timezone.now()
    all_bookings = Booking.objects.annotate(end_time=get_end_time_expression())
    if user.role == 'learner':
        upcoming = all_bookings.filter(learner=user.learner, end_time__gte=now).order_by('session_date')
        completed = all_bookings.filter(learner=user.learner, end_time__lt=now).order_by('-session_date')
    else:
        upcoming = all_bookings.filter(mentor=user.mentor, end_time__gte=now).order_by('session_date')
        completed = all_bookings.filter(mentor=user.mentor, end_time__lt=now).order_by('-session_date')
    context = {'upcoming_sessions': upcoming, 'completed_sessions': completed, 'user_role': user.role}
    return render(request, 'booking.html', context)

@login_required
def book_session_view(request, mentor_id):
    if not hasattr(request.user, 'learner'):
        messages.error(request, "Only registered learners can book sessions.")
        return redirect('home')

    mentor = Mentor.objects.get(pk=mentor_id)
    if request.method == 'POST':
        date_str, time_str = request.POST.get('session_date'), request.POST.get('session_time')
        session_start_time = timezone.make_aware(datetime.strptime(f'{date_str} {time_str}', '%Y-%m-%d %H:%M'))
        session_end_time = session_start_time + timedelta(minutes=30)
        
        if session_start_time < timezone.now():
            messages.error(request, "You cannot book a session in the past.")
            return render(request, 'book_session_form.html', {'mentor': mentor})
        
        conflicting_bookings = Booking.objects.annotate(
            end_time=get_end_time_expression()
        ).filter(
            mentor=mentor,
            session_date__lt=session_end_time,
            end_time__gt=session_start_time
        )
        if conflicting_bookings.exists():
            messages.error(request, "This time slot is no longer available.")
            return render(request, 'book_session_form.html', {'mentor': mentor})
        
        Booking.objects.create(learner=request.user.learner, mentor=mentor, session_date=session_start_time, duration=30)
        messages.success(request, f"Session with {mentor.user.full_name} booked successfully!")
        return redirect('booking')
    return render(request, 'book_session_form.html', {'mentor': mentor})

@login_required
def award_points_view(request, session_id):
    if request.method == 'POST':
        session = Booking.objects.get(id=session_id, learner=request.user.learner)
        points = int(request.POST.get('points'))
        session.points_awarded = points
        session.status = 'completed'
        session.save()
        mentor = session.mentor
        mentor.points += points
        mentor.save()
        return redirect('booking')
    return redirect('booking')

@login_required
def mentor_profiles_view(request):
    mentors = Mentor.objects.filter(status='approved').order_by('-points')
    return render(request, 'mentor_profiles.html', {'mentors': mentors})

@login_required
def leaderboard_view(request):
    ranked_mentors = Mentor.objects.filter(status='approved').order_by('-points')[:10]
    return render(request, 'leaderboard.html', {'mentors': ranked_mentors})

@login_required
def progress_tracker_view(request):
    learner = request.user.learner
    completed = Booking.objects.annotate(
        end_time=get_end_time_expression()
    ).filter(learner=learner, end_time__lt=timezone.now())
    context = {
        'completed_sessions': completed,
        'session_count': completed.count(),
        'total_points': completed.aggregate(total=Sum('points_awarded'))['total'] or 0,
    }
    return render(request, 'progress_track.html', context)

@login_required
def diet_plans_view(request):
    learner = request.user.learner
    plans = DietPlan.objects.filter(goal=learner.goal)
    context = {'diet_plans': plans, 'learner_goal': learner.get_goal_display()}
    return render(request, 'diet_plans.html', context)

# --- NEW VIEW FOR DYNAMIC DIET ---
@login_required
def dynamic_diet_view(request):
    plan = None
    learner = request.user.learner
    preference = 'vegetarian' # Default
    
    if request.method == 'POST':
        preference = request.POST.get('preference')
        plan = generate_smart_diet_plan(learner.goal, preference)
        
    return render(request, 'dynamic_diet.html', {
        'plan': plan,
        'learner': learner
    })

def application_submitted_view(request):
    return render(request, 'application_submitted.html')

@login_required
def safety_quiz_view(request):
    if request.user.role != 'mentor':
        return redirect('home')
    if request.user.mentor.passed_safety_quiz:
        return redirect('application_submitted')
    if request.method == 'POST':
        correct_answers = {'q1': 'b', 'q2': 'a', 'q3': 'c'}
        score = 0
        for q, a in correct_answers.items():
            if request.POST.get(q) == a:
                score += 1
        passed = (score == len(correct_answers))
        mentor = request.user.mentor
        mentor.passed_safety_quiz = passed
        mentor.save()
        logout(request)
        return redirect('application_submitted')
    return render(request, 'safety_quiz.html')

@login_required
def chat_view(request, booking_id):
    booking = Booking.objects.get(id=booking_id)
    if request.user != booking.learner.user and request.user != booking.mentor.user:
        return redirect('home')
    
    if request.user == booking.learner.user:
        other_user = booking.mentor.user
    else:
        other_user = booking.learner.user
    
    messages_list = Message.objects.filter(booking=booking).order_by('timestamp')
    
    return render(request, 'chat.html', {
        'booking': booking,
        'other_user': other_user,
        'messages': messages_list
    })