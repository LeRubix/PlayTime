import tkinter as tk
import time
import os
from tkinter import messagebox
import psutil
import threading

class PlaytimeTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("PlayTime")
        try:
            self.root.iconbitmap("playtime.ico")
        except tk.TclError:
            pass

        self.root.configure(bg="#333333")
        self.label_color = "#333333"
        self.button_color = "#666666"

        self.games = {}
        self.game_nicknames = {}
        self.playing_game = None
        self.current_game = tk.StringVar()
        self.process_name = tk.StringVar()
        self.playing = False
        self.selected_game_nickname = None
        self.check_thread = None

        self.setup_ui()
        self.check_and_create_data_file()
        self.load_data()
        self.update_result_label()

        self.current_game.set("")
        self.process_name.set("")

        self.first_run_flag = not os.path.exists("first_run.flag")
        if self.first_run_flag:
            self.show_first_run_message()

        self.root.protocol("WM_DELETE_WINDOW", self.save_data_and_quit)

    def setup_ui(self):
        tk.Label(root, text="Nickname:", bg=self.label_color, fg="white").grid(row=0, column=0, padx=10, pady=10)
        game_entry = tk.Entry(root, textvariable=self.current_game)
        game_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(root, text="Process Name:", bg=self.label_color, fg="white").grid(row=1, column=0, padx=10, pady=10)
        process_entry = tk.Entry(root, textvariable=self.process_name)
        process_entry.grid(row=1, column=1, padx=10, pady=10)

        self.question_mark_label = tk.Label(root, text="?", cursor="question_arrow", bg=self.label_color, fg="white")
        self.question_mark_label.bind("<Button-1>", self.show_help_message)
        self.question_mark_label.place(x=100, y=65)

        tk.Label(root, text="Previously Used:", bg=self.label_color, fg="white").grid(row=0, column=2)
        self.game_nickname_listbox = tk.Listbox(root, height=5)
        self.game_nickname_listbox.grid(row=1, column=2)

        self.icon_label = tk.Label(root, text="❓", cursor="hand2", font=("Helvetica", 10))
        self.icon_label.place(x=10, y=300)
        self.icon_label.bind("<Button-1>", self.show_about_message)

        self.status_label = tk.Label(root, text="Not Tracking", bg=self.label_color, fg="red")
        self.status_label.grid(row=2, column=0, columnspan=3, padx=10, pady=10)

        self.tracking_button = tk.Button(root, text="Start Tracking", command=self.toggle_tracking, bg=self.button_color, fg="white")
        self.tracking_button.grid(row=3, column=0, columnspan=3, padx=10, pady=10)

        self.result_label = tk.Label(root, text="", bg=self.label_color, fg="white")
        self.result_label.grid(row=4, column=0, columnspan=3, padx=10, pady=10)

        self.quit_button = tk.Button(root, text="Quit", command=self.save_data_and_quit, bg=self.button_color, fg="white")
        self.quit_button.grid(row=5, column=0, columnspan=3, padx=10, pady=10)

        self.delete_game_button = tk.Button(root, text="Delete Item from List", command=self.delete_selected_game, bg=self.button_color, fg="white")
        self.delete_game_button.grid(row=2, column=2, padx=10, pady=10)

        root.protocol("WM_DELETE_WINDOW", self.save_data_and_quit)

        self.game_nickname_listbox.bind("<<ListboxSelect>>", self.select_game_nickname)

    def check_and_create_data_file(self):
        if not os.path.exists("playtime_data.txt"):
            with open("playtime_data.txt", "w"):
                pass

    def show_first_run_message(self):
        messagebox.showinfo("Welcome", "Thanks for using PlayTime!\n\nIf you want to track anything manually (without defining a process), simply enter 'manual' or just a space into the process name box.\n\nAlso, keep the playtime data .txt file in the same folder as the program when you're using it.")
        with open("first_run.flag", "w"):
            pass

    def show_about_message(self, event):
        messagebox.showinfo("About", "This program was made by Rubix :)\nFind me at https://rubix.garden")

    def show_help_message(self, event):
        messagebox.showinfo("Help", "This field is for the process name of the program you want to track (e.g, GTA5.exe). It is case-sensitive.\n\nTo easily find the process name of a process, you can use Resource Monitor (or Task Manager > Right Click > Properties) if it's currently running.\n\nIf your program isn't running yet, you could look for the actual executable file for the program, but sometimes that can just be a launcher and not the actual name of the process.\n\nUSE THE PROCESS NAME 'manual' OR JUST A SPACE IF YOU WANT TO TRACK SOMETHING WITHOUT DEFINING A PROCESS!")

    def toggle_tracking(self):
        if self.playing:
            self.stop_tracking()
        else:
            game_nickname = self.current_game.get()
            process_name = self.process_name.get()

            if game_nickname and process_name:
                if process_name.lower() == "manual" or process_name.isspace():
                    self.game_nicknames[game_nickname] = "Manual"
                    if game_nickname not in self.games:
                        self.games[game_nickname] = 0
                        self.game_nickname_listbox.insert(tk.END, game_nickname)
                    self.save_data()
                    self.playing_game = game_nickname
                    self.start_time = time.time()
                    self.status_label.config(text=f"Tracking: {self.playing_game}", fg="green")
                    self.tracking_button.config(text="Stop Tracking")
                    self.playing = True
                elif self.is_process_running(process_name):
                    self.game_nicknames[game_nickname] = process_name
                    if game_nickname not in self.games:
                        self.games[game_nickname] = 0
                        self.game_nickname_listbox.insert(tk.END, game_nickname)
                    self.save_data()
                    self.playing_game = game_nickname
                    self.start_time = time.time()
                    self.status_label.config(text=f"Tracking: {self.playing_game}", fg="green")
                    self.tracking_button.config(text="Stop Tracking")
                    self.playing = True
                    self.check_thread = threading.Thread(target=self.process_check)
                    self.check_thread.daemon = True
                    self.check_thread.start()
                else:
                    messagebox.showerror("Error", f"The process '{process_name}' is not running.")
            else:
                messagebox.showerror("Error", "Game nickname and process name cannot be empty")

    def process_check(self):
        process_name = self.process_name.get()
        while self.playing:
            if not self.is_process_running(process_name):
                self.stop_tracking()
                break
            time.sleep(1)

    def start_tracking(self):
        game_nickname = self.current_game.get()
        process_name = self.process_name.get()
        self.current_game.set(game_nickname)
        self.process_name.set(process_name)

        if self.is_process_running(process_name):
            self.status_label.config(text=f"Tracking: {self.current_game.get()}")
            self.tracking_button.config(text="Stop Tracking")
            self.playing = True
            self.start_time = time.time()
        else:
            messagebox.showerror("Error", f"The process '{process_name}' is not running.")

    def stop_tracking(self):
        if self.playing:
            self.playing = False
            end_time = time.time()
            elapsed_time = end_time - self.start_time
            self.add_playtime(self.playing_game, elapsed_time)
            self.status_label.config(text="Not Tracking", fg="red")
            self.tracking_button.config(text="Start Tracking")
            self.playing = False
            self.playing_game = None

    def add_playtime(self, game, elapsed_time):
        if game in self.games:
            self.games[game] += elapsed_time
            self.update_result_label()

    def format_time(self, seconds):
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        return f"{int(days)} days, {int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds"

    def update_result_label(self):
        result_text = "Playtime:\n"
        for game, playtime in self.games.items():
            formatted_time = self.format_time(playtime)
            result_text += f"{game}: {formatted_time}\n"
        self.result_label.config(text=result_text)

    def select_game_nickname(self, event):
        selected_items = self.game_nickname_listbox.curselection()
        if selected_items: 
            selected_game = self.game_nickname_listbox.get(selected_items[0])
            if selected_game in self.game_nicknames:
                self.selected_game_nickname = selected_game
                game_nickname = selected_game
                process_name = self.game_nicknames[game_nickname]
                self.current_game.set(game_nickname)
                self.process_name.set(process_name)

    def load_data(self):
        self.game_nickname_listbox.selection_clear(0, tk.END)
        try:
            with open("playtime_data.txt", "r") as file:
                data = file.readlines()
                for line in data:
                    parts = line.strip().split(": ")
                    if len(parts) == 3:
                        game_nickname, process_name, playtime = parts
                        self.games[game_nickname] = float(playtime)
                        self.game_nicknames[game_nickname] = process_name
                        self.game_nickname_listbox.insert(tk.END, game_nickname)
                    elif len(parts) == 2:
                        game_nickname, process_name = parts
                        self.game_nicknames[game_nickname] = process_name
                        self.game_nickname_listbox.insert(tk.END, game_nickname)
        except FileNotFoundError:
            pass

    def save_data(self):
        with open("playtime_data.txt", "w") as file:
            for game, playtime in self.games.items():
                process_name = self.game_nicknames.get(game, "")
                file.write(f"{game}: {process_name}: {playtime}\n")

    def save_data_and_quit(self):
        self.stop_tracking()
        self.save_data()
        self.root.quit()

    def is_process_running(self, process_name):
        for process in psutil.process_iter(attrs=['name']):
            if process.info['name'] == process_name:
                return True
        return False

    def delete_selected_game(self):
        selected_game = self.game_nickname_listbox.get(tk.ACTIVE)
        if selected_game:
            confirmed = messagebox.askokcancel("Confirm Deletion", f"Are you sure you want to delete '{selected_game}'?")
            if confirmed:
                self.delete_game(selected_game)

    def delete_game(self, game):
        if game in self.games:
            del self.games[game]
        if game in self.game_nicknames:
            del self.game_nicknames[game]
        self.game_nickname_listbox.delete(tk.ACTIVE)
        self.update_result_label()
        self.save_data()

if __name__ == "__main__":
    root = tk.Tk()
    app = PlaytimeTracker(root)
    root.mainloop()
