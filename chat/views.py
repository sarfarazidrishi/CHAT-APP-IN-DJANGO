from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import ChatRoom, ChatMessage, GroupMembership, GroupMessage, GroupChatRoom
from django.contrib import messages
from django.utils.text import slugify
from django.contrib.auth import get_user_model, login, logout
import uuid

User = get_user_model()

# @login_required
def index_view(request):
    # Get all chatrooms where the current user is participating
    # We extract usernames from the chatroom slug (format: "user1-user2")
    user_chatrooms = []
    all_chatrooms = ChatRoom.objects.all()
    
    for chatroom in all_chatrooms:
        usernames = chatroom.slug.split('-')
        if request.user.username in usernames:
            user_chatrooms.append(chatroom)
    
    return render(request, "chat/index.html", {"chatrooms": user_chatrooms})

def home(request):
    # If the user is already logged in, redirect to the index
    if request.user.is_authenticated:
        return redirect('index')
    return render(request, "chat/home.html")

@login_required
def chat_view(request, slug):
    chatroom = get_object_or_404(ChatRoom, slug=slug)
    
    # Security check: make sure the current user is part of this chat
    usernames = chatroom.slug.split('-')
    if request.user.username not in usernames:
        messages.error(request, "You don't have access to this chat room")
        return redirect('index')
    
    # Get the other user in the chat
    other_username = usernames[0] if usernames[1] == request.user.username else usernames[1]
    
    messages = ChatMessage.objects.filter(chatroomname=chatroom)
    return render(request, "chat/chatroom.html", {
        'chatroom': chatroom, 
        'messages': messages,
        'other_username': other_username
    })

@login_required
def create_group(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        selected_users = request.POST.getlist('selected_users')
        
        if not name:
            messages.error(request, "Group name is required")
            return redirect('create_group')
            
        if GroupChatRoom.objects.filter(name=name).exists():
            messages.error(request, "A group with this name already exists")
            return redirect('create_group')
        
        # Create a unique slug
        slug = slugify(name)
        if GroupChatRoom.objects.filter(slug=slug).exists():
            slug = f"{slug}-{uuid.uuid4().hex[:8]}"
        
        # Create the group
        group = GroupChatRoom.objects.create(
            name=name,
            description=description,
            slug=slug,
            admin=request.user
        )
        
        # Add creator as admin member
        GroupMembership.objects.create(
            user=request.user,
            group=group,
            is_admin=True
        )
        
        # Add selected users as members
        for user_id in selected_users:
            try:
                user = User.objects.get(id=user_id)
                GroupMembership.objects.create(
                    user=user,
                    group=group
                )
            except User.DoesNotExist:
                pass
        
        messages.success(request, f"Group '{name}' created successfully!")
        return redirect('group_chat', slug=slug)
    
    # Get users the current user has chatted with
    chat_users = []
    all_chatrooms = ChatRoom.objects.all()
    
    for chatroom in all_chatrooms:
        usernames = chatroom.slug.split('-')
        if request.user.username in usernames:
            other_username = usernames[0] if usernames[1] == request.user.username else usernames[1]
            try:
                other_user = User.objects.get(username=other_username)
                if other_user not in chat_users:
                    chat_users.append(other_user)
            except User.DoesNotExist:
                pass
    
    return render(request, 'chat/create_group.html', {'chat_users': chat_users})

@login_required
def group_chat(request, slug):
    group = get_object_or_404(GroupChatRoom, slug=slug)
    
    # Check if user is a member
    is_member = GroupMembership.objects.filter(user=request.user, group=group).exists()
    if not is_member:
        messages.error(request, "You are not a member of this group")
        return redirect('index')
    
    # Get user's admin status
    is_admin = GroupMembership.objects.filter(
        user=request.user, 
        group=group, 
        is_admin=True
    ).exists()
    
    # Get all messages for this group
    group_messages = GroupMessage.objects.filter(group=group).order_by('date')
    
    # Get all members
    members = GroupMembership.objects.filter(group=group).select_related('user')
    
    # Check if user is the only admin
    is_only_admin = is_admin and GroupMembership.objects.filter(group=group, is_admin=True).count() == 1
    
    return render(request, 'chat/group_chat.html', {
        'group': group,
        'messages': group_messages,
        'members': members,
        'is_admin': is_admin,
        'is_only_admin': is_only_admin,
        'member_count': members.count()
    })

@login_required
def invite_to_group(request, slug):
    group = get_object_or_404(GroupChatRoom, slug=slug)
    # Check if user is admin
    is_admin = GroupMembership.objects.filter(
        user=request.user, 
        group=group, 
        is_admin=True
    ).exists()
      
    if not is_admin:
        messages.error(request, "Only admins can invite users")
        return redirect('group_chat', slug=slug)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        try:
            user_to_invite = User.objects.get(username=username)
            
            # Check if already a member
            if GroupMembership.objects.filter(user=user_to_invite, group=group).exists():
                messages.error(request, f"{username} is already a member")
                return redirect('invite_to_group', slug=slug)
            
            # Add as member
            GroupMembership.objects.create(
                user=user_to_invite,
                group=group
            )
            
            messages.success(request, f"{username} has been added to the group")
            return redirect('group_chat', slug=slug)
            
        except User.DoesNotExist:
            messages.error(request, f"User {username} not found")
    
    # Get all users who are not members
    existing_members = GroupMembership.objects.filter(group=group).values_list('user', flat=True)
    potential_members = User.objects.exclude(id__in=existing_members)
    
    return render(request, 'chat/invite_to_group.html', {
        'group': group,
        'potential_members': potential_members
    })

@login_required
def leave_group(request, slug):
    group = get_object_or_404(GroupChatRoom, slug=slug)
    
    # Check if user is a member
    membership = get_object_or_404(GroupMembership, user=request.user, group=group)
    
    # Check if user is the admin and the only admin
    if membership.is_admin and GroupMembership.objects.filter(group=group, is_admin=True).count() == 1:
        # Check if there are other members
        if GroupMembership.objects.filter(group=group).count() > 1:
            # If there are other members but no other admins, make the oldest member an adminw
             oldest_member = GroupMembership.objects.filter(
                 group=group
             ).exclude(
                 user=request.user
             ).order_by('joined_at').first()
             
             if oldest_member:
                 oldest_member.is_admin = True
                 oldest_member.save()
                 messages.info(request, f"{oldest_member.user.username} has been made an admin")

        
        # Last person in group, delete the group
        if GroupMembership.objects.filter(group=group).count() <= 1:
            group_name = group.name
            group.delete()
            messages.info(request, f"Group '{group_name}' has been deleted as you were the last member")
            return redirect('index')
    
    # Regular member or not the only admin
    membership.delete()
    messages.success(request, f"You have left the group '{group.name}'")
    return redirect('index')

@login_required
def make_admin(request, slug, user_id):
    group = get_object_or_404(GroupChatRoom, slug=slug)
    
    # Check if requester is admin
    is_admin = GroupMembership.objects.filter(
        user=request.user, 
        group=group, 
        is_admin=True
    ).exists()
    
    if not is_admin:
        messages.error(request, "Only admins can assign admin privileges")
        return redirect('group_chat', slug=slug)
    
    # Find the user to make admin
    target_membership = get_object_or_404(
        GroupMembership, 
        user_id=user_id,
        group=group
    )
    
    target_membership.is_admin = True
    target_membership.save()
    
    messages.success(request, f"{target_membership.user.username} is now an admin")
    return redirect('group_chat', slug=slug)

@login_required
def remove_from_group(request, slug, user_id):
    group = get_object_or_404(GroupChatRoom, slug=slug)
    
    # Check if requester is admin
    is_admin = GroupMembership.objects.filter(
        user=request.user, 
        group=group, 
        is_admin=True
    ).exists()
    
    if not is_admin:
        messages.error(request, "Only admins can remove members")
        return redirect('group_chat', slug=slug)
    
    # Can't remove yourself this way
    if int(user_id) == request.user.id:
        messages.error(request, "Use 'Leave Group' to remove yourself")
        return redirect('group_chat', slug=slug)
    
    # Find the membership to remove
    membership = get_object_or_404(
        GroupMembership, 
        user_id=user_id,
        group=group
    )
    
    username = membership.user.username
    membership.delete()
    
    messages.success(request, f"{username} has been removed from the group")
    return redirect('group_chat', slug=slug)

def group_chat_message(request):
    # This function should handle WebSocket connections in Django Channels consumer
    # See additional consumer.py file for WebSocket implementation
    pass