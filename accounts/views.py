from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth import get_user_model, login, logout
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from chat.models import ChatRoom
from django.utils.text import slugify
import uuid

# Create your views here.
User = get_user_model()


def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('InputEmail')  # Fixed field name
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        avatar = request.FILES.get('avatar')
        bio = request.POST.get('bio')
   
        if password1 != password2:
            messages.error(request, "Passwords didn't match")
            return render(request, 'accounts/register.html')
   
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
            return render(request, 'accounts/register.html')
   
        if email and User.objects.filter(email=email).exists():
            messages.error(request, "This email is already in use, please use a different email")
            return render(request, 'accounts/register.html')
   
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )
        if avatar:
            user.avatar = avatar
   
        if bio:
            user.bio = bio
        user.save()
        messages.success(request, "Account created successfully! Please log in.")
        return redirect('login')
        
    return render(request, "accounts/register.html")

def login_view(request):
     if request.method == "POST":
         username = request.POST.get('username')
         password = request.POST.get('password1')
         if User.objects.filter(username=username).exists():
             user = authenticate(request, username=username, password=password)
             if user is not None:
                 login(request, user)
                 messages.success(request, f"Welcome {username}")
                 return redirect('/')
             else:
                 messages.error(request, "Invalid password")
         else:
             messages.error(request, "Username not found")
     return render(request, "accounts/login.html")

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out")
    return redirect('login')

@login_required
def userprofile(request, username):
    profile_user = User.objects.get(username=username)
    current_user = request.user
    
    # Don't create chatroom for own profile
    show_message_button = profile_user != current_user
    
    context = {
        "username": profile_user.username,
        "bio": profile_user.bio,
        "avatar": profile_user.avatar,
        "show_message_button": show_message_button
    }
    
    return render(request, "accounts/userprofile.html", context)


@login_required
def create_or_get_chatroom(request, username):
    other_user = User.objects.get(username=username)
    current_user = request.user
    
    if current_user == other_user:
        messages.error(request, "You cannot chat with yourself")
        return redirect('index')
    
    # Create a unique, consistent slug for this user pair
    users = sorted([current_user.username, other_user.username])
    slug = f"{users[0]}-{users[1]}"
    
    # Check if chatroom already exists
    try:
        # First try to find an existing chatroom
        chatroom = ChatRoom.objects.get(
            slug=slug
        )
    except ChatRoom.DoesNotExist:
        # Create a new chatroom if it doesn't exist
        chatroom = ChatRoom.objects.create(
            user1=current_user,
            user2=other_user,
            slug=slug
        )
    
    return redirect('chatroom', slug=chatroom.slug)

@login_required
def search_view(request):
    query = request.GET.get('searchkey', '')
    
    if query:
        results = User.objects.filter(username__icontains=query).exclude(username=request.user.username)
    else:
        results = User.objects.none()
        
    return render(request, 'accounts/search.html', {'results': results})