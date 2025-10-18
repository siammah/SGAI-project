import math
import tkinter as tk
import platform

import tkinter.font as tkfont

from os.path import join
from PIL import ImageTk, Image
import threading
from endpoints.groq_helper import get_image_caption_groq


# Adjustable summary image dimensions
SUMMARY_IMG_WIDTH = 250
SUMMARY_IMG_HEIGHT = 170


def get_button_class():
    """Get the appropriate button class based on platform"""
    if platform.system() == "Darwin":
        try:
            from tkmacosx import Button as MacButton
            return MacButton
        except ImportError:
            return tk.Button
    else:
        return tk.Button


class GameViewer(object):
    def __init__(self, root, w, h, humanoid, info_text=None):
        self.root = root
        self.w = w
        self.h = h
        self.frame_width = math.floor(0.6 * w)
        self.frame_height = math.floor(0.7 * h)
        self.canvas = tk.Canvas(root, width=self.frame_width, height=self.frame_height, bg='#000000', highlightthickness=0)
        self.canvas.place(x=250, y=120)
        self.canvas.update()
        self.original_width = self.frame_width
        self.original_height = self.frame_height
        self.original_x = 250
        self.original_y = 120
        self.photo = None
        self.info_text_id = None
        self.info_text_content = ""
        self.create_photo(humanoid.fp, info_text=info_text)

    def resize_for_round_over(self):
        """Resize the game viewer to be significantly larger for the round over screen"""
        # Make it larger but not quite as large - about 80% of screen
        new_width = math.floor(1 * self.w)
        new_height = math.floor(1 * self.h)
        new_x = (self.w - new_width) // 2
        new_y = (self.h - new_height) // 2
        
        self.canvas.config(width=new_width, height=new_height)
        self.canvas.place(x=new_x, y=new_y)
        self.canvas.update()

    def resize_to_normal(self):
        """Resize the game viewer back to its normal size"""
        self.canvas.config(width=self.original_width, height=self.original_height)
        self.canvas.place(x=self.original_x, y=self.original_y)
        self.canvas.update()

    def delete_photo(self, event=None):
        self.canvas.delete('photo')

    def create_photo(self, fp, info_text=None):
        self.canvas.delete("all")
        for widget in self.canvas.winfo_children():
            widget.destroy()
        self._draw_windshield_frame()
        frame_padding = 20
        # Remove inner padding to make sides flush with image
        inner_x = frame_padding
        inner_y = frame_padding
        inner_width = self.frame_width - 2 * frame_padding
        # Remove the -40 to eliminate bottom dashboard area
        inner_height = self.frame_height - 2 * frame_padding
        self.photo = display_photo(fp, inner_width, inner_height)
        self.canvas.create_image(inner_x, inner_y, anchor=tk.NW, image=self.photo, tags='photo')
        if info_text is None:
            info_text = ""
        # Position text at top middle of the image
        text_x = inner_x + inner_width // 2  # Center horizontally
        text_y = inner_y + 10  # 10px from top edge
        self.info_text_id = self.canvas.create_text(
            text_x, text_y,
            text=info_text,
            fill="#00ff00",
            font=("Courier New", 32, "bold"),
            anchor="n"  # Anchor to north (top center)
        )
        self.info_text_content = info_text

    def update_info_text(self, info_text):
        if self.info_text_id is not None:
            self.canvas.itemconfig(self.info_text_id, text=info_text)
            self.info_text_content = info_text

    def _draw_windshield_frame(self):
        frame_padding = 20
        frame_x = frame_padding
        frame_y = frame_padding
        frame_width = self.frame_width - 2 * frame_padding
        frame_height = self.frame_height - 2 * frame_padding
        # Draw the main frame rectangle (this will be flush with the image)
        self.canvas.create_rectangle(frame_x, frame_y, frame_x + frame_width, frame_y + frame_height, 
                                   fill='#000000', outline='#00ff00', width=3)
        # Add a wiper line near the top
        wiper_y = frame_y + 30
        self.canvas.create_line(frame_x + 50, wiper_y, frame_x + frame_width - 50, wiper_y, 
                              fill='#00ff00', width=1, dash=(5, 10))

    def display_score(self, score, play_again_callback=None, final_meter_values=None, groq_summary="Loading mission briefing..."):
        self.canvas.delete("all")
        
        # Resize canvas for game over screen
        self.resize_for_round_over()
        
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        
        # Commander's Report Header
        header_y = 60
        self.canvas.create_text(canvas_w // 2, header_y, text="MISSION REPORT", font=("Courier New", 32, "bold"), fill="#00ff00")
        self.canvas.create_text(canvas_w // 2, header_y + 40, text="AMBULANCE OPERATION COMPLETE", font=("Courier New", 18), fill="#00ff00")
        

        # Calculate column widths
        left_column_width = canvas_w // 3
        right_column_width = canvas_w - left_column_width
        
        # LEFT COLUMN (1/3 width) - Mission Statistics and Performance Assessment
        left_x = 50
        left_y = 160
        
        # Mission Statistics Section
        self.canvas.create_text(left_x + left_column_width // 2, left_y, text="MISSION STATISTICS", font=("Courier New", 24, "bold"), fill="#00ff00")
        
        # Create a military-style report format
        report_lines = [
            f"CASUALTIES PREVENTED: {score.get('humans_saved', 0)}",
            f"FRIENDLY FIRE INCIDENTS: {score.get('humans_killed', 0)}",
            f"ZOMBIES SAVED: {score.get('zombies_saved', 0)}",
            f"ZOMBIE ELIMINATIONS: {score.get('zombies_killed', 0)}",
            f"CORPSES ENCOUNTERED: {score.get('corpses_encountered', 0)}"
        ]
        
        # Display statistics in military format
        for i, line in enumerate(report_lines):
            y_pos = left_y + 50 + (i * 35)
            color = "#00ff00" if "PREVENTED" in line or "ELIMINATIONS" in line else "#ff0000" if "FIRE" in line else "#ffff00"
            self.canvas.create_text(left_x + left_column_width // 2, y_pos, text=line, font=("Courier New", 16, "bold"), fill=color)
        
        # Performance Assessment Section
        assessment_y = left_y + 250
        self.canvas.create_text(left_x + left_column_width // 2, assessment_y, text="PERFORMANCE ASSESSMENT", font=("Courier New", 20, "bold"), fill="#00ff00")

        
        # Calculate performance rating
        humans_saved = score.get('humans_saved', 0)
        humans_killed = score.get('humans_killed', 0)
        zombies_saved = score.get('zombies_saved', 0)
        zombies_killed = score.get('zombies_killed', 0)
        

        # Advanced performance calculation considering both humans and zombies
        human_margin = humans_saved - humans_killed
        zombie_margin = zombies_killed - zombies_saved
        
        if human_margin >= 5 and zombie_margin >= 5:
            performance = "EXCELLENT - OUTSTANDING PERFORMANCE"
            perf_color = "#27ae60"
        elif human_margin > 0 and zombie_margin > 0:
            performance = "GOOD - POSITIVE RESCUE AND ELIMINATION RATIOS"
            perf_color = "#f39c12"
        elif (human_margin > 0 and zombie_margin <= 0) or (human_margin <= 0 and zombie_margin > 0):
            performance = "MEDIOCRE - MIXED RESULTS"
            perf_color = "#e67e22"
        elif humans_saved > 0 or zombies_killed > 0:
            performance = "POOR - LIMITED SUCCESS"
            perf_color = "#e74c3c"
        else:
            performance = "CRITICAL - NO POSITIVE ACTIVITY"
            perf_color = "#c0392b"
        self.canvas.create_text(left_x + left_column_width // 2, assessment_y + 40, text=performance, font=("Courier New", 12, "bold"), fill=perf_color)
        
        # RIGHT COLUMN (2/3 width) - Intelligence Report
        right_x = left_x + left_column_width -50
        intel_y = 160
        
        # Intelligence Report Section (GROQ Summary)
        self.canvas.create_text(right_x + right_column_width // 2, intel_y, text="INTELLIGENCE REPORT", font=("Courier New", 24, "bold"), fill="#00ff00")
        

        # Parse the GROQ summary for better formatting
        if groq_summary and groq_summary != "Loading mission briefing...":
            # Try to extract headline and content from GROQ response
            lines = groq_summary.split('\n')
            headline = None
            content = groq_summary
            
            for i, line in enumerate(lines):
                if line.strip().startswith('# '):
                    headline = line.strip()[2:].strip()
                    content_lines = [l for l in lines[i+1:] if l.strip()]
                    content = '\n'.join(content_lines)
                    break
            
            # Display headline if found
            if headline:

                self.canvas.create_text(right_x + right_column_width // 2, intel_y + 60, text=headline, font=("Courier New", 18, "bold"), fill="#ffff00", anchor="center", width=right_column_width - 100)
                self.canvas.create_text(right_x + right_column_width // 2, intel_y + 170, text=content, font=("Courier New", 13), fill="#ffff00", anchor="center", width=right_column_width - 100)
            else:
                self.canvas.create_text(right_x + right_column_width // 2, intel_y + 40, text=groq_summary, font=("Courier New", 16), fill="#ffff00", anchor="center", width=right_column_width - 100)
        else:
            self.canvas.create_text(right_x + right_column_width // 2, intel_y + 40, text=groq_summary, font=("Courier New", 16), fill="#ffff00", anchor="center", width=right_column_width - 100)
        
        # METERS SECTION - Full width below all other components
        if final_meter_values:
            # Calculate meters position (below all other content)
            meters_start_y = intel_y + 310  # Adjust based on intelligence report height
            meters_y = meters_start_y + 10
            
            self.canvas.create_text(canvas_w // 2, meters_start_y, text="REPUTATION STATUS", font=("Courier New", 20, "bold"), fill="#00ff00")
            
            meter_labels = ["MILITARY", "HRA", "SCIENCE", "MEDICAL"]
            bar_w = (canvas_w - 300) // 2 - 50  # Slightly smaller width
            bar_h = 45  # Slightly shorter height
            gap_x = 100  # Keep same horizontal gap
            gap_y = 50   # Decrease vertical gap
            
            # Calculate starting position for 2x2 grid
            meters_x = 150  # More left margin
            meters_center_y = meters_y + 50

            # Starting meter value (500)
            start_value = 500
            
            for i, label in enumerate(meter_labels):
                # Calculate grid position (2x2)
                row = i // 2
                col = i % 2
                
                x = meters_x + col * (bar_w + gap_x)
                y = meters_center_y + row * (bar_h + gap_y)
                
                # Label on top of the meter
                self.canvas.create_text(
                    x + bar_w // 2, y - 10, text=label, font=("Courier New", 14, "bold"), fill="#00ff00", anchor="s"
                )
                
                # Calculate difference from 500
                final_value = final_meter_values[i]
                difference = final_value - start_value
                difference_text = f"{difference:+d}" if difference != 0 else "0"
                
                # Value text showing the difference
                self.canvas.create_text(
                    x + bar_w + 10, y + bar_h // 2, text=difference_text, font=("Courier New", 14, "bold"), fill="#00ff00", anchor="w"
                )
                
                # Draw the meter bar with military styling
                self.canvas.create_rectangle(
                    x, y, x + bar_w, y + bar_h,
                    outline="#00ff00", fill="", width=2
                )
                
                # Fill the bar based on difference from 500
                # Show the difference as a percentage of half the bar width (since bar goes both ways from center)
                max_difference = 500  # Maximum possible difference (0 to 1000)
                half_bar_width = bar_w // 2
                difference_ratio = abs(difference) / max_difference
                fill_width = int(difference_ratio * half_bar_width)
                
                if fill_width > 0:
                    # Color based on whether it's positive or negative
                    if difference > 0:
                        fill_color = "#27ae60"  # Green for positive difference
                    else:
                        fill_color = "#e74c3c"  # Red for negative difference
                    
                    # Fill from center (500) outward
                    center_x = x + bar_w // 2
                    if difference > 0:
                        # Positive: fill from center to right
                        self.canvas.create_rectangle(
                            center_x, y, center_x + fill_width, y + bar_h,
                            fill=fill_color, outline=""
                        )
                    else:
                        # Negative: fill from center to left
                        self.canvas.create_rectangle(
                            center_x - fill_width, y, center_x, y + bar_h,
                            fill=fill_color, outline=""
                        )
                
                # Add center line to show 500 baseline
                center_x = x + bar_w // 2
                self.canvas.create_line(
                    center_x, y, center_x, y + bar_h,
                    fill="#00ff00", width=1, dash=(2, 2)
                )


        # # Mission Complete Footer
        # footer_y = canvas_h - 120
        # self.canvas.create_text(canvas_w // 2, footer_y, text="MISSION COMPLETE", font=("Courier New", 16, "bold"), fill="#00ff00")

        
        # Play Again button (styled as "NEW MISSION")
        if play_again_callback:
            ButtonClass = get_button_class()
            play_button = ButtonClass(

                self.canvas, text="New Mission", command=play_again_callback,
                font=("Courier New", 18, "bold"), bg="#000000", fg="#00ff00", relief=tk.RAISED, bd=3,
                height=60, width=200, bordercolor="#00ff00", highlightcolor="#00ff00",
                activebackground="#111111", activeforeground="#00ff00"
            )
            self.canvas.create_window(canvas_w // 2, canvas_h - 60, window=play_button)

#                 self.canvas, text="LAUNCH NEW MISSION", command=play_again_callback,
#                 font=("Courier New", 16, "bold"), bg="#000000", fg="#00ff00", relief=tk.RAISED, bd=3,
#                 height=50, width=250, bordercolor="#00ff00", highlightcolor="#00ff00",
#                 activebackground="#111111", activeforeground="#00ff00"
#             )
#             self.canvas.create_window(stats_x, canvas_h - 60, window=play_button)


    def display_round_over(self, score, next_round_callback=None):
        self.canvas.delete("all")
        for widget in self.canvas.winfo_children():
            widget.destroy()
        label1 = tk.Label(self.canvas, text="ROUND OVER", font=("Courier New", 30), bg='#1a1a1a', fg='white')
        self.canvas.create_window(20, 20, anchor=tk.NW, window=label1)
        
        # Show humans saved
        actual_humans_saved = score.get("humans_saved", 0)
        label3 = tk.Label(self.canvas, text=f"Humans Saved: {actual_humans_saved}", font=("Courier New", 15), bg='#1a1a1a', fg='white')
        self.canvas.create_window(20, 90, anchor=tk.NW, window=label3)
        
        label4 = tk.Label(self.canvas, text="Humans Killed: {}".format(score.get("humans_killed", 0)), font=("Courier New", 15), bg='#1a1a1a', fg='white')
        self.canvas.create_window(20, 120, anchor=tk.NW, window=label4)
        label5 = tk.Label(self.canvas, text="Zombies Saved: {}".format(score.get("zombies_saved", 0)), font=("Courier New", 15), bg='#1a1a1a', fg='red')
        self.canvas.create_window(20, 150, anchor=tk.NW, window=label5)
        label6 = tk.Label(self.canvas, text="Zombies Killed: {}".format(score.get("zombies_killed", 0)), font=("Courier New", 15), bg='#1a1a1a', fg='white')
        self.canvas.create_window(20, 180, anchor=tk.NW, window=label6)
        if next_round_callback:
            next_round_btn = tk.Button(self.canvas, text="Next Round", font=("Courier New", 16, "bold"), 
                                     bg="#27ae60", fg="white", relief=tk.RAISED, bd=3,
                                     command=next_round_callback)
            self.canvas.create_window(20, 220, anchor=tk.NW, window=next_round_btn)

    def display_round_over_with_summary(
        self, score, next_round_callback=None, summary_text="Loading summary...",
        summary_label_ref_callback=None, round_images=None,
        initial_meter_values=None, final_meter_values=None
    ):
        # Resize the canvas to be much larger for the round over screen
        self.resize_for_round_over()
        
        # Clear the canvas first
        self.canvas.delete("all")
        for widget in self.canvas.winfo_children():
            widget.destroy()

        # Parse summary_text for Markdown H1 headline, Focus, and blurb
        headline = None
        focus = None
        blurb = None
        if summary_text and isinstance(summary_text, str):
            lines = summary_text.splitlines()
            for i, line in enumerate(lines):
                if line.strip().startswith('# '):
                    headline = line.strip()[2:].strip()
                    for j, next_line in enumerate(lines[i+1:], start=i+1):
                        if next_line.strip().lower().startswith('focus:'):
                            focus = next_line.split(':', 1)[1].strip()
                            blurb_lines = [l for l in lines[j+1:] if l.strip()]
                            blurb = '\n'.join(blurb_lines)
                            break
                        elif next_line.strip():
                            blurb = next_line.strip()
                            break
                    break
        blurb_text = blurb if blurb else summary_text

        # Use the larger canvas size for better layout
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        left_x = 60
        y_offset = 50

        # Title and stats
        self.canvas.create_text(left_x, y_offset, text="ROUND OVER", font=("Courier New", 36, "bold"), fill='#00ff00', anchor=tk.NW)
        
        # Show humans saved
        actual_humans_saved = score.get('humans_saved', 0)

        self.canvas.create_text(left_x, y_offset + 60, text=f"Humans Saved: {actual_humans_saved}", font=("Courier New", 18), fill='#00ff00', anchor=tk.NW)
        
        self.canvas.create_text(left_x, y_offset + 90, text=f"Humans Killed: {score.get('humans_killed', 0)}", font=("Courier New", 18), fill='#00ff00', anchor=tk.NW)
        self.canvas.create_text(left_x, y_offset + 120, text=f"Zombies Saved: {score.get('zombies_saved', 0)}", font=("Courier New", 18), fill='#ff0000', anchor=tk.NW)
        self.canvas.create_text(left_x, y_offset + 150, text=f"Zombies Killed: {score.get('zombies_killed', 0)}", font=("Courier New", 18), fill='#00ff00', anchor=tk.NW)
        self.canvas.create_text(left_x, y_offset + 180, text=f"Corpses Encountered: {score.get('corpses_encountered', 0)}", font=("Courier New", 18), fill='#888888', anchor=tk.NW)
        y_offset += 230


        # Headline
        if headline:
            headline_label = tk.Label(
                self.canvas, text=headline, font=("Helvetica", 24, "bold"),
                bg='#000000', fg='#00ff00', wraplength=canvas_w - left_x - 80,
                justify='left', anchor='w'
            )
            self.canvas.create_window(left_x, y_offset, anchor=tk.NW, window=headline_label)
            y_offset += headline_label.winfo_reqheight() + 20

        # Scrollable summary text box
        summary_frame_height = 120
        summary_frame_width = canvas_w - left_x - 80
        summary_frame = tk.Frame(self.canvas, bg='#000000', width=summary_frame_width, height=summary_frame_height)
        summary_frame.pack_propagate(False)
        text_widget = tk.Text(
            summary_frame, wrap=tk.WORD, font=("Courier New", 16, "italic"),
            bg='#000000', fg='#00ff00', relief=tk.FLAT, borderwidth=0,
            highlightthickness=0
        )
        text_widget.insert(tk.END, blurb_text)
        text_widget.config(state=tk.DISABLED)
        scrollbar = tk.Scrollbar(summary_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.config(yscrollcommand=scrollbar.set)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.create_window(left_x, y_offset, anchor=tk.NW, window=summary_frame)
        y_offset += summary_frame_height + 20

        # Image and Caption
        img_y_offset = y_offset
        if focus and round_images:
            selected_img_fp = self._select_image_for_focus(focus, round_images)
        else:
            selected_img_fp = None
        if selected_img_fp:

            summary_photo = display_photo(selected_img_fp, int(SUMMARY_IMG_WIDTH * 1.5), int(SUMMARY_IMG_HEIGHT * 1.5))
            self.canvas.create_image(left_x, img_y_offset, anchor=tk.NW, image=summary_photo, tags='summary_photo')
            self.summary_photo = summary_photo

            img_tuple = next((tup for tup in round_images if tup[0] == selected_img_fp), None)

            caption = "Generating caption..."
            caption_label = tk.Label(

                self.canvas, text=caption, font=("Courier New", 13, "italic"),
                bg='#000000', fg='#00ff00', wraplength=500, justify='left'
            )
            # Place caption under the image
            caption_y = img_y_offset + int(SUMMARY_IMG_HEIGHT * 1.5) + 10
            self.canvas.create_window(left_x, caption_y, anchor=tk.NW, window=caption_label)
            # Async fetch Groq caption
            def fetch_and_update_caption():
                groq_caption = get_image_caption_groq(focus, summary_blurb=blurb_text)
                def update_caption():
                    caption_label.config(text=groq_caption)
                self.canvas.after(0, update_caption)
            threading.Thread(target=fetch_and_update_caption, daemon=True).start()

        # Next Round button (positioned better for larger canvas)
        if next_round_callback:
            ButtonClass = get_button_class()
            next_round_btn = ButtonClass(
                self.canvas, text="Next Round", font=("Courier New", 16, "bold"),
                bg="#000000", fg="#00ff00", relief=tk.RAISED, bd=3, padx=20, pady=10,
                activebackground="#111111", activeforeground="#00ff00",
                height=60, width=200,  # Added height and width for tkmacosx
                command=next_round_callback
            )
            self.canvas.create_window(canvas_w - 300, 80, anchor=tk.NW, window=next_round_btn)

        # Meter Bars - positioned for larger canvas and moved down
        if initial_meter_values and final_meter_values:
            meter_labels = ["Military", "HRA", "Scientist", "Medic"]
            bar_w = 300
            bar_h = 35
            gap_y = 25
            # Position meters higher up and more to the left
            meters_x = canvas_w - bar_w - 300
            meters_y = canvas_h - (len(meter_labels) * (bar_h + gap_y)) -50

            for i, label in enumerate(meter_labels):
                y = meters_y + i * (bar_h + gap_y)
                self.canvas.create_text(
                    meters_x - 20, y + bar_h / 2, text=label, font=("Courier New", 18, "bold"), fill="#00ff00", anchor="e"
                )
                init_val = initial_meter_values[i]
                final_val = final_meter_values[i]
                init_frac = min(init_val / 1000.0, 1.0)
                final_frac = min(final_val / 1000.0, 1.0)
                
                # Draw the full bar outline first
                self.canvas.create_rectangle(
                    meters_x, y, meters_x + bar_w, y + bar_h,
                    outline="#00ff00", fill=""
                )
                
                # Draw the initial (gray) bar as background
                self.canvas.create_rectangle(
                    meters_x, y, meters_x + int(bar_w * init_frac), y + bar_h,
                    fill="#333333", outline=""
                )
                
                # Draw final bar on top (only the difference)
                if final_val > init_val:
                    # Green bar for increase (drawn on top of gray)
                    self.canvas.create_rectangle(
                        meters_x + int(bar_w * init_frac), y, meters_x + int(bar_w * final_frac), y + bar_h,
                        fill="#27ae60", outline=""
                    )
                elif final_val < init_val:
                    # Red bar for decrease (drawn from 0 to final, on top of gray)
                    self.canvas.create_rectangle(
                        meters_x, y, meters_x + int(bar_w * final_frac), y + bar_h,
                        fill="#e74c3c", outline=""
                    )
                # If equal, no additional bar needed
                
                self.canvas.create_text(
                    meters_x + bar_w + 15, y + bar_h / 2, text=f"{init_val} → {final_val}",
                    font=("Courier New", 16), fill="#00ff00", anchor="w"
                )
            self.canvas.create_text(
                meters_x + bar_w / 2, meters_y - 30,
                text="Initial (grey), Final (green/red)", font=("Courier New", 14, "italic"),
                fill="#00ff00", anchor="center"
            )

    def _select_image_for_focus(self, focus, round_images):
        if not focus or not round_images:
            return None
        focus = focus.lower().strip()

        def role_match(role, keyword):
            return keyword in role.lower()

        if focus == 'squished military':
            return next((fp for fp, action, state, role in round_images if action == 'squish' and role_match(role, 'military')), None)
        elif focus == 'squished doctor':
            return next((fp for fp, action, state, role in round_images if action == 'squish' and role_match(role, 'doctor')), None)
        elif focus == 'squished elderly':
            return next((fp for fp, action, state, role in round_images if action == 'squish' and role_match(role, 'elderly')), None)
        elif focus == 'squished business':
            return next((fp for fp, action, state, role in round_images if action == 'squish' and role_match(role, 'business')), None)
        elif focus == 'squished zombie':
            return next((fp for fp, action, state, role in round_images if action == 'squish' and state == 'zombie'), None)
        elif focus == 'saved zombie':
            return next((fp for fp, action, state, role in round_images if action == 'save' and state == 'zombie'), None)
        elif focus == 'saved military':
            return next((fp for fp, action, state, role in round_images if action == 'save' and role_match(role, 'military')), None)
        elif focus == 'saved doctor':
            return next((fp for fp, action, state, role in round_images if action == 'save' and role_match(role, 'doctor')), None)
        elif focus == 'saved elderly':
            return next((fp for fp, action, state, role in round_images if action == 'save' and role_match(role, 'elderly')), None)
        elif focus == 'saved business':
            return next((fp for fp, action, state, role in round_images if action == 'save' and role_match(role, 'business')), None)
        elif focus == 'scrammed everyone':
            return next((fp for fp, action, state, role in round_images if action == 'scram'), None)
        elif focus == 'skipped everyone':
            return next((fp for fp, action, state, role in round_images if action == 'skip'), None)
        elif focus == 'saved everyone':
            return next((fp for fp, action, state, role in round_images if action == 'save'), None)
        elif focus == 'no actions taken':
            return None
        # Fallback: just return the first image
        return round_images[0][0] if round_images else None

def display_photo(img_path, w, h):
    img = Image.open(img_path)
    resized = img.resize((w, h), Image.Resampling.LANCZOS)
    tk_img = ImageTk.PhotoImage(resized)
    return tk_img