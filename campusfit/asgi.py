import os
from django.core.asgi import get_asgi_application

# 1. Set the settings module first
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campusfit.settings')

# 2. Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

# 3. Now it's safe to import Channels and your app routing
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import app.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            app.routing.websocket_urlpatterns
        )
    ),
})