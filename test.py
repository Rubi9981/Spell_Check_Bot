import tkinter as tk
from tkinter import ttk
import time
from PIL import Image, ImageTk
import os
import sys


class Spell:
    """Represents a spell with a name and cooldown."""

    def __init__(self, name, cooldown):
        self.name = name
        self.base_cooldown = cooldown


class CooldownTimer:
    """Manages the cooldown state for a spell."""

    def __init__(self, spell):
        self.spell = spell
        self.start_time = 0
        self.is_active = False
        self.current_cooldown = spell.base_cooldown

    def activate(self, cooldown):
        """Activates or restarts the timer with a specific cooldown."""
        self.current_cooldown = cooldown
        self.start_time = time.time()
        self.is_active = True

    def reset(self):
        """Resets the timer manually."""
        self.is_active = False
        self.start_time = 0

    def get_remaining_time(self):
        """Returns the remaining cooldown time in seconds."""
        if not self.is_active:
            return 0

        elapsed = time.time() - self.start_time
        if elapsed >= self.current_cooldown:
            self.is_active = False
            self.start_time = 0
            return 0
        else:
            return self.current_cooldown - elapsed


class FlashTrackerApp(tk.Tk):
    """Main application class for the Flash Tracker GUI."""

    def __init__(self):
        super().__init__()
        self.title("Enemy Flash Tracker")
        self.geometry("250x250")  # Adjusted window size
        self.resizable(False, False)

        # Load and resize the flash image
        if getattr(sys, 'frozen', False):
            # Running in a PyInstaller bundle
            base_path = sys._MEIPASS
        else:
            # Running in a normal Python environment
            base_path = os.path.abspath(".")

        self.flash_image = Image.open(os.path.join(base_path, "flash.png"))
        self.flash_image = self.flash_image.resize(
            (30, 30), Image.LANCZOS
        )  # Resize to 30x30 pixels
        self.flash_photo = ImageTk.PhotoImage(self.flash_image)

        # Load and resize Ionian Boots image
        self.boots_image_original = Image.open(os.path.join(base_path, "Ionian_Boots.png")).resize(
            (15, 15), Image.LANCZOS
        )
        self.boots_photo_opaque = ImageTk.PhotoImage(self.boots_image_original)
        self.boots_image_transparent = self.boots_image_original.copy()
        self.boots_image_transparent.putalpha(128)  # 50% transparency
        self.boots_photo_transparent = ImageTk.PhotoImage(self.boots_image_transparent)

        # Load and resize Cosmic Insight image
        self.cosmic_image_original = Image.open(os.path.join(base_path, "Cosmic_Insight.png")).resize(
            (15, 15), Image.LANCZOS
        )
        self.cosmic_photo_opaque = ImageTk.PhotoImage(self.cosmic_image_original)
        self.cosmic_image_transparent = self.cosmic_image_original.copy()
        self.cosmic_image_transparent.putalpha(128)  # 50% transparency
        self.cosmic_photo_transparent = ImageTk.PhotoImage(
            self.cosmic_image_transparent
        )

        self.game_start_time = 0
        self.is_game_timer_running = False
        self.game_timer_value = tk.StringVar(value="00:00")  # Initial display
        self._game_timer_after_id = None  # To store the after ID for game timer

        self.flash_spell = Spell("Flash", 300)
        self.roles = ["Top", "Jungle", "Mid", "ADC", "Support"]

        self.timers = {role: CooldownTimer(self.flash_spell) for role in self.roles}
        self.labels = {}
        self.buttons = {}
        self.checkbox_vars = {
            role: {"boots": tk.BooleanVar(), "cosmic": tk.BooleanVar()}
            for role in self.roles
        }

        self._create_widgets()
        self.update_timers()

    def _create_widgets(self):
        """Creates and lays out the GUI widgets."""
        container = ttk.Frame(self, padding="10")
        container.pack(expand=True, fill="both")

        # Game Timer Entry and Button
        self.game_timer_entry = ttk.Entry(
            container,
            textvariable=self.game_timer_value,
            width=8,
            font=("Helvetica", 12, "bold"),
            justify="center",
        )
        self.game_timer_entry.grid(row=0, column=0, columnspan=3, pady=2)
        self.game_timer_entry.bind(
            "<Return>", self.set_game_time_from_entry
        )  # Allow setting time by pressing Enter

        self.game_timer_button = ttk.Button(
            container, text="Start Game", command=self.toggle_game_timer
        )
        self.game_timer_button.grid(row=0, column=3, columnspan=2, pady=2)

        for i, role in enumerate(self.roles):
            # Role name label
            role_label = ttk.Label(
                container, text=f"{role}:", font=("Helvetica", 10, "bold")
            )
            role_label.grid(row=i + 1, column=0, padx=(0, 2), pady=1, sticky="w")

            # Cooldown status label
            self.labels[role] = ttk.Label(
                container, text="Ready", font=("Helvetica", 10)
            )
            self.labels[role].grid(row=i + 1, column=1, padx=2, pady=1, sticky="w")

            # 'Used Flash' button
            self.buttons[role] = ttk.Button(
                container,
                image=self.flash_photo,
                command=lambda r=role: self.start_timer(r),
                width=30,  # Set a fixed width for a square button
            )
            self.buttons[role].grid(row=i + 1, column=2, padx=(0, 2), pady=1)

            # Ionian Boots button (replaces checkbox)
            boots_button = ttk.Button(
                container,
                image=self.boots_photo_transparent,  # Initial image is transparent
                command=lambda r=role: self.toggle_checkbox(r, "boots"),
                width=15,  # Half size of flash button
            )
            boots_button.grid(row=i + 1, column=3, padx=0, pady=1)
            self.checkbox_vars[role]["boots"].trace_add(
                "write",
                lambda *args, r=role, btn=boots_button: self.update_button_relief(
                    r, "boots", btn
                ),
            )

            # Cosmic Insight button (replaces checkbox)
            cosmic_button = ttk.Button(
                container,
                image=self.cosmic_photo_transparent,  # Initial image is transparent
                command=lambda r=role: self.toggle_checkbox(r, "cosmic"),
                width=15,  # Half size of flash button
            )
            cosmic_button.grid(row=i + 1, column=4, padx=0, pady=1)
            self.checkbox_vars[role]["cosmic"].trace_add(
                "write",
                lambda *args, r=role, btn=cosmic_button: self.update_button_relief(
                    r, "cosmic", btn
                ),
            )

    def start_timer(self, role):
        """Starts or restarts the cooldown timer for a specific role with the correct cooldown."""
        has_boots = self.checkbox_vars[role]["boots"].get()
        has_cosmic = self.checkbox_vars[role]["cosmic"].get()

        cooldown = self.flash_spell.base_cooldown

        if has_boots and has_cosmic:
            cooldown = 230
        elif has_boots:
            cooldown = 267
        elif has_cosmic:
            cooldown = 254

        self.timers[role].activate(cooldown)

    def toggle_checkbox(self, role, item_type):
        """Toggles the state of the associated BooleanVar."""
        self.checkbox_vars[role][item_type].set(
            not self.checkbox_vars[role][item_type].get()
        )

    def update_button_relief(self, role, item_type, button):
        """Updates the relief and image of the button based on the checkbox state."""
        if self.checkbox_vars[role][item_type].get():
            if item_type == "boots":
                button.config(image=self.boots_photo_opaque)
            elif item_type == "cosmic":
                button.config(image=self.cosmic_photo_opaque)
        else:
            if item_type == "boots":
                button.config(image=self.boots_photo_transparent)
            elif item_type == "cosmic":
                button.config(image=self.cosmic_photo_transparent)

    def update_timers(self):
        """Periodically updates the cooldown labels."""
        for role in self.roles:
            timer = self.timers[role]
            remaining_time = timer.get_remaining_time()

            if remaining_time > 0:
                self.labels[role].config(
                    text=f"{remaining_time:.0f}s", foreground="red"
                )
            else:
                self.labels[role].config(text="Ready", foreground="green")

        self.after(1000, self.update_timers)

    def toggle_game_timer(self):
        if self.is_game_timer_running:
            self.is_game_timer_running = False
            self.game_timer_button.config(text="Start Game")
            self.game_timer_entry.config(state="normal")  # Allow editing when stopped
            if self._game_timer_after_id:  # Cancel scheduled update if exists
                self.after_cancel(self._game_timer_after_id)
                self._game_timer_after_id = None
        else:
            self.is_game_timer_running = True
            self.game_timer_button.config(text="Stop Game")
            self.game_timer_entry.config(
                state="readonly"
            )  # Prevent editing when running
            # Set start time based on current entry value or 0 if empty/invalid
            current_time_str = self.game_timer_value.get()
            try:
                minutes, seconds = map(int, current_time_str.split(":"))
                initial_seconds = minutes * 60 + seconds
            except ValueError:
                initial_seconds = 0  # Default to 0 if format is wrong
            self.game_start_time = time.time() - initial_seconds
            self.update_game_timer()

    def update_game_timer(self):
        if self.is_game_timer_running:
            elapsed_seconds = int(time.time() - self.game_start_time)
            minutes = elapsed_seconds // 60
            seconds = elapsed_seconds % 60
            self.game_timer_value.set(f"{minutes:02d}:{seconds:02d}")
            self._game_timer_after_id = self.after(1000, self.update_game_timer)

    def set_game_time_from_entry(self, event=None):
        # This function is called when user presses Enter in the Entry widget
        if not self.is_game_timer_running:
            current_time_str = self.game_timer_value.get()
            try:
                minutes, seconds = map(int, current_time_str.split(":"))
                # Optionally add validation for minutes/seconds range
                if not (0 <= minutes < 60 and 0 <= seconds < 60):
                    raise ValueError("Invalid time range")
                total_seconds = minutes * 60 + seconds
                self.game_timer_value.set(
                    f"{minutes:02d}:{seconds:02d}"
                )  # Format for consistency
            except ValueError:
                self.game_timer_value.set("00:00")  # Reset to 00:00 on invalid input


if __name__ == "__main__":
    app = FlashTrackerApp()
    app.mainloop()
