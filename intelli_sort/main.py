import os
import yaml
import shutil
import logging
import argparse
import time
import sys # <- Import the 'sys' library
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- NEW HELPER FUNCTION ---
def resolve_path(path):
    """
    Get the absolute path to a resource, works for dev and for PyInstaller.
    """
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, path)
    return os.path.abspath(path)
# -------------------------

def setup_logging():
    # ... (This function remains exactly the same) ...
    logger = logging.getLogger()
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    log_file_path = resolve_path('organizer.log') # Use resolver for log file too
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


def load_config():
    """Loads the configuration from the YAML file."""
    # Use our new helper function to find the config file
    config_path = resolve_path("config.yaml")
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)
    return config

# The MyEventHandler class remains exactly the same...
class MyEventHandler(FileSystemEventHandler):
    def __init__(self, source_dir, categories):
        self.source_dir = source_dir
        self.categories = categories
    
    def on_created(self, event):
        if not event.is_directory:
            self.process_file(event.src_path)
            
    def process_file(self, file_path):
        filename = os.path.basename(file_path)
        time.sleep(1)
        if filename == 'organizer.log':
            return
        file_extension = os.path.splitext(filename)[1].lower()
        if not file_extension:
            logging.warning(f"Skipped: '{filename}' (No extension)")
            return
        for category_name, extensions in self.categories.items():
            if file_extension in extensions:
                dest_dir = os.path.join(self.source_dir, category_name)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
                    logging.info(f"Created new folder: {dest_dir}")
                try:
                    shutil.move(file_path, dest_dir)
                    logging.info(f"Moved: '{filename}' -> {category_name}/")
                except Exception as e:
                    logging.error(f"Could not move '{filename}'. Reason: {e}")
                return
        logging.warning(f"Skipped: '{filename}' (Uncategorized)")


if __name__ == "__main__":
    setup_logging()
    
    parser = argparse.ArgumentParser(description="Organize files in a directory in real-time.")
    parser.add_argument('--source', required=True, help="The source directory to monitor.")
    args = parser.parse_args()
    source_dir = args.source
    
    logging.info(f"Starting IntelliSort service on directory: {source_dir}")

    try:
        config = load_config()
        # ... (Rest of the main block is the same) ...
        categories = config.get("categories")
        if os.path.exists(source_dir) and categories:
            event_handler = MyEventHandler(source_dir, categories)
            observer = Observer()
            observer.schedule(event_handler, source_dir, recursive=False)
            observer.start()
            logging.info("Observer started. Watching for new files...")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logging.info("Shutdown signal received. Stopping observer.")
                observer.stop()
            observer.join()
        else:
            logging.error(f"Directory or categories configuration is invalid.")
    except Exception as e:
        logging.critical(f"An unexpected error occurred: {e}", exc_info=True)
    
    logging.info("IntelliSort service has been shut down.")