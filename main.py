import flet as ft
from database import Database
import time
import os
from datetime import datetime
import threading
import json
import emoji
from comm_client import CommClient
import asyncio
import base64
from playsound import playsound

class OfficeMessenger:
    def __init__(self):
        self.db = Database()
        self.current_user = None
        self.chat_with = None
        self.message_update_timer = None
        self.network = None
        self.is_dark_theme = False
        self.emoji_data = list(emoji.EMOJI_DATA.keys())
        self.unseen_messages = {}  # Track unseen messages per user
        self.comm_client = None
        self.comm_loop = None
        self.comm_thread = None
        self._pending_update = False
        self.typing_timeout = None  # For debouncing typing events
        self.typing_users = set()   # Track who is typing
        self.sent_message_ids = set()  # Track message IDs we've already processed
        self.chat_scroll_pos = 0  # Track chat scroll position
        self.notification_sound = "notification.wav"  # Path to notification sound
        
    def main(self, page: ft.Page):
        # Configure page
        page.title = "Office IP Messenger"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.window_width = 1200
        page.window_height = 800
        page.window_resizable = True
        page.padding = 0
        page.bgcolor = "#f5f5f5"
        
        # Define colors - will be updated when theme changes
        self.theme = {
            "light": {
                "primary_color": "#2196F3",
                "secondary_color": "#E8F4FD",
                "accent_color": "#1976D2",
                "text_color": "#212121",
                "error_color": "#F44336",
                "background_color": "#F5F8FA",
                "card_color": "#FFFFFF",
                "message_sent": "#E3F2FD",
                "message_received": "#FFFFFF",
                "message_text_sent": "#0D47A1",
                "message_text_received": "#212121",
                "border_color": "#EEEEEE",
                "hover_color": "#F5F5F5",
                "button_text_color": "#FFFFFF",
                "icon_color": "#2196F3"
            },
            "dark": {
                "primary_color": "#2196F3",
                "secondary_color": "#1E2A38",
                "accent_color": "#64B5F6",
                "text_color": "#E0E0E0",
                "error_color": "#EF5350",
                "background_color": "#121212",
                "card_color": "#1E1E1E",
                "message_sent": "#1565C0",
                "message_received": "#263238",
                "message_text_sent": "#FFFFFF",
                "message_text_received": "#E0E0E0",
                "border_color": "#333333",
                "hover_color": "#252525",
                "button_text_color": "#FFFFFF",
                "icon_color": "#64B5F6"
            }
        }
        
        current_theme = self.theme["light"]
        
        def handle_typing(e):
            """Handle typing events with debounce using threading.Timer"""
            if not self.chat_with:
                return
            # Send typing status
            self.set_typing(True)
            # Cancel previous timer
            if self.typing_timeout:
                try:
                    self.typing_timeout.cancel()
                except:
                    pass
            # Schedule clearing typing status after 3 seconds
            timer = threading.Timer(3, lambda: self.set_typing(False))
            timer.daemon = True
            timer.start()
            self.typing_timeout = timer

        def send_message(e):
            if not self.message_field.value:
                return
            if not self.chat_with:
                return
            # If a file is pending, send it as JSON payload
            if hasattr(self, 'pending_file') and self.pending_file:
                message = json.dumps(self.pending_file)
                # clear pending file
                del self.pending_file
            else:
                message = self.message_field.value
            
            # Generate a unique message ID
            msg_id = f"{self.current_user}_{self.chat_with}_{time.time()}"
            self.sent_message_ids.add(msg_id)
            
            # Send via CommClient
            if self.comm_client and self.comm_loop:
                print(f"[DEBUG] Sending message to {self.chat_with}: {message}")
                asyncio.run_coroutine_threadsafe(
                    self.comm_client.send_message(self.chat_with, message, msg_id),
                    self.comm_loop
                )
                # Also save message locally to display immediately for sender
                self.db.save_message(self.current_user, self.chat_with, message)
                # Update the chat view to show sent message immediately
                self.update_chat()
            self.message_field.value = ""
            # Turn off typing indicator when sending a message
            self.set_typing(False)
            page.update()

        # Now create message field with the handler
        self.message_field = ft.TextField(
            hint_text="Type your message...",
            border=ft.InputBorder.NONE,
            multiline=True,
            min_lines=1,
            max_lines=5,
            expand=True,
            text_size=14,
            content_padding=ft.padding.symmetric(horizontal=20, vertical=12),
            cursor_color=current_theme["primary_color"],
            bgcolor=current_theme["card_color"],
            color=current_theme["text_color"],
            on_change=handle_typing,
            on_submit=send_message,
            data="message_field"
        )
        
        # Store the handler for later use if needed
        self._handle_typing = handle_typing
        
        # Login components
        self.username_field = ft.TextField(
            label="Username",
            border=ft.InputBorder.OUTLINE,
            width=350,
            autofocus=True,
            border_color=current_theme["border_color"],
            focused_border_color=current_theme["primary_color"],
            text_size=14,
            hint_style=ft.TextStyle(color=ft.Colors.with_opacity(0.5, current_theme["text_color"])),
            cursor_color=current_theme["primary_color"],
            content_padding=ft.padding.symmetric(horizontal=16, vertical=12),
            prefix_icon=ft.Icons.PERSON_OUTLINE
        )
        
        self.password_field = ft.TextField(
            label="Password",
            border=ft.InputBorder.OUTLINE,
            password=True,
            can_reveal_password=True,
            width=350,
            border_color=current_theme["border_color"],
            focused_border_color=current_theme["primary_color"],
            text_size=14,
            hint_style=ft.TextStyle(color=ft.Colors.with_opacity(0.5, current_theme["text_color"])),
            cursor_color=current_theme["primary_color"],
            content_padding=ft.padding.symmetric(horizontal=16, vertical=12),
            prefix_icon=ft.Icons.LOCK_OUTLINE
        )
        
        self.login_message = ft.Text("", color=current_theme["error_color"], size=14)
        
        # Chat components
        self.user_list = ft.ListView(
            spacing=10,
            padding=20,
            auto_scroll=True,
            expand=True
        )
        
        self.chat_view = ft.ListView(
            spacing=10,
            padding=20,
            auto_scroll=False,  # Disable auto scroll so we can control it
            expand=True,
            on_scroll=self.on_chat_scroll
        )
        
        # Emoji picker
        self.emoji_grid = ft.GridView(
            expand=True,
            max_extent=38,
            spacing=5,
            run_spacing=5,
            padding=10,
            visible=False,
            height=200,
            data="emoji_grid"  # Add identifier
        )
        
        # Common emojis for better selection
        common_emojis = ["ᶠᶸᶜᵏMe𓀐𓂸", "😂", "😊", "😎", "🥰", "😍", "🤔", "👍", "👋", "🙏", 
                         "🎉", "🔥", "❤️", "✅", "⭐", "🌟", "💯", "🤝", "👏", "💪",
                         "😁", "😉", "😋", "😇", "🥳", "😜", "😄", "🤣", "😌", "😴","( ◡̀_◡́)ᕤ","（ ͜.人 ͜.）"]
        
        # Add emojis to grid with proper event handling
        for emoji_char in common_emojis:
            self.emoji_grid.controls.append(
                ft.Container(
                    content=ft.Text(emoji_char, size=20),
                    alignment=ft.alignment.center,
                    width=30,
                    height=30,
                    border_radius=5,
                    on_click=lambda e, emoji=emoji_char: self.insert_emoji(emoji),
                    data="emoji_container"  # Add identifier
                )
            )
        
        # Create a Text control for chat header
        self.chat_header = ft.Text(
            "",
            size=18,
            weight=ft.FontWeight.BOLD,
            color=current_theme["text_color"]
        )
        
        # File picker
        def on_file_selected(e):
            if e.files and len(e.files) > 0:
                file_info = e.files[0]
                file_name = file_info.name
                file_path = file_info.path
                # Read and encode file content
                with open(file_path, 'rb') as f:
                    data = f.read()
                encoded = base64.b64encode(data).decode('utf-8')
                # Store pending file payload
                self.pending_file = {"name": file_name, "data": encoded}
                # Update field to show attachment
                self.message_field.value = f"📎 File: {file_name}"

        self.file_picker = ft.FilePicker(on_result=on_file_selected)
        page.overlay.append(self.file_picker)
        
        def login_click(e):
            username = self.username_field.value
            password = self.password_field.value
            if not username or not password:
                self.login_message.value = "Please enter both username and password"
                page.update()
                return
            success, message = self.db.authenticate_user(username, password)
            if success:
                self.current_user = username
                self.chat_with = None  # Reset chat_with when logging in
                self.login_message.value = ""
                # Clear any existing messages in the chat view
                self.chat_view.controls.clear()
                self.chat_header.value = ""
                # Initialize CommClient
                self.comm_client = CommClient(username)
                self.comm_loop = asyncio.new_event_loop()
                def run_ws():
                    asyncio.set_event_loop(self.comm_loop)
                    self.comm_loop.run_until_complete(self.comm_client.connect_ws())
                self.comm_thread = threading.Thread(target=run_ws, daemon=True)
                self.comm_thread.start()
                # Set up event handlers
                self.comm_client.on_message = self.handle_received_message
                self.comm_client.on_status = self.handle_status_update
                self.comm_client.on_typing = self.handle_typing_update
                # Remove legacy NetworkManager initialization
                self.show_chat_screen()
                page.update()
            else:
                self.login_message.value = message
                page.update()
        
        def register_click(e):
            username = self.username_field.value
            password = self.password_field.value
            
            if not username or not password:
                self.login_message.value = "Please enter both username and password"
                page.update()
                return
                
            success, message = self.db.register_user(username, password)
            
            if success:
                self.login_message.value = "Registration successful! You can now login."
                page.update()
            else:
                self.login_message.value = message
                page.update()
        
        def toggle_emoji_picker(e):
            # Toggle the emoji grid visibility
            self.emoji_grid.visible = not self.emoji_grid.visible
            # Toggle the wrapper container visibility and height
            # chat_screen.controls[1] is the chat area
            chat_area = self.chat_screen.controls[1]
            for col_control in chat_area.content.controls:
                if isinstance(col_control, ft.Container) and col_control.content == self.emoji_grid:
                    col_control.visible = self.emoji_grid.visible
                    col_control.height = 200 if self.emoji_grid.visible else 0
                    break
            # Refresh UI
            page.update()
        
        def upload_file(e):
            self.file_picker.pick_files(allow_multiple=False)
        
        def select_user(e):
            self.chat_with = e.control.data
            # Clear unread count for this user
            if self.chat_with in self.unseen_messages:
                self.unseen_messages[self.chat_with] = 0
            self.update_chat()
            page.update()
        
        def logout(e):
            self.current_user = None
            self.chat_with = None
            
            # Stop the network server
            if self.network:
                self.network.stop()
                self.network = None
            
            # Stop the websocket client
            if self.comm_client:
                self.comm_client.stop()
            
            # Clear any timers
            if self.typing_timeout:
                try:
                    self.page.clear_interval(self.typing_timeout)
                except Exception as ex:
                    print(f"Error clearing typing timeout: {ex}")
                self.typing_timeout = None
            
            # Remove user from peers list
            try:
                with open("peers.json", "r") as f:
                    peers = json.loads(f.read())
                
                if self.current_user in peers:
                    del peers[self.current_user]
                    
                with open("peers.json", "w") as f:
                    json.dump(peers, f)
            except:
                pass
            
            # Clear chat view and header
            self.chat_view.controls.clear()
            self.chat_header.value = ""
            
            self.show_login_screen()
            page.update()
        
        def toggle_theme(e):
            self.is_dark_theme = not self.is_dark_theme
            theme_mode = "dark" if self.is_dark_theme else "light"
            current_theme = self.theme[theme_mode]
            
            # Update page theme
            page.theme_mode = ft.ThemeMode.DARK if self.is_dark_theme else ft.ThemeMode.LIGHT
            page.bgcolor = current_theme["background_color"]
            
            # Update login screen if it exists
            if hasattr(self, 'login_screen'):
                self.update_login_screen_theme(current_theme)
            
            # Update chat screen if it exists
            if hasattr(self, 'chat_screen'):
                self.update_chat_screen_theme(current_theme)
            
            # Update message field
            if hasattr(self, 'message_field'):
                self.message_field.bgcolor = current_theme["card_color"]
                self.message_field.color = current_theme["text_color"]
            
            # Update emoji grid
            if hasattr(self, 'emoji_grid'):
                for emoji_container in self.emoji_grid.controls:
                    emoji_container.bgcolor = current_theme["card_color"]
                    emoji_container.on_hover = lambda e: setattr(e.control, 'bgcolor', 
                        current_theme["secondary_color"] if e.data == "true" else current_theme["card_color"])
            
            # Force update all controls
            page.update()
        
        # Login screen
        self.login_screen = ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Column([
                            ft.Container(
                                content=ft.Image(
                                    src="assets/icon.png" if os.path.exists("assets/icon.png") else None,
                                    width=100,
                                    height=100,
                                    fit=ft.ImageFit.CONTAIN,
                                ),
                                alignment=ft.alignment.center,
                                margin=ft.margin.only(bottom=20),
                            ),
                            ft.Text(
                                "Office IP Messenger",
                                size=32,
                                weight=ft.FontWeight.BOLD,
                                color=current_theme["primary_color"],
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Text(
                                "Secure Enterprise Communication",
                                size=16,
                                color=current_theme["text_color"],
                                opacity=0.7,
                                text_align=ft.TextAlign.CENTER,
                            )
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        margin=ft.margin.only(bottom=30),
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(
                        content=ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Container(
                                        content=ft.Text(
                                            "Welcome Back",
                                            size=24,
                                            weight=ft.FontWeight.BOLD,
                                            color=current_theme["text_color"],
                                        ),
                                        margin=ft.margin.only(bottom=5),
                                    ),
                                    ft.Text(
                                        "Sign in to continue",
                                        size=14,
                                        color=current_theme["text_color"],
                                        opacity=0.7,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    ft.Divider(height=20, color=current_theme["border_color"]),
                                    self.username_field,
                                    ft.Container(height=10),
                                    self.password_field,
                                    ft.Container(
                                        content=self.login_message,
                                        margin=ft.margin.symmetric(vertical=10),
                                    ),
                                    ft.Container(
                                        content=ft.Row([
                                            ft.ElevatedButton(
                                                "Login",
                                                on_click=login_click,
                                                style=ft.ButtonStyle(
                                                    shape=ft.RoundedRectangleBorder(radius=8),
                                                    color=current_theme["button_text_color"],
                                                    bgcolor=current_theme["primary_color"],
                                                    padding=15
                                                ),
                                                expand=1,
                                            ),
                                            ft.Container(width=15),
                                            ft.OutlinedButton(
                                                "Register",
                                                on_click=register_click,
                                                style=ft.ButtonStyle(
                                                    shape=ft.RoundedRectangleBorder(radius=8),
                                                    color=current_theme["primary_color"],
                                                    side=ft.BorderSide(width=1.5, color=current_theme["primary_color"]),
                                                    padding=15
                                                ),
                                                expand=1,
                                            )
                                        ], alignment=ft.MainAxisAlignment.CENTER),
                                        margin=ft.margin.only(top=10),
                                    ),
                                    ft.Container(
                                        content=ft.IconButton(
                                            icon=ft.Icons.DARK_MODE if not self.is_dark_theme else ft.Icons.LIGHT_MODE,
                                            tooltip="Toggle theme",
                                            on_click=toggle_theme,
                                            icon_color=current_theme["icon_color"],
                                            icon_size=24,
                                        ),
                                        alignment=ft.alignment.center,
                                        margin=ft.margin.only(top=15),
                                    )
                                ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                padding=30,
                                border_radius=12,
                            ),
                            elevation=4 if not self.is_dark_theme else 2,
                        ),
                        padding=20,
                        alignment=ft.alignment.center,
                        width=400,
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            ),
            expand=True,
            padding=20,
            alignment=ft.alignment.center,
            bgcolor=current_theme["background_color"]
        )
        
        # Chat screen
        self.chat_screen = ft.Row(
            [
                # User list sidebar
                ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Row([
                                ft.Row([
                                    ft.Icon(
                                        ft.Icons.PEOPLE_ALT_ROUNDED,
                                        color=current_theme["primary_color"],
                                        size=24
                                    ),
                                    ft.Text(
                                        "Contacts",
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                        color=current_theme["text_color"]
                                    ),
                                ], spacing=10),
                                ft.Row([
                                    ft.IconButton(
                                        icon=ft.Icons.DARK_MODE if not self.is_dark_theme else ft.Icons.LIGHT_MODE,
                                        tooltip="Toggle theme",
                                        on_click=toggle_theme,
                                        icon_color=current_theme["icon_color"],
                                        icon_size=20
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.LOGOUT,
                                        tooltip="Logout",
                                        on_click=logout,
                                        icon_color=current_theme["icon_color"],
                                        icon_size=20
                                    )
                                ])
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            padding=ft.padding.symmetric(horizontal=15, vertical=15),
                            bgcolor=current_theme["card_color"]
                        ),
                        ft.Divider(height=1, color=current_theme["border_color"]),
                        ft.Container(
                            content=ft.Column([
                                ft.Container(
                                    content=ft.Row([
                                        ft.Icon(
                                            ft.Icons.SEARCH,
                                            color=current_theme["text_color"],
                                            opacity=0.7,
                                            size=20
                                        ),
                                        ft.Text(
                                            "Search contacts",
                                            size=14,
                                            color=current_theme["text_color"],
                                            opacity=0.7,
                                            italic=True
                                        )
                                    ], spacing=10),
                                    padding=ft.padding.all(10),
                                    border_radius=8,
                                    bgcolor=current_theme["background_color"],
                                ),
                                ft.Container(height=5)
                            ]),
                            padding=ft.padding.all(15),
                            bgcolor=current_theme["card_color"],
                        ),
                        ft.Container(
                            content=self.user_list,
                            expand=True,
                            bgcolor=current_theme["card_color"]
                        )
                    ]),
                    width=280,
                    bgcolor=current_theme["card_color"],
                    border=ft.border.only(right=ft.BorderSide(1, current_theme["border_color"]))
                ),
                # Chat area
                ft.Container(
                    content=ft.Column([
                        # Chat header
                        ft.Container(
                            content=ft.Row([
                                self.chat_header,
                                ft.Container(
                                    content=ft.Row([
                                        ft.IconButton(
                                            icon=ft.Icons.CALL,
                                            tooltip="Call",
                                            icon_color=current_theme["icon_color"],
                                            icon_size=20
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.VIDEOCAM,
                                            tooltip="Video Call",
                                            icon_color=current_theme["icon_color"],
                                            icon_size=20
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.MORE_VERT,
                                            tooltip="More options",
                                            icon_color=current_theme["icon_color"],
                                            icon_size=20
                                        )
                                    ]),
                                    visible=self.chat_with is not None
                                )
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            padding=ft.padding.symmetric(horizontal=20, vertical=15),
                            bgcolor=current_theme["card_color"],
                            border_radius=ft.border_radius.only(top_left=10, top_right=10)
                        ),
                        ft.Divider(height=1, color=current_theme["border_color"]),
                        # Messages
                        ft.Container(
                            content=self.chat_view,
                            expand=True,
                            bgcolor=current_theme["background_color"]
                        ),
                        # Emoji picker
                        ft.Container(
                            content=self.emoji_grid,
                            bgcolor=current_theme["card_color"],
                            border=ft.border.only(top=ft.BorderSide(1, current_theme["border_color"])),
                            visible=False,
                            height=200
                        ),
                        # Message input
                        ft.Container(
                            content=ft.Column([
                                # Typing indicator
                                ft.Container(
                                    content=ft.Row([
                                        ft.Text(
                                            f"{self.chat_with} is typing",
                                            italic=True,
                                            size=12,
                                            color=current_theme["text_color"],
                                            opacity=0.7
                                        ),
                                        ft.Container(
                                            content=ft.Text("•", size=16, color=current_theme["text_color"]),
                                            animate=ft.animation.Animation(300, ft.AnimationCurve.BOUNCE_OUT),
                                            animate_opacity=ft.animation.Animation(300, ft.AnimationCurve.BOUNCE_OUT),
                                        ),
                                        ft.Container(
                                            content=ft.Text("•", size=16, color=current_theme["text_color"]),
                                            animate=ft.animation.Animation(600, ft.AnimationCurve.BOUNCE_OUT),
                                            animate_opacity=ft.animation.Animation(600, ft.AnimationCurve.BOUNCE_OUT),
                                        ),
                                        ft.Container(
                                            content=ft.Text("•", size=16, color=current_theme["text_color"]),
                                            animate=ft.animation.Animation(900, ft.AnimationCurve.BOUNCE_OUT),
                                            animate_opacity=ft.animation.Animation(900, ft.AnimationCurve.BOUNCE_OUT),
                                        ),
                                    ], spacing=2),
                                    padding=ft.padding.symmetric(horizontal=15, vertical=5),
                                    visible=False,
                                    key="typing_indicator"
                                ),
                                ft.Row([
                                    ft.IconButton(
                                        icon=ft.Icons.EMOJI_EMOTIONS,
                                        tooltip="Insert emoji",
                                        on_click=toggle_emoji_picker,
                                        icon_color=current_theme["icon_color"],
                                        icon_size=24
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.ATTACH_FILE,
                                        tooltip="Attach file",
                                        on_click=upload_file,
                                        icon_color=current_theme["icon_color"],
                                        icon_size=24
                                    ),
                                    ft.Container(
                                        content=self.message_field,
                                        expand=True,
                                        margin=ft.margin.symmetric(horizontal=8),
                                        border_radius=30,
                                        bgcolor=current_theme["card_color"]
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.SEND_ROUNDED,
                                        tooltip="Send message",
                                        on_click=send_message,
                                        icon_color=current_theme["primary_color"],
                                        icon_size=28
                                    )
                                ], spacing=5),
                            ], spacing=0),
                            padding=ft.padding.symmetric(horizontal=15, vertical=10),
                            bgcolor=current_theme["card_color"],
                            border_radius=ft.border_radius.only(bottom_left=10, bottom_right=10),
                            shadow=ft.BoxShadow(
                                spread_radius=0,
                                blur_radius=5,
                                color="#40000000",
                                offset=ft.Offset(0, -1)
                            )
                        )
                    ]),
                    expand=True
                )
            ],
            expand=True,
            spacing=0,
            height=700  # Set a fixed height for responsiveness
        )
        
        # Set initial view
        page.add(self.login_screen)
        
        # Helper methods for UI management
        def update_user_list():
            self.user_list.controls.clear()
            users = self.db.get_all_users()
            theme_mode = "dark" if self.is_dark_theme else "light"
            current_theme = self.theme[theme_mode]
            for user in users:
                if user == self.current_user:
                    continue
                # Count unread messages
                unread_count = self.unseen_messages.get(user, 0)
                
                # Extract first letter of username for avatar
                first_letter = user[0].upper()
                
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
                        bgcolor=current_theme["primary_color"],
                        height=22,
                        width=22,
                        border_radius=11,
                        alignment=ft.alignment.center,
                        padding=ft.padding.symmetric(horizontal=4)
                    )
                
                avatar = ft.Container(
                    content=ft.Text(
                        first_letter,
                        color="#FFFFFF",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER
                    ),
                    width=38,
                    height=38,
                    bgcolor=current_theme["primary_color"],
                    border_radius=19,
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(right=10)
                )
                
                # Show online indicator
                is_online = hasattr(self, 'online_users') and user in getattr(self, 'online_users', set())
                
                user_row = ft.Row([
                    ft.Stack([
                        avatar,
                        ft.Container(
                            width=12,
                            height=12,
                            border_radius=6,
                            bgcolor="#4CAF50" if is_online else "#9E9E9E",
                            border=ft.border.all(1, "#FFFFFF"),
                            right=0,
                            bottom=0,
                            visible=True
                        )
                    ], width=38),
                    ft.Column([
                        ft.Text(
                            user,
                            size=15,
                            weight=ft.FontWeight.BOLD,
                            color=current_theme["text_color"]
                        ),
                        ft.Text(
                            "Online" if is_online else "Offline",
                            size=12,
                            color=current_theme["text_color"],
                            opacity=0.6
                        )
                    ], spacing=2, expand=True, alignment=ft.MainAxisAlignment.CENTER),
                    badge if badge else ft.Container(width=0)
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
                
                user_item = ft.Container(
                    content=user_row,
                    padding=10,
                    border_radius=8,
                    data=user,
                    on_click=select_user,
                    bgcolor=current_theme["card_color"]
                )
                if user == self.chat_with:
                    user_item.bgcolor = current_theme["secondary_color"]
                else:
                    user_item.on_hover = lambda e: setattr(e.control, 'bgcolor', 
                                                         current_theme["secondary_color"] if e.data == "true" else current_theme["card_color"])
                self.user_list.controls.append(user_item)
        
        def update_chat_view():
            # Save current position
            current_scroll = self.chat_scroll_pos
            last_message_count = len(self.chat_view.controls)
            
            self.chat_view.controls.clear()
            theme_mode = "dark" if self.is_dark_theme else "light"
            current_theme = self.theme[theme_mode]
            if not self.chat_with:
                self.chat_view.controls.append(
                    ft.Container(
                        content=ft.Text(
                            "Select a user to start chatting",
                            italic=True,
                            color="#9E9E9E",
                            size=16
                        ),
                        alignment=ft.alignment.center,
                        expand=True
                    )
                )
                return
            self.chat_header.value = f"Chat with {self.chat_with}"
            self.chat_header.color = current_theme["text_color"]
            
            messages = self.db.get_messages(self.current_user, self.chat_with)
            
            # Add messages to chat view
            for msg in messages:
                is_from_me = msg["sender"] == self.current_user
                message_text = msg["message"]
                
                # Skip encrypted messages (they should have been decrypted already)
                if message_text.startswith("gAAAAAB"):
                    message_text = "[Encrypted message]"
                
                # Try to parse JSON for file payload
                file_payload = None
                try:
                    obj = json.loads(message_text)
                    if isinstance(obj, dict) and "name" in obj and "data" in obj:
                        file_payload = obj
                except:
                    pass
                if file_payload:
                    file_name = file_payload["name"]
                    file_data = file_payload["data"]
                    # File bubble with download button
                    bubble_content = ft.Row([
                        ft.Icon(ft.Icons.ATTACHMENT, color="#FFFFFF" if is_from_me else current_theme["text_color"], size=16),
                        ft.Text(
                            file_name,
                            selectable=True,
                            color="#FFFFFF" if is_from_me else current_theme["text_color"],
                            size=14
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DOWNLOAD,
                            tooltip="Download file",
                            icon_color=current_theme["primary_color"],
                            icon_size=18,
                            on_click=lambda e, fn=file_name, fd=file_data: self.download_file(fn, fd)
                        )
                    ], spacing=5)
                    bubble = ft.Column([
                        bubble_content,
                        ft.Text(
                            datetime.fromtimestamp(msg["timestamp"]).strftime("%H:%M"),
                            size=12,
                            color="#E0E0E0" if is_from_me else "#757575"
                        )
                    ], spacing=5)
                else:
                    # Regular text message
                    bubble = ft.Column([
                        ft.Text(
                            message_text,
                            selectable=True,
                            color=current_theme["message_text_sent"] if is_from_me else current_theme["message_text_received"],
                            size=14
                        ),
                        ft.Text(
                            datetime.fromtimestamp(msg["timestamp"]).strftime("%H:%M"),
                            size=12,
                            color=current_theme["message_text_sent"] if is_from_me else current_theme["message_text_received"],
                            opacity=0.7
                        )
                    ], spacing=5)
                message_bubble = ft.Container(
                    content=bubble,
                    padding=15,
                    border_radius=ft.border_radius.only(
                        top_left=20 if is_from_me else 4,
                        top_right=4 if is_from_me else 20,
                        bottom_left=20,
                        bottom_right=20
                    ),
                    bgcolor=current_theme["message_sent"] if is_from_me else current_theme["message_received"],
                    width=400,
                    margin=ft.margin.only(left=50 if is_from_me else 0, right=0 if is_from_me else 50),
                    shadow=ft.BoxShadow(
                        spread_radius=0,
                        blur_radius=4,
                        color="#20000000",
                        offset=ft.Offset(0, 2)
                    )
                )
                self.chat_view.controls.append(
                    ft.Container(
                        content=message_bubble,
                        alignment=ft.alignment.center_right if is_from_me else ft.alignment.center_left,
                        padding=10
                    )
                )
            
            # Scroll management
            if len(messages) > 0:
                if last_message_count == 0:
                    # First load - scroll to bottom
                    self.chat_view.auto_scroll = True
                elif len(self.chat_view.controls) > last_message_count:
                    # New messages added - scroll to bottom
                    self.chat_view.auto_scroll = True 
                else:
                    # No new messages - maintain position
                    self.chat_view.auto_scroll = False
                    # Restore scroll position immediately
                    self.restore_scroll_position(current_scroll)
        
        self.update_users = update_user_list
        self.update_chat = update_chat_view
        
    def insert_emoji(self, emoji_char):
        """Insert emoji at cursor position in message field"""
        if not hasattr(self, 'message_field'):
            return
        
        current_text = self.message_field.value or ""
        cursor_position = getattr(self.message_field, 'cursor_index', len(current_text))
        
        # Insert emoji at cursor position
        new_text = current_text[:cursor_position] + emoji_char + current_text[cursor_position:]
        self.message_field.value = new_text
        
        # Update cursor position
        self.message_field.cursor_index = cursor_position + len(emoji_char)
        
        # Don't hide emoji grid after selection to allow multiple emoji selection
        self.page.update()
    
    def update_login_screen_theme(self, current_theme):
        """Update login screen with current theme colors"""
        # First update the background color
        self.login_screen.bgcolor = current_theme["background_color"]
        
        # Find and update all elements in the login screen
        for control in self.login_screen.content.controls:
            if isinstance(control, ft.Container) and control.content:
                # Update app title color
                if isinstance(control.content, ft.Column):
                    for col_item in control.content.controls:
                        if isinstance(col_item, ft.Text):
                            if "Office IP Messenger" in col_item.value:
                                col_item.color = current_theme["primary_color"]
                            elif "Secure Enterprise" in col_item.value:
                                col_item.color = current_theme["text_color"]
                
                # Update login form
                if isinstance(control.content, ft.Column):
                    for col_control in control.content.controls:
                        if isinstance(col_control, ft.Container) and isinstance(col_control.content, ft.Column):
                            # Update login card
                            container = col_control
                            container.bgcolor = current_theme["card_color"]
                            container.shadow = ft.BoxShadow(
                                spread_radius=1,
                                blur_radius=15,
                                color="#80000000" if self.is_dark_theme else "#B0BEC5",  # 50% opacity black
                                offset=ft.Offset(0, 0)
                            )
                            
                            # Update form fields and buttons
                            for item in container.content.controls:
                                if isinstance(item, ft.TextField):
                                    item.border_color = current_theme["primary_color"]
                                    item.focused_border_color = current_theme["accent_color"]
                                    item.color = current_theme["text_color"]
                                    item.bgcolor = current_theme["card_color"]
                                elif isinstance(item, ft.Text):
                                    item.color = current_theme["error_color"]
                                elif isinstance(item, ft.Row):
                                    for button in item.controls:
                                        if isinstance(button, ft.ElevatedButton):
                                            button.style.bgcolor = current_theme["primary_color"]
                                        elif isinstance(button, ft.OutlinedButton):
                                            button.style.color = current_theme["primary_color"]
                                            button.style.side = ft.BorderSide(width=1, color=current_theme["primary_color"])
                                elif isinstance(item, ft.Container) and isinstance(item.content, ft.IconButton):
                                    item.content.icon = ft.Icons.DARK_MODE if not self.is_dark_theme else ft.Icons.LIGHT_MODE
                                    item.content.icon_color = current_theme["primary_color"]
        
    def update_chat_screen_theme(self, current_theme):
        """Update chat screen with current theme colors"""
        if not hasattr(self, 'chat_screen'):
            return
        
        # Update main chat screen container
        self.chat_screen.bgcolor = current_theme["background_color"]
        
        # Update user list sidebar
        for container in self.chat_screen.controls:
            if isinstance(container, ft.Container):
                if container.width == 280:  # User list sidebar
                    container.bgcolor = current_theme["card_color"]
                    container.border = ft.border.only(right=ft.BorderSide(1, current_theme["border_color"]))
                    
                    for col_control in container.content.controls:
                        if isinstance(col_control, ft.Container):
                            col_control.bgcolor = current_theme["card_color"]
                            
                            # Update header elements
                            if isinstance(col_control.content, ft.Row):
                                for row_control in col_control.content.controls:
                                    if isinstance(row_control, ft.Row):
                                        for item in row_control.controls:
                                            if isinstance(item, ft.Icon):
                                                item.color = current_theme["primary_color"]
                                            elif isinstance(item, ft.Text):
                                                item.color = current_theme["text_color"]
                                    elif isinstance(row_control, ft.IconButton):
                                        row_control.icon_color = current_theme["icon_color"]
                    
                        elif isinstance(col_control, ft.Divider):
                            col_control.color = current_theme["border_color"]
                
                # Update chat area
                else:
                    container.bgcolor = current_theme["background_color"]
                    
                    for col_control in container.content.controls:
                        if isinstance(col_control, ft.Container):
                            if col_control.content == self.chat_view:
                                col_control.bgcolor = current_theme["background_color"]
                            elif col_control.content == self.emoji_grid:
                                col_control.bgcolor = current_theme["card_color"]
                                col_control.border = ft.border.only(top=ft.BorderSide(1, current_theme["border_color"]))
                            elif isinstance(col_control.content, ft.Row) and len(col_control.content.controls) > 0:
                                # Message input area
                                col_control.bgcolor = current_theme["card_color"]
                                for control in col_control.content.controls:
                                    if isinstance(control, ft.IconButton):
                                        control.icon_color = current_theme["icon_color"]
                                    elif isinstance(control, ft.Container) and control.content == self.message_field:
                                        control.bgcolor = current_theme["card_color"]
                                        self.message_field.bgcolor = current_theme["card_color"]
                                        self.message_field.color = current_theme["text_color"]
        
        # Update user list items
        if hasattr(self, 'user_list'):
            for user_item in self.user_list.controls:
                if isinstance(user_item, ft.Container):
                    if user_item.data == self.chat_with:
                        user_item.bgcolor = current_theme["secondary_color"]
                    else:
                        user_item.bgcolor = current_theme["card_color"]
                        user_item.on_hover = lambda e: setattr(e.control, 'bgcolor',
                            current_theme["secondary_color"] if e.data == "true" else current_theme["card_color"])
        
        # Update chat header
        if hasattr(self, 'chat_header'):
            self.chat_header.color = current_theme["text_color"]
        
        # Update emoji grid
        if hasattr(self, 'emoji_grid'):
            for emoji_container in self.emoji_grid.controls:
                emoji_container.bgcolor = current_theme["card_color"]
                emoji_container.on_hover = lambda e: setattr(e.control, 'bgcolor',
                    current_theme["secondary_color"] if e.data == "true" else current_theme["card_color"])

    async def handle_received_message(self, data):
        sender = data.get("sender")
        content = data.get("content")
        msg_id = data.get("msg_id")
        
        # Skip if we've already processed this message
        if msg_id and msg_id in self.sent_message_ids:
            print(f"[DEBUG] Skipping duplicate message with ID: {msg_id}")
            return
        
        if sender and content:
            # Add message ID to our tracking set if it has one
            if msg_id:
                self.sent_message_ids.add(msg_id)
            
            # For messages from other users to me, save them
            if sender != self.current_user:
                print(f"[DEBUG] Received message from {sender}: {content}")
                self.db.save_message(sender, self.current_user, content)
                if self.chat_with != sender:
                    # Increment unread count
                    self.unseen_messages[sender] = self.unseen_messages.get(sender, 0) + 1
                    # Play notification sound
                    self.play_notification()
            
            # Update UI if we're in the relevant chat
            if self.chat_with == sender:
                self.update_chat()
                self.page.update()
            else:
                # Just update the user list to show unread count
                self.update_users()
                self.page.update()
    
    async def handle_status_update(self, data):
        # data: {'type': 'status', 'online': [...]}
        # Highlight online users in the user list
        self.online_users = set(data.get('online', []))
        self.update_users()
        self.page.update()
    
    async def handle_typing_update(self, data):
        # data: {'type': 'typing', 'users': [...]}
        # Show typing indicator in input area
        typing_users = set(data.get('users', []))
        
        # Only update if typing status has changed
        if typing_users != self.typing_users:
            self.typing_users = typing_users
            # Only update UI if we're in a chat
            if self.chat_with:
                # Only update UI if we're chatting with someone who's typing
                if self.chat_with in self.typing_users:
                    # Find the typing indicator container
                    for control in self.chat_screen.controls:
                        if isinstance(control, ft.Container) and control.expand:
                            for col_control in control.content.controls:
                                if isinstance(col_control, ft.Container) and col_control.key == "typing_indicator":
                                    col_control.visible = True
                                    self.page.update()
                                    return
                else:
                    # Hide typing indicator if user stopped typing
                    for control in self.chat_screen.controls:
                        if isinstance(control, ft.Container) and control.expand:
                            for col_control in control.content.controls:
                                if isinstance(col_control, ft.Container) and col_control.key == "typing_indicator":
                                    col_control.visible = False
                                    self.page.update()
                                    return
    
    def show_login_screen(self):
        self.page.controls.clear()
        self.page.add(self.login_screen)
    
    def show_chat_screen(self):
        self.page.controls.clear()
        self.page.add(self.chat_screen)
        self.update_users()
    
    @property
    def page(self):
        # Get the page from any control
        return self.login_screen.page or self.chat_screen.page

    def download_file(self, file_name, file_data=None):
        # Use FilePicker to save a dummy file with the same name
        def on_save(e):
            if e.path:
                save_dir = os.path.dirname(e.path)
                # Determine save path (preserve filename)
                target_path = e.path
                if os.path.basename(target_path) != file_name:
                    target_path = os.path.join(save_dir, file_name)
                # Write actual content or dummy fallback
                if file_data:
                    try:
                        content = base64.b64decode(file_data)
                        with open(target_path, 'wb') as f:
                            f.write(content)
                    except Exception as ex:
                        print(f"Error saving file: {ex}")
                        return
                else:
                    with open(target_path, 'w', encoding='utf-8') as f:
                        f.write(f"This is a dummy file for {file_name}\n")
                # Remove original if renamed
                if target_path != e.path and os.path.exists(e.path):
                    try:
                        os.remove(e.path)
                    except:
                        pass
        # Create file picker
        picker = ft.FilePicker(on_result=on_save)
        # Add picker to overlay if not already present
        if picker not in self.page.overlay:
            self.page.overlay.append(picker)
        # Push overlay change and invoke save dialog with correct default filename
        self.page.update()
        # Open save dialog and suggest the correct filename
        picker.save_file(file_name=file_name)

    def send_message(self, recipient, content):
        if self.comm_client and self.comm_loop:
            asyncio.run_coroutine_threadsafe(
                self.comm_client.send_message(recipient, content),
                self.comm_loop
            )

    def set_typing(self, is_typing):
        if self.comm_client and self.comm_loop and self.chat_with:
            # Send typing status immediately
            asyncio.run_coroutine_threadsafe(
                self.comm_client.send_typing(is_typing),
                self.comm_loop
            )
            # Optionally clear typing after 3 seconds using threading.Timer
            if is_typing:
                # Cancel previous timer if exists
                if hasattr(self, 'typing_timeout') and isinstance(self.typing_timeout, threading.Timer):
                    try:
                        self.typing_timeout.cancel()
                    except:
                        pass
                # Schedule to clear typing status
                timer = threading.Timer(3, lambda: asyncio.run_coroutine_threadsafe(
                    self.comm_client.send_typing(False), self.comm_loop))
                timer.daemon = True
                timer.start()
                self.typing_timeout = timer

    def on_chat_scroll(self, e):
        """Track scroll position to restore it after updates"""
        self.chat_scroll_pos = e.pixels

    def restore_scroll_position(self, current_scroll):
        """Restore chat scroll position directly"""
        if hasattr(self, 'chat_view'):
            self.chat_view.auto_scroll = False
            self.chat_view.scroll_to(current_scroll)

    def play_notification(self):
        """Play notification sound if file exists"""
        try:
            import os
            if os.name == 'nt':  # Windows
                import winsound
                winsound.PlaySound("notification.wav", winsound.SND_ASYNC)
            elif os.name == 'posix':  # macOS/Linux
                os.system('afplay notification.wav &')
        except Exception as e:
            print(f"Error playing notification sound: {e}")

if __name__ == "__main__":
    app = OfficeMessenger()
    ft.app(target=app.main) 