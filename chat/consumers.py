# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import GroupChatRoom, GroupMessage, GroupMembership, ChatRoom, ChatMessage

User = get_user_model()

class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_slug = self.scope['url_route']['kwargs']['group_id']
        self.room_group_name = f'group_chat_{self.group_slug}'

        # Check if the user is authenticated and a member of the group
        if self.scope['user'].is_anonymous:
            await self.close()
            return

        is_member = await self.check_membership(self.scope['user'], self.group_slug)
        if not is_member:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'message')
        username = data.get('username')
        group_slug = data.get('group_slug')
        
        if message_type == 'message':
            message = data.get('message')
            
            # Save message to database
            await self.store_message(username, message, group_slug)
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': username
                }
            )
        elif message_type == 'typing':
            is_typing = data.get('isTyping')
            
            # Send typing status to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_status',
                    'username': username,
                    'isTyping': is_typing
                }
            )
        elif message_type == 'user_joined':
            # Send user joined notification
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_joined',
                    'username': username
                }
            )
        elif message_type == 'user_left':
            # Send user left notification
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_left',
                    'username': username
                }
            )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        username = event['username']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': message,
            'username': username
        }))

    async def typing_status(self, event):
        username = event['username']
        is_typing = event['isTyping']
        
        # Send typing status to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'username': username,
            'isTyping': is_typing
        }))

    async def user_joined(self, event):
        username = event['username']
        
        # Send user joined notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'username': username
        }))

    async def user_left(self, event):
        username = event['username']
        
        # Send user left notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'username': username
        }))

    @database_sync_to_async
    def store_message(self, username, message_content, group_slug):
        try:
            user = User.objects.get(username=username)
            group = GroupChatRoom.objects.get(slug=group_slug)
            
            GroupMessage.objects.create(
                user=user,
                group=group,
                message_content=message_content,
                date=timezone.now()
            )
            
            return True
        except (User.DoesNotExist, GroupChatRoom.DoesNotExist):
            return False

    @database_sync_to_async
    def check_membership(self, user, group_slug):
        try:
            group = GroupChatRoom.objects.get(slug=group_slug)
            return GroupMembership.objects.filter(user=user, group=group).exists()
        except GroupChatRoom.DoesNotExist:
            return False

# chat/consumers.py - Add this to your existing file

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # Check if the user is authenticated
        if self.scope['user'].is_anonymous:
            await self.close()
            return
            
        # Check if the user is part of this chat (verify user is in the chatroom slug)
        usernames = self.room_name.split('-')
        if self.scope['user'].username not in usernames:
            await self.close()
            return

        # Add the user to the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'message')
        username = data.get('username')
        
        if message_type == 'message':
            message = data.get('message')
            chatroomname = data.get('chatroomname')
            
            # Save message to database
            await self.store_message(username, message, chatroomname)
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': username,
                }
            )
        elif message_type == 'typing':
            is_typing = data.get('isTyping')
            
            # Send typing status to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_status',
                    'username': username,
                    'isTyping': is_typing
                }
            )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        username = event['username']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': message,
            'username': username,
        }))
    
    # Receive typing status from room group
    async def typing_status(self, event):
        username = event['username']
        is_typing = event['isTyping']
        
        # Send typing status to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'username': username,
            'isTyping': is_typing
        }))
        
    @database_sync_to_async
    def store_message(self, username, message_content, chatroomname):
        try:
            user = User.objects.get(username=username)
            chatroom = ChatRoom.objects.get(slug=chatroomname)
            
            ChatMessage.objects.create(
                user=user,
                chatroomname=chatroom,
                message_content=message_content,
                date=timezone.now()
            )
            
            return True
        except (User.DoesNotExist, ChatRoom.DoesNotExist):
            return False