# 🎙️ MacDictate

**Local, lightning-fast dictation for macOS.**

MacDictate brings the power of **Apple Silicon optimized AI** to your fingertips via a native, unintrusive HUD.

- **Core Transcription**: Uses [mlx-whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper) for private, **on-device** transcription.
- **Optional Editing**: Use the **Gemini integration** for cloud-powered text polishing.
- **Native Experience**: A lightweight macOS Menu Bar app with a beautiful "Glass" HUD.

![MacDictate HUD](./Mac_Dictate%20_Logo.png)

---

## ✨ Features

- **🚀 Speed**: Leverages MLX for near-instant transcription on M-series chips.
- **🔒 Privacy First**: By default, everything stays on your Mac. Audio is processed locally. (Optional Gemini editing uses the cloud).
- **⌨️ Universal Hotkey**: Hold `Left Control` to talk in *any* application.
- **🧠 Smart Formatting**: (Optional) Hold `Control + Q` to have Gemini clean up your grammar and formatting.
- **💎 Native UI**: Floating "Glass" HUD that stays out of your way and pulses when listening.

---

## 🛠️ Installation & Setup

### Prerequisites
- macOS 12+ (Apple Silicon recommended)
- Python 3.11+
- [Git](https://git-scm.com/)

### 1. Clone & Install
```bash
git clone https://github.com/antonynjoro/MacDictate.git
cd MacDictate
./setup.sh
```

### 2. Permissions
When you first run the app, macOS will ask for:
- **Microphone**: To hear your voice.
- **Accessibility**: To detect the key press (Left Control).
- **System Events**: To inject the transcribed text.

### 3. Usage
Run the app:
```bash
python main.py
```
You will see a microphone icon in your Menu Bar.
- **Talk**: Hold `Left Control`. The HUD will appear. Speak. Release to transcribe.
- **Talk + Polish**: Hold `Left Control + Q`. Speak. Release.

### 4. Create an Automator App
To run MacDictate as a standalone app without opening a terminal:

1. Open **Automator** and create a new **Application**.
2. Add a **Run Shell Script** action.
3. Paste the following code (update `PROJECT_DIR` if you moved the folder):

```bash
# Path to your MacDictate project
PROJECT_DIR="/Users/antony/Documents/Projects/MacDictate"

# 1. Stop any existing instance
pkill -f "main.py" || true
sleep 0.5

# 2. Go to directory
cd "$PROJECT_DIR"

# 3. Launch quietly in background
nohup ./.venv/bin/python main.py >/dev/null 2>&1 &
```

4. Save the app as **MacDictate**.
5. (Optional) Add it to **System Settings > General > Login Items** to start on boot.

---

## ⚙️ Configuration

MacDictate manages configuration via Environment Variables.

### Logging
By default, logging is **DISABLED** for privacy and performance.
To enable logging (for development):
1. Create a `.env` file in the root directory.
2. Add: `DEBUG=True`
3. Restart the app. Logs will appear in console.

### Gemini API (Optional)
To use the "Smart Formatting" feature:
1. Get a Key from [Google AI Studio](https://aistudio.google.com/).
2. Add to `.env`: `GOOGLE_API_KEY=your_key_here`

---

## ❓ Troubleshooting

### Permissions Issues
If the app runs but doesn't paste text or listen:

1. **Accessibility (Text Pasting fails)**
   - Go to **System Settings > Privacy & Security > Accessibility**.
   - If `MacDictate` (or your terminal/Python) is listed, select it and click the **minus (-)** button to remove it.
   - Run the app again. macOS will prompt you to re-add it.
   - *Why?* Sometimes macOS updates invalidate old permission entries.

2. **Microphone (No audio)**
   - Go to **System Settings > Privacy & Security > Microphone**.
   - Remove `MacDictate` (or Terminal/Python) and restart the app to re-trigger the permission prompt.

3. **System Events (Automation)**
   - This control is located in **System Settings > Privacy & Security > Automation**.
   - Ensure `MacDictate` has access to `System Events`.

---

## 🧪 Development

### Running Tests
We use `pytest` for unit testing.
```bash
# Run all tests
python -m pytest tests/

# Check coverage
python -m pytest --cov=macdictate tests/
```

### Project Structure
- `macdictate/core`: Business logic (State machine, Recorder, Key monitoring).
- `macdictate/gui`: UI code (Menu bar, HUD) using `PyObjC`.
- `tests/`: Unit and integration tests.

---

## 📅 Change Log

### [v0.8.0] - 2026-01-02
- **Universal Text Injection**: A massive upgrade to compatibility.
    - **FastTyper**: Uses low-level `CGEvent` to simulate hardware typing for instant, universal compatibility (works in Chrome, Terminal, VS Code, etc.).
    - **Clipboard Safety**: New `ClipboardManager` snapshots and restores your clipboard content, so dictating doesn't overwrite your copied images or files.
    - **Tiered Logic**: Automatically switches between Instant Typing (short text) and Safe Paste (long text) for the best performance.
- **Robustness**:
    - Removed reliance on flaky Accessibility APIs for text insertion.
    - Added comprehensive unit tests for core injection logic.
    - Enhanced debug logging for easier troubleshooting.

### [v0.7.0] - 2026-01-02
- **"Liquid Orbit" HUD**: Complete visual overhaul using a modern web-based rendering engine.
    - **Audio Visualization**: Real-time, thread-safe audio glow that pulses organically with your voice.
    - **Smooth Animations**: "Attack/Release" smoothing (120ms/600ms) for a premium, liquid feel.
    - **States**: Distinct visual identities for Recording (Cyan), Processing (Indigo), Success (Green), and Error (Red).
- **Manual Controls**: Added a clickable **Stop (■)** button to the HUD for handling long or stuck recordings.
- **Robustness**: 
    - Fixed threading issues that previously caused UI freezes.
    - Implemented a robust JS-to-Python bridge for reliable state management.

### [v0.6.0] - 2026-01-02
- **Performance Optimization**: Significant reduction in recording latency via audio stream and sound effect warmups.
- **Visual Enhancements**:
    - New **Waveform Visualization** in the HUD during recording.
    - Improved **Heads-Up Display** with slide animations and repositioned layout.
- **Reliability & Accuracy**:
    - Migrated to `google.genai` for more robust cloud-powered editing.
    - Optimized transcription pipeline for faster turnaround on short phrases.
    - Added extensive logging and diagnostic tools for performance monitoring.
- **Developer Experience**: Improved test coverage for state machine and audio broadcasting logic.

### [v0.5.0] - 2025-12-29
- **Major Architecture Overhaul**: Refactored into a modular package (`macdictate`) with Native App structure.
- **New UI**: Replaced basic transparent window with a **Native Glass HUD** using `NSVisualEffectView`.
    - Added "Pulse" animations for Recording (Red) and Processing (Blue).
    - Compact 180x44 design positioned above the Dock.
- **Native Audio**: Switched from `afplay` to `NSSound` for reliable, low-latency audio cues ("Pop" sound).
- **Security**: Implemented Environment-based configuration. Logging is now strictly opt-in via `DEBUG=True`.
- **Testing**: Added comprehensive unit tests for State Machine and Input Monitor (90% coverage).

### [v0.1.0] - 2025-12-01
- Initial Release.
- Background script approach.
- MLX Whisper integration.

---
*Developed with ❤️ for Mac users who hate typing.*
