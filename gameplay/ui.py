import math
import tkinter as tk
from tkinter import messagebox
from ui_elements.button_menu import ButtonMenu
from ui_elements.capacity_meter import CapacityMeter
from ui_elements.clock import Clock
from endpoints.heuristic_interface import HeuristicInterface
from ui_elements.game_viewer import GameViewer
from ui_elements.machine_menu import MachineMenu
from ui_elements.meters import MetersPanel
from os.path import join
import threading
import platform
import numpy as np
import io
import pygame
from endpoints.groq_helper import get_round_summary
from endpoints.data_parser import datarow_to_state
from gameplay.start_screen import StartScreen
from gameplay.launch_screen import LaunchScreen
from PIL import ImageTk, Image


class SoundManager:
    """Manages sound effects for the game"""
    
    def __init__(self):
        # Initialize pygame mixer
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        
        # Load sound effects from MP3 files
        try:
            self.sounds = {
                'squish': pygame.mixer.Sound('ui_elements/sfx/squish.mp3'),
                'scram': pygame.mixer.Sound('ui_elements/sfx/scram.mp3'),
                'save': pygame.mixer.Sound('ui_elements/sfx/save.mp3'),
                'skip': pygame.mixer.Sound('ui_elements/sfx/skip.mp3')
            }
        except Exception as e:
            print(f"Error loading sound effects: {e}")
            self.sounds = {}
    
    def play_sound(self, action):
        """Play sound effect for the given action"""
        try:
            if action in self.sounds:
                self.sounds[action].play()
        except Exception as e:
            print(f"Error playing sound for {action}: {e}")


class UI(object):
    def __init__(self, data_parser, scorekeeper, data_fp, suggest, log):
        self.data_parser = data_parser
        self.scorekeeper = scorekeeper
        self.data_fp = data_fp
        self.log = log
        self.round_actions = {'skip': 0, 'squish': 0, 'save': 0, 'scram': 0}
        self.all_game_events = []  # Track all events across the entire game
        w, h = 1280, 800
        capacity = 12
        self.root = tk.Tk()
        self.root.title("Beaverworks SGAI 2025 - Dead or Alive")
        self.root.geometry(str(w) + 'x' + str(h))
        self.root.resizable(False, False)
        
        # Initialize sound manager
        self.sound_manager = SoundManager()
        
        self.launch_screen = LaunchScreen(self.root, self._on_launch_continue)
        self.root.mainloop()
        self.final_meter_values = None
        self.initial_meter_values = None

    def _on_launch_continue(self):
        """Called when user clicks continue on launch screen"""
        self.launch_screen.canvas.destroy()
        self.start_screen = StartScreen(self.root, self._on_start_game)

    def _on_start_game(self, timestamp=None, operator_name="", player_name=""):
        # Update the scorekeeper's timestamp if provided
        if timestamp:
            self.scorekeeper.game_start_timestamp = timestamp
        
        # Store operator and player names
        self.operator_name = operator_name
        self.player_name = player_name
        
        # Update the scorekeeper with the names
        self.scorekeeper.operator_name = operator_name
        self.scorekeeper.player_name = player_name
        
        self.init_main_ui()

    def init_main_ui(self):
        w, h = 1280, 800
        capacity = 12
        suggest = False
        self.humanoid = self.data_parser.get_random()
        if suggest:
            self.machine_interface = HeuristicInterface(self.root, w, h)
        self.round_states = {}
        self.round_roles = {}
        self.round_images = []
        self.game_number = 1
        self.round_number = 1
        user_buttons = [
            ("Skip", lambda: [self.sound_manager.play_sound('skip'), self.increment_action('skip'), self.scorekeeper.log(self.humanoid, 'skip', self.game_number, self.round_number), self.scorekeeper.skip(self.humanoid), self.update_ui(self.scorekeeper), self.get_next(self.data_fp, self.data_parser, self.scorekeeper)]),
            ("Squish", lambda: [self.sound_manager.play_sound('squish'), self.increment_action('squish'), self.scorekeeper.log(self.humanoid, 'squish', self.game_number, self.round_number), self.scorekeeper.squish(self.humanoid), self.update_ui(self.scorekeeper), self.get_next(self.data_fp, self.data_parser, self.scorekeeper)]),
            ("Save", lambda: [self.sound_manager.play_sound('save'), self.increment_action('save'), self.scorekeeper.log(self.humanoid, 'save', self.game_number, self.round_number), self.scorekeeper.save(self.humanoid), self.update_ui(self.scorekeeper), self.get_next(self.data_fp, self.data_parser, self.scorekeeper)]),
            ("Scram", lambda: [self.sound_manager.play_sound('scram'), self.increment_action('scram'), self.scorekeeper.log(self.humanoid, 'scram', self.game_number, self.round_number), self.scorekeeper.scram(self.humanoid), self.update_ui(self.scorekeeper), self.get_next(self.data_fp, self.data_parser, self.scorekeeper)]),
            ("End Round", self.end_round),
            ("End Game", lambda: self.end_game())
        ]
        # Create background canvas first and ensure it's at the bottom
        self._create_background_canvas()
        
        # Add logo to the main screen
        self._add_logo()
        
        # Create button menu after background to ensure it appears on top
        self.button_menu = ButtonMenu(self.root, user_buttons)
        if suggest:
            machine_buttons = [
                ("Suggest", lambda: [self.machine_interface.suggest(self.humanoid)]),
                ("Act", lambda: [self.machine_interface.act(self.scorekeeper, self.humanoid), self.update_ui(self.scorekeeper), self.get_next(self.data_fp, self.data_parser, self.scorekeeper)])
            ]
            self.machine_menu = MachineMenu(self.root, machine_buttons)
        
        info_text = self._get_info_text(self.humanoid)
        self.game_viewer = GameViewer(self.root, w, h, self.humanoid, info_text=info_text)
        self.root.bind("<Delete>", self.game_viewer.delete_photo)
        # Calculate initial time display based on remaining_time
        init_h = int(self.scorekeeper.remaining_time // 60)
        init_m = int(self.scorekeeper.remaining_time % 60)
        self.clock = Clock(self.root, w, h, init_h, init_m)
        right_panel_width = math.floor(0.20 * w)
        cap_height = 200
        meters_height = 300  # Increased from 180 to 300 to accommodate larger labels and vertical layout
        right_x = w - right_panel_width - 4
        cap_y = 140
        meters_y = cap_y + cap_height + 20
        self.capacity_meter = CapacityMeter(self.root, w, h, capacity, width=right_panel_width, height=cap_height, x=right_x, y=cap_y)
        self.meters_panel = MetersPanel(self.root, right_x, meters_y, width=right_panel_width, height=meters_height)
        
        # Show round time popup for the first round
        self._show_round_time_popup(1, self.scorekeeper.round_duration)
        
        self.ticking = True
        self.tick_clock(self.scorekeeper)
        self.initial_meter_values = [
            self.scorekeeper.military,
            self.scorekeeper.hra,
            self.scorekeeper.scientist,
            self.scorekeeper.medic
        ]

    def update_meters(self, scorekeeper, data_parser):
        military_val = scorekeeper.get_military_meter()
        self.meters_panel.update_meter(0, military_val, 1000)
        hra_val = scorekeeper.get_hra_meter()
        self.meters_panel.update_meter(1, hra_val, 1000)
        scientist_val = scorekeeper.get_scientist_meter()
        self.meters_panel.update_meter(2, scientist_val, 1000)
        medic_val = scorekeeper.get_medic_meter()
        self.meters_panel.update_meter(3, medic_val, 1000)

    def tick_clock(self, scorekeeper):
        if scorekeeper.remaining_time > 0 and self.ticking:
            scorekeeper.remaining_time = max(0, scorekeeper.remaining_time - 1)
            self.update_clock_display(scorekeeper)
            self.update_meters(scorekeeper, self.data_parser)
            self.root.after(1000, lambda: self.tick_clock(scorekeeper))
        elif scorekeeper.remaining_time <= 0:
            self.update_clock_display(scorekeeper)
            self.update_meters(scorekeeper, self.data_parser)
            self.ticking = False
            self.show_round_over()

    def update_clock_display(self, scorekeeper):
        h = max(0, int(scorekeeper.remaining_time // 60))
        m = max(0, int(scorekeeper.remaining_time % 60))
        self.clock.update_time(h, m)

    def update_ui(self, scorekeeper):     
        h = max(0, int(scorekeeper.remaining_time // 60))
        m = max(0, int(scorekeeper.remaining_time % 60))
        self.clock.update_time(h, m)
        self.capacity_meter.update_fill(scorekeeper.get_current_capacity()) 
        self.update_meters(scorekeeper, self.data_parser)
        remaining = len(self.data_parser.unvisited)
        self.button_menu.disable_buttons(scorekeeper.remaining_time, remaining, scorekeeper.at_capacity())

    def on_resize(self, event):
        w, h = 0.6 * self.root.winfo_width(), 0.7 * self.root.winfo_height()
        self.game_viewer.canvas.config(width=w, height=h)

    def get_next(self, data_fp, data_parser, scorekeeper):
        remaining = len(data_parser.unvisited)
        if remaining == 0 or scorekeeper.remaining_time <= 0:
            if self.log:
                scorekeeper.save_log()
            self.capacity_meter.update_fill(0)
            self.game_viewer.delete_photo(None)
            
            # Capture final meter values before they might get reset
            final_meter_values = [
                scorekeeper.military,
                scorekeeper.hra,
                scorekeeper.scientist,
                scorekeeper.medic
            ]
            

            # Show initial game over screen with loading message
            self.game_viewer.display_score(scorekeeper.get_score(), self.play_again, final_meter_values, "Loading mission briefing...")
            
            # Generate final game summary in background
            threading.Thread(target=self._fetch_and_update_final_summary, daemon=True).start()

        else:
            humanoid = data_parser.get_random()
            self.humanoid = humanoid
            info_text = self._get_info_text(self.humanoid)
            self.game_viewer.create_photo(self.humanoid.fp, info_text=info_text)
        self.button_menu.disable_buttons(scorekeeper.remaining_time, remaining, scorekeeper.at_capacity())

    def end_round(self):
        self.scorekeeper.remaining_time = 1

    def end_game(self):
        result = messagebox.askyesno("End Game", "Are you sure you want to end the game?")
        if result:
            # Capture final meter values before they get reset
            final_meter_values = [
                self.scorekeeper.military,
                self.scorekeeper.hra,
                self.scorekeeper.scientist,
                self.scorekeeper.medic
            ]
            
            final_score = self.scorekeeper.end_game()
            self.show_final_score(final_score, final_meter_values)

    def show_final_score(self, final_score=None, final_meter_values=None):
        if self.log:
            self.scorekeeper.save_log()
        self.ticking = False
        self.button_menu.canvas.place_forget()
        if hasattr(self, 'machine_menu'):
            self.machine_menu.canvas.place_forget()
        self.clock.canvas.place_forget()
        self.capacity_meter.canvas.place_forget()
        self.meters_panel.hide()
        self.game_viewer.delete_photo(None)
        score_to_display = final_score or self.scorekeeper.get_score()
        
        # Store final meter values as instance variable to persist through summary updates
        self.final_meter_values = final_meter_values or [
            self.scorekeeper.military,
            self.scorekeeper.hra,
            self.scorekeeper.scientist,
            self.scorekeeper.medic
        ]
        
        # Show initial game over screen with loading message
        self.game_viewer.display_score(score_to_display, self.play_again, self.final_meter_values, "Loading mission briefing...")

        
        # Generate final game summary in background
        threading.Thread(target=self._fetch_and_update_final_summary, daemon=True).start()

    def show_round_over(self):
        self.ticking = False
        self.button_menu.canvas.place_forget()
        if hasattr(self, 'machine_menu'):
            self.machine_menu.canvas.place_forget()
        self.clock.canvas.place_forget()
        self.capacity_meter.canvas.place_forget()
        self.meters_panel.hide()
        self.game_viewer.delete_photo(None)
        self.final_meter_values = [
            self.scorekeeper.military,
            self.scorekeeper.hra,
            self.scorekeeper.scientist,
            self.scorekeeper.medic
        ]
        self._round_summary_text = None

        # --- NEW: expanded panel size and pass meter values ---
        self.game_viewer.display_round_over_with_summary(
            self.scorekeeper.get_round_score(),
            self.next_round,
            summary_text="Loading summary...",
            summary_label_ref_callback=self._set_round_summary_label,
            round_images=self.round_images,
            initial_meter_values=self.initial_meter_values,
            final_meter_values=self.final_meter_values
        )
        threading.Thread(target=self._fetch_and_update_round_summary, daemon=True).start()

    def _set_round_summary_label(self, label):
        self._round_summary_text = label

    def _fetch_and_update_round_summary(self):
        summary = get_round_summary(self.round_actions, self.round_states, self.round_roles, self.round_images, self.scorekeeper.get_round_score())

        def update_ui_with_summary():
            # --- NEW: pass meter values again ---
            self.game_viewer.display_round_over_with_summary(
                self.scorekeeper.get_round_score(),
                self.next_round,
                summary_text=summary,
                summary_label_ref_callback=self._set_round_summary_label,
                round_images=self.round_images,
                initial_meter_values=self.initial_meter_values,
                final_meter_values=self.final_meter_values
            )
        self.root.after(0, update_ui_with_summary)

    def _fetch_and_update_final_summary(self):
        """Fetch the final game summary from GROQ and update the display"""
        from endpoints.groq_helper import get_final_game_summary
        
        # Get the final game statistics
        final_score = self.scorekeeper.get_score()
        total_rounds = self.round_number
        

        # Aggregate all round data for comprehensive statistics
        all_round_actions = {'skip': 0, 'squish': 0, 'save': 0, 'scram': 0}
        all_round_states = {}
        all_round_roles = {}
        
        # Aggregate data from all game events
        for img_fp, action, state, role, round_num in self.all_game_events:
            all_round_actions[action] = all_round_actions.get(action, 0) + 1
            if state:
                all_round_states[state] = all_round_states.get(state, 0) + 1
            if role:
                all_round_roles[role] = all_round_roles.get(role, 0) + 1
        
        # Generate the final summary
        final_summary = get_final_game_summary(final_score, total_rounds, self.all_game_events, all_round_actions, all_round_states, all_round_roles)
        
        def update_ui_with_final_summary():
            # Use the stored final meter values instead of getting them from scorekeeper
            self.game_viewer.display_score(
                self.scorekeeper.get_score(), 
                self.play_again, 
                self.final_meter_values, 
                final_summary
            )
        
        self.root.after(0, update_ui_with_final_summary)


    def increment_action(self, action):
        if action in self.round_actions:
            self.round_actions[action] += 1
        state = self.humanoid.state.get('parent', '') if hasattr(self.humanoid, 'state') else ''
        role = self.humanoid.state.get('role', '') if hasattr(self.humanoid, 'state') else ''
        if state:
            self.round_states[state] = self.round_states.get(state, 0) + 1
        if role:
            self.round_roles[role] = self.round_roles.get(role, 0) + 1
        self.round_images.append((self.humanoid.fp, action, state, role))
        
        # Track game event with round number
        self.all_game_events.append((self.humanoid.fp, action, state, role, self.round_number))

    def next_round(self):
        if self.scorekeeper.next_round():
            # Clear the game viewer first to remove the round over screen
            self.game_viewer.canvas.delete("all")
            for widget in self.game_viewer.canvas.winfo_children():
                widget.destroy()
            
            # Resize the game viewer back to normal size
            self.game_viewer.resize_to_normal()
            
            self.initial_meter_values = [
                self.scorekeeper.military,
                self.scorekeeper.hra,
                self.scorekeeper.scientist,
                self.scorekeeper.medic
            ]
            self.data_parser.reset()
            self.scorekeeper.reset()
            
            self.round_actions = {k: 0 for k in self.round_actions}
            self.round_states = {}
            self.round_roles = {}
            self.round_images = []
            if hasattr(self.game_viewer, 'meters_canvas') and self.game_viewer.meters_canvas.winfo_exists():
                self.game_viewer.meters_canvas.destroy()
            for widget in self.game_viewer.canvas.winfo_children():
                widget.destroy()
            self.game_viewer.canvas.delete("all")
            self.humanoid = self.data_parser.get_random()
            self.game_viewer.canvas.delete("all")
            
            # Re-add background image first
            self._add_background_image()
            
            # Re-add logo
            self._add_logo()
            
            # Then reposition UI elements BEFORE showing popup
            self.button_menu.canvas.place(x=0, y=150)
            if hasattr(self, 'machine_menu'):
                self.machine_menu.canvas.place(x=450, y=720)
            w, h = 1280, 800
            clock_width = math.floor(0.4 * w)
            self.clock.canvas.place(x=(w - clock_width) // 2, y=20)
            right_panel_width = math.floor(0.20 * w)
            cap_height = 200
            meters_height = 300  # Increased from 180 to 300 to accommodate larger labels and vertical layout
            right_x = w - right_panel_width - 4
            cap_y = 140  # Match the initial positioning from init_main_ui
            meters_y = cap_y + cap_height + 20  # Match the initial positioning from init_main_ui
            self.capacity_meter.canvas.place(x=right_x, y=cap_y, width=right_panel_width, height=cap_height)
            self.meters_panel.show(right_x, meters_y)
            self.capacity_meter.update_fill(0)
            # Update clock with the new round's time
            init_h = int(self.scorekeeper.remaining_time // 60)
            init_m = int(self.scorekeeper.remaining_time % 60)
            self.clock.update_time(init_h, init_m)
            info_text = self._get_info_text(self.humanoid)
            self.game_viewer.create_photo(self.humanoid.fp, info_text=info_text)
            
            # Show round time popup AFTER UI components are restored
            self._show_round_time_popup(self.round_number + 1, self.scorekeeper.round_duration)
            
            self.ticking = True
            self.tick_clock(self.scorekeeper)
            self.round_number += 1
            self.update_ui(self.scorekeeper)
        else:
            self.show_final_score()

    def play_again(self):
        # Clear the game viewer first to remove the final score screen
        self.game_viewer.canvas.delete("all")
        for widget in self.game_viewer.canvas.winfo_children():
            widget.destroy()
        
        # Resize the game viewer back to normal size
        self.game_viewer.resize_to_normal()
        
        # Mark that a game has been played (for round duration tracking)
        self.scorekeeper.mark_game_played()
        
        # Reset meters AFTER the button is pressed (not before displaying game over screen)
        self.scorekeeper.reset_meters()
        
        self.scorekeeper.reset()
        self.data_parser.reset()
        
        # Update initial meter values after resetting meters
        self.initial_meter_values = [
            self.scorekeeper.military,
            self.scorekeeper.hra,
            self.scorekeeper.scientist,
            self.scorekeeper.medic
        ]

        self.round_actions = {k: 0 for k in self.round_actions}
        self.round_states = {}
        self.round_roles = {}
        self.round_images = []
        self.scorekeeper.current_round = 1
        self.humanoid = self.data_parser.get_random()
        
        # Re-add background image first
        self._add_background_image()
        
        # Re-add logo
        self._add_logo()
        
        # Then reposition UI elements BEFORE showing popup
        self.button_menu.canvas.place(x=0, y=150)
        if hasattr(self, 'machine_menu'):
            self.machine_menu.canvas.place(x=450, y=720)
        w, h = 1280, 800
        clock_width = math.floor(0.4 * w)
        self.clock.canvas.place(x=(w - clock_width) // 2, y=20)
        right_panel_width = math.floor(0.20 * w)
        cap_height = 200
        meters_height = 300  # Increased from 180 to 300 to accommodate larger labels and vertical layout
        right_x = w - right_panel_width - 4
        cap_y = 140  # Match the initial positioning from init_main_ui
        meters_y = cap_y + cap_height + 20  # Match the initial positioning from init_main_ui
        self.capacity_meter.canvas.place(x=right_x, y=cap_y, width=right_panel_width, height=cap_height)
        self.meters_panel.show(right_x, meters_y)
        self.capacity_meter.update_fill(0)
        # Update clock with the new game's time (first round is always 120 seconds)
        init_h = int(self.scorekeeper.remaining_time // 60)
        init_m = int(self.scorekeeper.remaining_time % 60)
        self.clock.update_time(init_h, init_m)
        info_text = self._get_info_text(self.humanoid)
        self.game_viewer.create_photo(self.humanoid.fp, info_text=info_text)
        
        # Show round time popup AFTER UI components are restored
        self._show_round_time_popup(1, self.scorekeeper.round_duration)
        
        self.ticking = True
        self.tick_clock(self.scorekeeper)
        self.game_number += 1
        self.round_number = 1
        self.update_ui(self.scorekeeper)

    def _create_background_canvas(self):
        """Create the background canvas first to ensure proper layering"""
        try:
            # Remove existing background canvas if it exists
            if hasattr(self, 'background_canvas') and self.background_canvas.winfo_exists():
                self.background_canvas.destroy()
            
            # Create a background canvas that covers the entire window
            self.background_canvas = tk.Canvas(
                self.root, 
                width=1280, 
                height=800, 
                highlightthickness=0,
                bg='black'  # Set background color in case image fails to load
            )
            
            # Place the background canvas first to ensure it's at the bottom
            self.background_canvas.place(x=0, y=0)
            
            # Load and add the background image
            self._add_background_image()
            
        except Exception as e:
            print(f"Error creating background canvas: {e}")
            import traceback
            traceback.print_exc()

    def _add_background_image(self):
        """Add the full ambulance dashboard as a background image for the main game screen"""
        try:
            # Load the full ambulance dashboard image
            image_path = "ui_elements/graphics/ambulancedashbottom6.png"
            img = Image.open(image_path)
            
            # Get window dimensions
            window_width = 1280
            window_height = 800
            
            # Resize the image to fit the entire window
            resized_img = img.resize((window_width, window_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self.background_photo = ImageTk.PhotoImage(resized_img)
            
            # Clear the existing canvas and add the background image
            self.background_canvas.delete("all")
            self.background_canvas.create_image(0, 0, anchor=tk.NW, image=self.background_photo)
            
        except Exception as e:
            print(f"Error loading background image: {e}")
            import traceback
            traceback.print_exc()

    def _add_logo(self):
        """Add the logo image to the main screen at specified coordinates"""
        try:
            # Load the logo image
            image_path = "ui_elements/graphics/logo5trans.png"
            img = Image.open(image_path)
            
            # Resize the logo to match logo3 dimensions
            logo_width = 300
            logo_height = 50
            resized_img = img.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
            
            # Apply 80% opacity by creating a new image with alpha channel
            if resized_img.mode != 'RGBA':
                resized_img = resized_img.convert('RGBA')
            
            # Create a new image with 80% opacity
            rgba = resized_img.split()
            alpha = rgba[3].point(lambda x: int(x * 0.8))  # 80% opacity
            img_with_opacity = Image.merge('RGBA', rgba[:3] + (alpha,))
            
            # Convert to PhotoImage
            self.logo_photo = ImageTk.PhotoImage(img_with_opacity)
            
            # Add the logo to the background canvas at the specified coordinates
            self.background_canvas.create_image(950, 30, anchor=tk.NW, image=self.logo_photo)
            
        except Exception as e:
            print(f"Error loading logo image: {e}")
            import traceback
            traceback.print_exc()

    def _show_round_time_popup(self, round_number, duration_seconds):
        """Show a popup informing the player of the round duration"""
        # Create a custom popup window
        popup = tk.Toplevel(self.root)
        popup.title("Round Information")
        popup.geometry("400x200")
        popup.resizable(False, False)
        popup.configure(bg='#000000')  # Set popup background to black
        
        # Center the popup on the screen
        popup.transient(self.root)
        popup.grab_set()
        
        # Calculate minutes and seconds for display
        minutes = duration_seconds // 60
        seconds = duration_seconds % 60
        
        # Create the message
        if minutes > 0:
            time_text = f"{minutes} minute{'s' if minutes != 1 else ''} and {seconds} second{'s' if seconds != 1 else ''}"
        else:
            time_text = f"{seconds} second{'s' if seconds != 1 else ''}"
        
        # Create and pack widgets
        title_label = tk.Label(popup, text=f"Round {round_number}", font=("Courier New", 18, "bold"), fg="#00ff00", bg="#000000")
        title_label.pack(pady=(20, 10))
        
        message_label = tk.Label(popup, text=f"You have {time_text}\nfor this round.", 
                               font=("Courier New", 14), fg="#00ff00", bg="#000000", justify=tk.CENTER)
        message_label.pack(pady=10)
        
        # Use tkmacosx button on macOS for better styling
        if platform.system() == "Darwin":
            try:
                from tkmacosx import Button as MacButton
                ButtonClass = MacButton
            except ImportError:
                ButtonClass = tk.Button
        else:
            ButtonClass = tk.Button
        
        # Confirm button
        confirm_button = ButtonClass(popup, text="Confirm", command=popup.destroy,
                                   font=("Courier New", 12, "bold"), bg="#000000", fg="#00ff00",
                                   relief=tk.RAISED, bd=3, padx=20, pady=5, 
                                   bordercolor="#00ff00", highlightcolor="#00ff00",
                                   activebackground="#111111", activeforeground="#00ff00")
        confirm_button.pack(pady=20)
        
        # Center the popup on the main window
        popup.update_idletasks()
        x = (self.root.winfo_width() // 2) - (popup.winfo_width() // 2)
        y = (self.root.winfo_height() // 2) - (popup.winfo_height() // 2)
        popup.geometry(f"+{x}+{y}")
        
        # Wait for the popup to be closed
        self.root.wait_window(popup)

    def _get_info_text(self, humanoid):
        role = ''
        if hasattr(humanoid, 'state') and humanoid.state:
            role = humanoid.state.get('role', '')
        elif hasattr(humanoid, 'fp'):
            parent_folder = humanoid.fp.split('/')[-2] if '/' in humanoid.fp else ''
            info = datarow_to_state(humanoid.fp.split('/')[-1], parent_folder)
            role = info.get('role', '')
        desc = f"{role.capitalize()}"

        return desc