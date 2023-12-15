from pypresence import Presence
import time
import os
import psutil
import logging
# Constants
EU4_PROCESS_NAME = "eu4.exe"
DISCORD_APP_ID = '687351243462541358'
SAVEFILE_PATHS = [os.path.join(os.environ['USERPROFILE'], 'Documents', 'Paradox Interactive', 'Europa Universalis IV', 'save games'),
                  os.path.join(os.environ['USERPROFILE'], 'OneDrive', 'Documents', 'Paradox Interactive', 'Europa Universalis IV', 'save games')]
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June',
          'July', 'August', 'September', 'October', 'November', 'December']

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_eu4_process():
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == EU4_PROCESS_NAME:
            logger.info(f"EU4 detected with PID: {proc.info['pid']}")
            return True
    return False


def get_savefile_path():
    for path in SAVEFILE_PATHS:
        try:
            os.listdir(path)
            return path
        except FileNotFoundError:
            continue
    logger.error("No valid save file paths found.")
    return None


def update_discord_presence(file_path, presence, start_epoch):
    try:
        save_list = os.listdir(file_path)
        if not save_list:
            logger.warning("No save files found.")
            return

        savefile_name = max(save_list, key=lambda x: os.stat(
            os.path.join(file_path, x)).st_mtime)
        logger.info("Using data from: %s", savefile_name)

        with open(os.path.join(file_path, savefile_name), "r") as f:
            contents = f.read()
            listconts = contents.split()

            country_rank_num = listconts[listconts.index("human=yes") + 3][16:]
            country_rank = "Duchy" if int(country_rank_num) == 1 else "Kingdom" if int(
                country_rank_num) == 2 else "Empire"

            x = listconts.index("EU4txt")
            country_name = listconts[x + 4][24:len(listconts[x + 4]) - 1]
            current_month = MONTHS[int(listconts[x + 1][10:][:-1][:-1]) - 1]
            current_year = listconts[x + 1][5:9]

            presence.update(
                state=f"{current_month}, {current_year}",
                details=f"{country_rank} of {country_name}",
                large_text="Europa Universalis IV",
                large_image="eu4logolarge",
                start=start_epoch
            )
            logger.info("Updated presence successfully.")

    except Exception as e:
        logger.error(f"Error while updating presence: {e}")


def main():
    presence = Presence(DISCORD_APP_ID)
    presence.connect()
    start_epoch = time.time()

    try:
        while find_eu4_process():
            savefile_path = get_savefile_path()

            if savefile_path:
                update_discord_presence(savefile_path, presence, start_epoch)

            time.sleep(20)

    except KeyboardInterrupt:
        logger.info("Script terminated by user.")

    finally:
        presence.close()


if __name__ == "__main__":
    main()
