import tkinter as tk
from tkinter import ttk
from threading import Thread
from pypresence import Presence
import time
import os
import psutil
import logging

# Constants
EU4_PROCESS_NAME = "eu4.exe"
DISCORD_APP_ID = '687351243462541358'
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June',
          'July', 'August', 'September', 'October', 'November', 'December']

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EU4PresenceApp:
    def __init__(self, master):
        self.master = master
        self.master.title("EU4 Presence App")
        self.master.geometry("400x300")

        self.presence = Presence(DISCORD_APP_ID)
        self.presence.connect()
        self.start_epoch = time.time()

        self.running = False  # Flag to control the script thread
        self.script_thread = None  # Reference to the script thread

        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self.master, text="EU4 Presence App",
                  font=("Helvetica", 16)).pack(pady=10)

        self.status_label = ttk.Label(self.master, text="Status: Ready")
        self.status_label.pack(pady=10)

        ttk.Button(self.master, text="Start Script",
                   command=self.start_script).pack(pady=10)
        ttk.Button(self.master, text="Stop Script",
                   command=self.stop_script).pack(pady=10)

    def set_savefile_path(self):
        potential_paths = [
            os.path.join(os.environ['USERPROFILE'], 'Documents',
                         'Paradox Interactive', 'Europa Universalis IV', 'save games'),
            os.path.join(os.environ['USERPROFILE'], 'OneDrive', 'Documents',
                         'Paradox Interactive', 'Europa Universalis IV', 'save games')
        ]

        for path in potential_paths:
            try:
                os.listdir(path)
                return path
            except FileNotFoundError:
                continue

        logger.error("No valid save file paths found.")
        return None

    def find_eu4_process(self):
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == EU4_PROCESS_NAME:
                logger.info(f"EU4 detected with PID: {proc.info['pid']}")
                return True
        return False

    def update_discord_presence(self):
        savefile_path = self.set_savefile_path()
        if not savefile_path:
            logger.warning("No save files found.")
            return

        try:
            save_list = os.listdir(savefile_path)
            if not save_list:
                logger.warning("No save files found.")
                return

            savefile_name = max(save_list, key=lambda x: os.stat(
                os.path.join(savefile_path, x)).st_mtime)
            logger.info("Using data from: %s", savefile_name)

            with open(os.path.join(savefile_path, savefile_name), "r") as f:
                contents = f.read()
                listconts = contents.split()

                country_rank_num = listconts[listconts.index(
                    "human=yes") + 3][16:]
                country_rank = "Duchy" if int(country_rank_num) == 1 else "Kingdom" if int(
                    country_rank_num) == 2 else "Empire"

                x = listconts.index("EU4txt")
                country_name = listconts[x + 4][24:len(listconts[x + 4]) - 1]
                current_month = MONTHS[int(
                    listconts[x + 1][10:][:-1][:-1]) - 1]
                current_year = listconts[x + 1][5:9]

                self.presence.update(
                    state=f"{current_month}, {current_year}",
                    details=f"{country_rank} of {country_name}",
                    large_text="Europa Universalis IV",
                    large_image="eu4logolarge",
                    start=self.start_epoch
                )
                logger.info("Updated presence successfully.")

        except Exception as e:
            logger.error(f"Error while updating presence: {e}")

    def start_script(self):
        if not self.running:
            self.status_label.config(text="Status: Script Running")
            self.running = True
            self.script_thread = Thread(target=self.run_script)
            self.script_thread.start()
            # Periodically check if the thread is still running
            self.master.after(100, self.check_thread)

    def run_script(self):
        try:
            while self.find_eu4_process() and self.running:
                self.update_discord_presence()
                time.sleep(20)
        except KeyboardInterrupt:
            logger.info("Script terminated by user.")
        finally:
            self.running = False
            self.presence.close()
            self.status_label.config(text="Status: Script Stopped")

    def check_thread(self):
        if self.script_thread and self.script_thread.is_alive():
            # Continue checking if the thread is still running
            self.master.after(100, self.check_thread)
        else:
            # Thread has finished, update UI
            self.status_label.config(text="Status: Script Stopped")

    def stop_script(self):
        if self.running:
            self.running = False
            self.script_thread.join()  # Wait for the background thread to finish
            self.status_label.config(text="Status: Script Stopped")


if __name__ == "__main__":
    root = tk.Tk()
    app = EU4PresenceApp(root)
    root.mainloop()
