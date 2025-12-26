import os
import django
from django.contrib.auth import get_user_model

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "campusfit.settings")
django.setup()

User = get_user_model()

# Create superuser if it doesn't exist
def create_admin():
    username = "ajith"
    password = "9059907938"  # <--- This will be your password
    email = "ajithonlinee@gmail.com"

    if not User.objects.filter(username=username).exists():
        print("Creating superuser...")
        User.objects.create_superuser(username=username, email=email, password=password)
        print("Superuser 'admin' created!")
    else:
        print("Superuser already exists.")

if __name__ == "__main__":
    create_admin()