# MacDictate

A local macOS dictation app using **MLX Whisper** for fast, private, on-device transcription on Apple Silicon.

## Features
- **Local Transcription**: Uses `mlx-whisper` (Apple Silicon optimized).
- **Global Hotkey**: **Hold** `Left Control` to record.
- **Audio Feedback**: Plays a confirmation sound (configurable).
- **Background Service**: Ready for macOS Automator integration.

## Permissions & Privacy

MacDictate is a local-only application. Audio data never leaves your device.
- **Microphone**: Required to listen to your dictation.
- **Accessibility**: Required to read the global hotkey (`Left Control`).
- **Automation (System Events)**: Required to paste text into other applications.

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
- **Logging**: Set `ENABLE_LOGGING = True` to write debug logs to `mac_dictate.log`.

## Usage

### Manual Run
```bash
python main.py
```
- **Dictate**: **Hold** `Left Control` to start recording. **Release** to stop and transcribe.
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
