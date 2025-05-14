from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone


User = get_user_model()

class ChatRoom(models.Model):
    user1 = models.ForeignKey(User, related_name='chatroom_user1', on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name='chatroom_user2', on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    slug = models.SlugField(unique=True, blank=True)
   
    def __str__(self):
        return f"Chatroom between {self.user1.username} and {self.user2.username}"

    @classmethod
    def get_or_create_chatroom(cls, user1, user2):
        # Check if chatroom already exists
        chatroom, created = cls.objects.get_or_create(
            user1__in=[user1, user2], user2__in=[user1, user2]
        )
        return chatroom

class ChatMessage(models.Model):
    user= models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    chatroomname= models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    message_content= models.TextField()
    date= models.DateTimeField(auto_now=True)

    class Meta:
        ordering=('date',)

class GroupChatRoom(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_of')
    
    def __str__(self):
        return self.name

class GroupMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(GroupChatRoom, on_delete=models.CASCADE, related_name='memberships')
    joined_at = models.DateTimeField(default=timezone.now)
    is_admin = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('user', 'group')
    
    def __str__(self):
        return f"{self.user.username} in {self.group.name}"

class GroupMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(GroupChatRoom, on_delete=models.CASCADE, related_name='messages')
    message_content = models.TextField()
    date = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ('date',)