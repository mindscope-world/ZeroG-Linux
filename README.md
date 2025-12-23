# 🎙️ MacDictate

**Local, lightning-fast dictation for macOS.** 

MacDictate brings the power of **Apple Silicon optimized AI** to your fingertips. 

- **Core Transcription**: Uses `mlx-whisper` for private, **on-device** transcription.
- **Optional Editing**: Use the **Gemini integration** for cloud-powered text polishing.

---

## ✨ Features

- **🚀 Speed**: Leverages MLX for near-instant transcription on M-series chips.
- **🔒 Privacy First**: By default, everything stays on your Mac. Audio is processed locally. (Optional Gemini editing uses the cloud).
- **⌨️ Universal Hotkey**: Hold `Left Control` to talk in *any* application.
- **🧠 Smart Formatting**: (Optional) Hold `Control + Q` to have Gemini clean up your grammar and formatting for Slack-style perfection.

---

## 🛡️ Privacy & Logging

**Your privacy is the top priority.**

- **On-Device (Default)**: Audio recorded for Whisper never leaves your computer. The transcription is performed entirely by your Mac's own processor.
- **Cloud-Based (Optional)**: If you possess a Google API key and choose to use the **Gemini feature** (by holding `Q`), the transcribed *text* (not the audio) is sent to Google's servers for processing.
- **Logging is OFF by default**: By default, MacDictate does not save any transcriptions or audio logs.
- **Local-Only Logging**: If you manually enable `ENABLE_LOGGING` in [main.py](file:///Users/antony/Documents/Projects/MacDictate/main.py) for troubleshooting, status messages and transcriptions will be saved to a local file named [mac_dictate.log](file:///Users/antony/Documents/Projects/MacDictate/mac_dictate.log). 
- **⚠️ Important Warning**: This log file is stored **only on your machine**. However, it will contain the text of what you dictate. We recommend keeping logging disabled for daily use and only enabling it briefly for debugging.

---

## 🚀 Quick Start (Non-Technical Guide)

If you have a Mac and want to get started:

1.  **Open Terminal** (Found in Applications > Utilities).
2.  **Paste these commands** one by one:
    ```bash
    git clone https://github.com/yourusername/MacDictate.git
    cd MacDictate
    ./setup.sh  # (If you created a setup script, otherwise see below)
    ```
    *(If you don't have python, the app will guide you or you can install it via [python.org](https://python.org))*

3.  **Run the app**:
    ```bash
    python main.py
    ```
4.  **Try it out**: Open Notes or Slack, hold your `Left Control` key, say something, and let go!

---

## 🛠️ Installation & Setup

### Prerequisites
- macOS (Apple Silicon recommended)
- Python 3.11+

### 1. Clone & Install
```bash
git clone https://github.com/yourusername/MacDictate.git
cd MacDictate
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Permissions
When you first run the app, macOS will ask for:
- **Microphone**: To hear your voice.
- **Accessibility**: To detect the hotkey.
- **System Events**: To paste the text for you.

---

## ⚙️ Configuration

You can customize `main.py`:
- `SOUND_FILE`: Change the "Pop" sound to something else.
- `ENABLE_LOGGING`: Set to `True` only if you need to debug issues (see Privacy section).
- **Gemini Feature**: Note that holding `Q` will only work if a valid `GOOGLE_API_KEY` is found in your environment. If no key is found, the app will ignore the `Q` key and perform standard local-only transcription.

---

## 🤖 Advanced: Gemini AI Editing

If you have a Google Gemini API Key, you can enable "Super-Power" mode:
1. Rename [.env.example](file:///Users/antony/Documents/Projects/MacDictate/.env.example) to `.env`.
2. Open `.env` and add your `GOOGLE_API_KEY`.
3. While dictating, **hold the `Q` key** along with `Left Control`.
4. MacDictate will send the transcription to **Google Gemini** (Cloud) to perfectly format your speech into a clean message.

---

## 🏃 Run as a Background Service

Want it to start automatically?
1. Open **Automator** > New **Application**.
2. Add **Run Shell Script**.
3. Paste the path to `run_mac_dictate.sh`.
4. Add the resulting app to your **Login Items**.

## 🎨 Custom App Icon

Want MacDictate to look like a real app in your Dock or Launcher? We've included a high-quality logo: [Mac_Dictate _Logo.png](file:///Users/antony/Documents/Projects/MacDictate/Mac_Dictate%20_Logo.png).

**How to change the icon of your Automator App:**
1. Open [Mac_Dictate _Logo.png](file:///Users/antony/Documents/Projects/MacDictate/Mac_Dictate%20_Logo.png) in **Preview**.
2. Press `Command + A` (Select All) then `Command + C` (Copy).
3. Find your **MacDictate** application in Finder.
4. Right-click it and select **Get Info**.
5. Click the small icon in the **top-left corner** of the Info window (it should be highlighted with a blue border).
6. Press `Command + V` (Paste).

---
*Developed with ❤️ for Mac users who hate typing.*
