# MacDictate

A local macOS dictation app using MLX Whisper.

## Features
- **Local Transcription**: Uses `mlx-whisper` for fast, private transcription on Apple Silicon.
- **Global Hotkey**: Toggle recording with `Left Control`.
- **Background Mode**: Can be run via Automator as a service.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/MacDictate.git
    cd MacDictate
    ```

2.  **Set up Python Environment**:
    Recommended to use `pyenv` and python 3.11.
    ```bash
    pyenv install 3.11.9
    pyenv local 3.11.9
    cd .
    # Create venv if desired, or use pyenv directly
    pip install -r requirements.txt
    ```

## Usage

Run the main script:
```bash
python main.py
```

- **Start/Stop Recording**: Press `Left Control`.
- **Output**: Text is copied to clipboard and pasted into the active application.

## Automator Setup (Run as Service)

To run MacDictate in the background using macOS Automator:

1.  Open **Automator** and create a new **Application**.
2.  Add a **Run Shell Script** action.
3.  Set "Pass input" to `to stdin`.
4.  Paste the contents of `run_mac_dictate.sh` (or just call the script directly):

    ```bash
    /Users/antony/Documents/Projects/MacDictate/run_mac_dictate.sh
    ```
    *(Make sure `run_mac_dictate.sh` is executable: `chmod +x run_mac_dictate.sh`)*

5.  Save the Automator app (e.g., "MacDictate Service").
6.  Add the Automator app to your **Login Items** in System Settings if you want it to start automatically.

**Note:** The `run_mac_dictate.sh` script is configured to use the absolute path to your specific Python environment to avoid path issues in Automator. If you move the project or change python versions, check this script.
