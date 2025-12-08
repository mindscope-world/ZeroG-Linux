# MacDictate

A local macOS dictation app using **MLX Whisper** for fast, private, on-device transcription on Apple Silicon.

## Features
- **Local Transcription**: Uses `mlx-whisper` (Apple Silicon optimized).
- **Global Hotkey**: Press `Left Control` to toggle recording.
- **Audio Feedback**: Plays a confirmation sound (configurable).
- **Background Service**: Ready for macOS Automator integration.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/MacDictate.git
    cd MacDictate
    ```

2.  **Install Dependencies**:
    Requires Python 3.11+. Recommended to use a virtual environment.
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

You can customize the application by editing `main.py`:
- **Sound**: Change `SOUND_FILE` to any standard macOS sound.
  - Recommended: `/System/Library/Sounds/Pop.aiff` or `Tink.aiff`.
- **Model**: Change `MODEL_PATH` to use a different Whisper model (e.g., `mlx-community/whisper-tiny-mlx`, `small`, `large`).

## Usage

### Manual Run
```bash
python main.py
```
- **Start/Stop Recording**: Press `Left Control`.
- **Output**: Transcribed text is copied to clipboard and pasted into the active application.

### Run as macOS Service (Automator)

To run MacDictate in the background automatically:

1.  Open **Automator** on your Mac.
2.  Create a new **Application**.
3.  Search for and add the **Run Shell Script** action.
4.  Set "Pass input" to `to stdin`.
5.  Paste the correct command to launch the included script:
    ```bash
    /Users/antony/Documents/Projects/MacDictate/run_mac_dictate.sh
    ```
    *Note: Edit `run_mac_dictate.sh` if your python path or project location changes.*

6.  Save the application (e.g., "MacDictate").
7.  (Optional) Add it to **System Settings > General > Login Items** to start on boot.
