import flet as ft
import json
from datetime import datetime
import os
import time
import subprocess

class DatabaseUI:
    def __init__(self):
        self.users_file = "users.json"
        self.messages_file = "messages.json"
        self.page = None
        self.last_message_count = 0
        self.unread_messages = {}  # Track unread messages per user
        
    def main(self, page: ft.Page):
        self.page = page
        page.title = "Database Statistics"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 20
        
        # Create main container
        main_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Database Statistics", size=30, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    self.create_user_stats(),
                    ft.Divider(),
                    self.create_message_stats(),
                ],
                spacing=20,
            ),
            padding=20,
            border_radius=10,
            bgcolor=ft.colors.WHITE,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=ft.colors.BLUE_GREY_300,
                offset=ft.Offset(0, 0),
            ),
        )
        
        page.add(main_container)
        page.update()
        
        # Start periodic update
        self.start_periodic_update()
    
    def start_periodic_update(self):
        def update_ui():
            while True:
                try:
                    # Check for new messages
                    with open(self.messages_file, "r") as f:
                        messages = json.load(f)
                    
                    current_count = len(messages)
                    if current_count > self.last_message_count:
                        # New messages detected
                        self.last_message_count = current_count
                        self.play_notification()
                        self.update_unread_counts(messages)
                        self.page.update()
                    
                    time.sleep(1)  # Check every second
                except Exception as e:
                    print(f"Error in periodic update: {e}")
                    time.sleep(5)  # Wait longer on error
        
        import threading
        threading.Thread(target=update_ui, daemon=True).start()
    
    def play_notification(self):
        try:
            # Use macOS's built-in system sound
            subprocess.run(['afplay', '/System/Library/Sounds/Ping.aiff'])
        except Exception as e:
            print(f"Error playing notification sound: {e}")
    
    def update_unread_counts(self, messages):
        # Reset unread counts
        self.unread_messages = {}
        
        # Count unread messages for each user
        for msg in messages:
            receiver = msg.get("receiver", "Unknown")
            if receiver not in self.unread_messages:
                self.unread_messages[receiver] = 0
            self.unread_messages[receiver] += 1
    
    def create_user_stats(self):
        try:
            with open(self.users_file, "r") as f:
                users = json.load(f)
            
            user_count = len(users)
            user_list = ft.ListView(
                height=200,
                spacing=10,
                padding=20,
            )
            
            for username in users:
                unread_count = self.unread_messages.get(username, 0)
                badge = None
                if unread_count > 0:
                    badge = ft.Container(
                        content=ft.Text(
                            str(unread_count if unread_count < 100 else "99+"),
                            color="#fff",
                            size=11,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER
                        ),
                        bgcolor=ft.colors.RED,
                        height=22,
                        width=22,
                        border_radius=11,
                        alignment=ft.alignment.center,
                        padding=ft.padding.symmetric(horizontal=4)
                    )
                
                user_row = ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Text(username),
                            padding=10,
                            border_radius=5,
                            bgcolor=ft.colors.BLUE_GREY_50,
                            expand=True
                        ),
                        badge if badge else ft.Container(width=0)
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                )
                
                user_list.controls.append(user_row)
            
            return ft.Column(
                controls=[
                    ft.Text(f"Total Users: {user_count}", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text("User List:", size=16),
                    user_list,
                ],
                spacing=10,
            )
        except Exception as e:
            return ft.Text(f"Error loading user data: {str(e)}", color=ft.colors.RED)
    
    def create_message_stats(self):
        try:
            with open(self.messages_file, "r") as f:
                messages = json.load(f)
            
            total_messages = len(messages)
            message_stats = {}
            
            # Count messages between each pair of users
            for msg in messages:
                sender = msg.get("sender", "Unknown")
                receiver = msg.get("receiver", "Unknown")
                pair = tuple(sorted([sender, receiver]))
                message_stats[pair] = message_stats.get(pair, 0) + 1
            
            # Create message statistics view
            stats_list = ft.ListView(
                height=300,
                spacing=10,
                padding=20,
            )
            
            for (user1, user2), count in sorted(message_stats.items(), key=lambda x: x[1], reverse=True):
                stats_list.controls.append(
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text(f"{user1} ↔️ {user2}", weight=ft.FontWeight.BOLD),
                                ft.Text(f"Messages exchanged: {count}"),
                            ],
                            spacing=5,
                        ),
                        padding=10,
                        border_radius=5,
                        bgcolor=ft.colors.BLUE_GREY_50,
                    )
                )
            
            return ft.Column(
                controls=[
                    ft.Text(f"Total Messages: {total_messages}", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text("Message Statistics:", size=16),
                    stats_list,
                ],
                spacing=10,
            )
        except Exception as e:
            return ft.Text(f"Error loading message data: {str(e)}", color=ft.colors.RED)

def main():
    ft.app(target=DatabaseUI().main)

if __name__ == "__main__":
    main() 