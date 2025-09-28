# import os
# import yaml
# import shutil
# import logging
# import argparse
# import time
# import sys # <- Import the 'sys' library
# from watchdog.observers import Observer
# from watchdog.events import FileSystemEventHandler

# # --- NEW HELPER FUNCTION ---
# def resolve_path(path):
#     """
#     Get the absolute path to a resource, works for dev and for PyInstaller.
#     """
#     # PyInstaller creates a temp folder and stores path in _MEIPASS
#     if hasattr(sys, '_MEIPASS'):
#         return os.path.join(sys._MEIPASS, path)
#     return os.path.abspath(path)
# # -------------------------

# def setup_logging():
#     # ... (This function remains exactly the same) ...
#     logger = logging.getLogger()
#     if logger.hasHandlers():
#         logger.handlers.clear()
#     logger.setLevel(logging.INFO)
#     formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
#     log_file_path = resolve_path('organizer.log') # Use resolver for log file too
#     file_handler = logging.FileHandler(log_file_path)
#     file_handler.setFormatter(formatter)
#     stream_handler = logging.StreamHandler()
#     stream_handler.setFormatter(formatter)
#     logger.addHandler(file_handler)
#     logger.addHandler(stream_handler)


# def load_config():
#     """Loads the configuration from the YAML file."""
#     # Use our new helper function to find the config file
#     config_path = resolve_path("config.yaml")
#     with open(config_path, "r") as file:
#         config = yaml.safe_load(file)
#     return config

# # The MyEventHandler class remains exactly the same...
# class MyEventHandler(FileSystemEventHandler):
#     def __init__(self, source_dir, categories):
#         self.source_dir = source_dir
#         self.categories = categories
    
#     def on_created(self, event):
#         if not event.is_directory:
#             self.process_file(event.src_path)
            
#     def process_file(self, file_path):
#         filename = os.path.basename(file_path)
#         time.sleep(1)
#         if filename == 'organizer.log':
#             return
#         file_extension = os.path.splitext(filename)[1].lower()
#         if not file_extension:
#             logging.warning(f"Skipped: '{filename}' (No extension)")
#             return
#         for category_name, extensions in self.categories.items():
#             if file_extension in extensions:
#                 dest_dir = os.path.join(self.source_dir, category_name)
#                 if not os.path.exists(dest_dir):
#                     os.makedirs(dest_dir)
#                     logging.info(f"Created new folder: {dest_dir}")
#                 try:
#                     shutil.move(file_path, dest_dir)
#                     logging.info(f"Moved: '{filename}' -> {category_name}/")
#                 except Exception as e:
#                     logging.error(f"Could not move '{filename}'. Reason: {e}")
#                 return
#         logging.warning(f"Skipped: '{filename}' (Uncategorized)")


# if __name__ == "__main__":
#     setup_logging()
    
#     parser = argparse.ArgumentParser(description="Organize files in a directory in real-time.")
#     parser.add_argument('--source', required=True, help="The source directory to monitor.")
#     args = parser.parse_args()
#     source_dir = args.source
    
#     logging.info(f"Starting IntelliSort service on directory: {source_dir}")

#     try:
#         config = load_config()
#         # ... (Rest of the main block is the same) ...
#         categories = config.get("categories")
#         if os.path.exists(source_dir) and categories:
#             event_handler = MyEventHandler(source_dir, categories)
#             observer = Observer()
#             observer.schedule(event_handler, source_dir, recursive=False)
#             observer.start()
#             logging.info("Observer started. Watching for new files...")
#             try:
#                 while True:
#                     time.sleep(1)
#             except KeyboardInterrupt:
#                 logging.info("Shutdown signal received. Stopping observer.")
#                 observer.stop()
#             observer.join()
#         else:
#             logging.error(f"Directory or categories configuration is invalid.")
#     except Exception as e:
#         logging.critical(f"An unexpected error occurred: {e}", exc_info=True)
    
#     logging.info("IntelliSort service has been shut down.")

import os
import yaml
import shutil
import logging
import argparse
import time
import sys
import sqlite3
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

DB_FILE = 'history.db'

def resolve_path(path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, path)
    return os.path.abspath(path)

# --- DATABASE FUNCTIONS (remain the same) ---
def init_db():
    db_path = resolve_path(DB_FILE)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS move_history (
                id INTEGER PRIMARY KEY,
                source_path TEXT NOT NULL,
                destination_path TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        conn.commit()

def log_move(source, destination):
    db_path = resolve_path(DB_FILE)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO move_history (source_path, destination_path, timestamp) VALUES (?, ?, ?)",
            (source, destination, datetime.now().isoformat())
        )
        conn.commit()

def perform_undo():
    """Reverts the last set of file moves and cleans up empty folders."""
    db_path = resolve_path(DB_FILE)
    if not os.path.exists(db_path):
        logging.warning("No history database found. Nothing to undo.")
        return

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, source_path, destination_path FROM move_history ORDER BY id DESC")
        moves = cursor.fetchall()

        if not moves:
            logging.info("Move history is empty. Nothing to undo.")
            return

        logging.info(f"Found {len(moves)} moves to revert. Proceeding to undo...")
        for move_id, source_path, dest_path in moves:
            try:
                if os.path.exists(dest_path):
                    original_folder = os.path.dirname(source_path)
                    folder_that_will_be_emptied = os.path.dirname(dest_path) # Get the folder path (e.g., .../Documents)

                    shutil.move(dest_path, original_folder)
                    logging.info(f"Reverted: '{os.path.basename(dest_path)}' -> {original_folder}")
                    
                    # --- NEW CLEANUP LOGIC ---
                    # After moving the file, check if the folder is now empty
                    if not os.listdir(folder_that_will_be_emptied):
                        os.rmdir(folder_that_will_be_emptied)
                        logging.info(f"Removed empty folder: {folder_that_will_be_emptied}")
                    # --------------------------

                    cursor.execute("DELETE FROM move_history WHERE id = ?", (move_id,))
                else:
                    logging.warning(f"File '{os.path.basename(dest_path)}' no longer at destination. Removing log entry.")
                    cursor.execute("DELETE FROM move_history WHERE id = ?", (move_id,))
            except Exception as e:
                logging.error(f"Failed to revert move for {os.path.basename(dest_path)}. Reason: {e}")
        conn.commit()
    logging.info("Undo operation complete.")

# --- setup_logging() and load_config() remain the same ---
def setup_logging():
    # ... (same as before) ...
    logger = logging.getLogger()
    if logger.hasHandlers(): logger.handlers.clear()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    log_file_path = resolve_path('organizer.log')
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
def load_config():
    # ... (same as before) ...
    config_path = resolve_path("config.yaml")
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)
    return config

# --- MyEventHandler class remains the same ---
class MyEventHandler(FileSystemEventHandler):
    # ... (same as before) ...
    def __init__(self, source_dir, categories):
        self.source_dir = source_dir
        self.categories = categories
    def on_created(self, event):
        if not event.is_directory: self.process_file(event.src_path)
    def process_file(self, file_path):
        filename = os.path.basename(file_path)
        time.sleep(1)
        if filename in ['organizer.log', DB_FILE] or not os.path.exists(file_path): return
        file_extension = os.path.splitext(filename)[1].lower()
        if not file_extension:
            logging.warning(f"Skipped: '{filename}' (No extension)"); return
        for category_name, extensions in self.categories.items():
            if file_extension in extensions:
                dest_dir = os.path.join(self.source_dir, category_name)
                dest_file_path = os.path.join(dest_dir, filename)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir); logging.info(f"Created new folder: {dest_dir}")
                try:
                    shutil.move(file_path, dest_file_path)
                    log_move(file_path, dest_file_path)
                    logging.info(f"Moved: '{filename}' -> {category_name}/")
                except Exception as e:
                    logging.error(f"Could not move '{filename}'. Reason: {e}")
                return
        logging.warning(f"Skipped: '{filename}' (Uncategorized)")

# --- THIS IS THE FIX ---
# 1. Re-introducing the initial cleanup function.
def perform_initial_cleanup(source_dir, categories):
    """Scans and organizes all files currently in the directory."""
    logging.info("Performing initial cleanup of existing files...")
    handler = MyEventHandler(source_dir, categories)
    for filename in os.listdir(source_dir):
        file_path = os.path.join(source_dir, filename)
        if os.path.isfile(file_path):
            handler.process_file(file_path)
    logging.info("Initial cleanup complete.")

if __name__ == "__main__":
    setup_logging()
    init_db()
    
    parser = argparse.ArgumentParser(description="Organize files in a directory in real-time or undo the last run.")
    parser.add_argument('--source', help="The source directory to monitor. Required for organizing.")
    parser.add_argument('--undo', action='store_true', help="Undo the last organization run.")
    args = parser.parse_args()

    if args.undo:
        perform_undo()
    elif args.source:
        source_dir = args.source
        logging.info(f"Starting IntelliSort service on directory: {source_dir}")
        try:
            config = load_config()
            categories = config.get("categories")
            if os.path.exists(source_dir) and categories:
                # 2. CALLING the cleanup function before starting the observer.
                perform_initial_cleanup(source_dir, categories)
                
                event_handler = MyEventHandler(source_dir, categories)
                observer = Observer()
                observer.schedule(event_handler, source_dir, recursive=False)
                observer.start()
                logging.info("Observer started. Now watching for new files...")
                try:
                    while True: time.sleep(1)
                except KeyboardInterrupt:
                    logging.info("Shutdown signal received. Stopping observer.")
                    observer.stop()
                observer.join()
            else:
                logging.error(f"Directory or categories configuration is invalid.")
        except Exception as e:
            logging.critical(f"An unexpected error occurred: {e}", exc_info=True)
        logging.info("IntelliSort service has been shut down.")
    else:
        logging.warning("No action specified. Please provide '--source' to start organizing or '--undo' to revert.")
        parser.print_help()