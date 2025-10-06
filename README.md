# IntelliSort - Automated File Management System

![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

A smart, real-time, and configurable utility that automatically organizes files in a directory based on their extension, with a robust undo feature to ensure user control.

---

### Key Features

This project was built from the ground up to be a professional-grade software utility, demonstrating a full range of development skills:

* **Real-Time Monitoring:** Utilizes the `watchdog` library to monitor a target directory and organize new files the instant they are created or downloaded.
* **Initial Cleanup:** On startup, the service first performs a full scan to organize all pre-existing files before beginning real-time monitoring.
* **User-Defined Rules:** All categorization logic is managed in a clean, human-readable `config.yaml` file, allowing users to easily define their own rules without touching the source code.
* **Transactional Undo Feature:** Every file move is recorded in a `SQLite` database. A command-line flag (`--undo`) allows the user to safely revert the entire last organization session, including the removal of newly created empty folders.
* **Professional Logging:** All actions are logged to both the console and a persistent `organizer.log` file, with different log levels for routine operations (`INFO`), recoverable issues (`WARNING`), and critical failures (`ERROR`).
* **Flexible CLI:** Built with Python's `argparse` module, the tool can be pointed at any directory, making it a flexible and reusable utility.
* **Verified & Reliable:** The core file processing logic is backed by automated `unit tests` written with the `pytest` framework to ensure reliability and prevent regressions.
* **Packaged for Distribution:** The entire application is packaged into a standalone Windows executable (`.exe`) using `PyInstaller`, allowing it to be run on any Windows machine without needing Python or any libraries installed.

---

### Technology Stack

* **Language:** Python 3
* **Database:** SQLite 3 (built-in)
* **Core Libraries:**
    * `watchdog` (Real-Time Monitoring)
    * `PyYAML` (Configuration Management)
    * `pytest` (Unit Testing)
    * `PyInstaller` (Packaging)

---

### Installation & Usage (for Developers)

To run this project from the source code:

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/BattuNarayana/intelli-sort.git](https://github.com/BattuNarayana/intelli-sort.git)
    cd intelli-sort
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application:**
    *(To organize a folder)*
    ```bash
    python intelli_sort/main.py --source "C:\Path\To\Your\Folder"
    ```
    *(To undo the last run)*
    ```bash
    python intelli_sort/main.py --undo
    ```

5.  **Run tests:**
    ```bash
    pytest
    ```

---

### License
This project is licensed under the MIT License. See the `LICENSE` file for details.