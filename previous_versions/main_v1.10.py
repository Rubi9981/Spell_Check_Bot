import tkinter as tk
from tkinter import ttk
import time


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
        self.geometry("680x220")  # Increased window size for checkboxes
        self.resizable(False, False)

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

        # Add headers for checkboxes
        ttk.Label(container, text="Ionian Boots", font=("Helvetica", 8)).grid(
            row=0, column=4, padx=5
        )
        ttk.Label(container, text="Cosmic Insight", font=("Helvetica", 8)).grid(
            row=0, column=5, padx=5
        )

        for i, role in enumerate(self.roles):
            # Role name label
            role_label = ttk.Label(
                container, text=f"{role}:", font=("Helvetica", 10, "bold")
            )
            role_label.grid(row=i + 1, column=0, padx=(0, 10), pady=5, sticky="w")

            # Cooldown status label
            self.labels[role] = ttk.Label(
                container, text="Ready", font=("Helvetica", 10), width=20
            )
            self.labels[role].grid(row=i + 1, column=1, padx=10, pady=5, sticky="w")

            # 'Used Flash' button
            self.buttons[role] = ttk.Button(
                container, text="Used Flash", command=lambda r=role: self.start_timer(r)
            )
            self.buttons[role].grid(row=i + 1, column=2, padx=(0, 5), pady=5)

            # 'Reset' button
            reset_button = ttk.Button(
                container, text="Reset", command=lambda r=role: self.reset_timer(r)
            )
            reset_button.grid(row=i + 1, column=3, padx=(0, 10), pady=5)

            # Checkboxes
            boots_check = ttk.Checkbutton(
                container, variable=self.checkbox_vars[role]["boots"]
            )
            boots_check.grid(row=i + 1, column=4)

            cosmic_check = ttk.Checkbutton(
                container, variable=self.checkbox_vars[role]["cosmic"]
            )
            cosmic_check.grid(row=i + 1, column=5)

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

    def reset_timer(self, role):
        """Resets the cooldown timer for a specific role."""
        self.timers[role].reset()

    def update_timers(self):
        """Periodically updates the cooldown labels."""
        for role in self.roles:
            timer = self.timers[role]
            remaining_time = timer.get_remaining_time()

            if remaining_time > 0:
                self.labels[role].config(
                    text=f"{remaining_time:.0f}s remaining", foreground="red"
                )
            else:
                self.labels[role].config(text="Ready", foreground="green")

        self.after(1000, self.update_timers)


if __name__ == "__main__":
    app = FlashTrackerApp()
    app.mainloop()
