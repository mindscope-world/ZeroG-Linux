# 🛰️ ZeroG for Linux (Ubuntu 24.04)
> Inspired by [ZeroG](https://github.com/antonynjoro/ZeroG)

### "The voice typing tool so good, you'll forget how to type."

Welcome to the Linux sector. This version of ZeroG has been specifically refitted for **Ubuntu 24.04 (Noble)**, replacing Apple Silicon dependencies with a robust **PyQt6 GUI** and **Faster-Whisper** optimized for Intel i7 hardware.

## Acknowledgement

This project is a Linux adaptation of **ZeroG**, originally developed for macOS by **Antony Njoro**.
All core ideas, architecture, and the original implementation credit go to the original author.

Original repository:
[https://github.com/antonynjoro/ZeroG](https://github.com/antonynjoro/ZeroG)

This fork focuses on rebuilding, refactoring, and extending the application to run natively on Linux while preserving the original vision and functionality. Any modifications are made with respect to the original work.

---

## 🚀 Flight Systems (Linux Refit)

* **Engine:** Powered by `Faster-Whisper` using `float32` compute for maximum stability on Intel Iris Xe and mobile CPUs.
* **Sensors:** Features a **Stay-on-Top HUD** to bypass Wayland/X11 keyboard permission conflicts.
* **Thrusters:** Text injection handled via `xdotool` for universal compatibility across Linux applications (Browsers, IDEs, Slack).
* **Telemetry:** Launched in **Unbuffered Mode** (`python3 -u`) to provide real-time terminal diagnostics.

---

## 🛠️ Pre-Flight Check (Installation)

### Prerequisites

* **Ubuntu 24.04 LTS** (Noble Tahr)
* **Python 3.12+**
* **X11 Session** (Recommended for `xdotool` reliability)

### 1. Board the Ship

```bash
git clone https://github.com/antonynjoro/MacDictate.git
cd MacDictate

```

### 2. Ignition (System Dependencies)

Ubuntu 24.04 requires specific Mesa and X11 utilities to handle AI model processing and window management. Run the following:

```bash
sudo apt update
sudo apt install -y libosmesa6 libgl1 mesa-utils xdotool python3-tk

```

### 3. Virtual Environment Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install numpy sounddevice faster-whisper pyperclip PyQt6

```

---

## 🛫 Takeoff

To launch ZeroG with full terminal telemetry:

```bash
chmod +x run_zerog.sh
./run_zerog.sh

```

### Flight Controls

* **Start Recording:** Click the **🔴 Start Recording** button. The HUD will stay on top of your other windows.
* **Stop Recording:** Click the **⏹️ Stop Recording** button.
* **Processing:** ZeroG will transcribe your voice using the `tiny` model for near-instant results on your i7 processor.
* **Injection:** ZeroG automatically copies the text and uses `xdotool` to paste (Ctrl+V) into your active window.

---

## 🕹️ Configuration

Adjust the system via `zerog/core/recorder.py`:

* **Model Size:** Set to `tiny` for speed or `base` for higher accuracy.
* **Compute Type:** Set to `float32` for Intel CPU stability or `int8` for lower RAM usage.

---

## ⚠️ Turbulence (Troubleshooting)

### Status: Processing (Hanging)

Your 11th Gen i7 requires the **OSMesa** libraries to prevent the AI engine from hanging. Ensure you have run:
`sudo apt install libosmesa6 libgl1`

### No Text Injected

If the terminal shows a transcription but nothing appears in your app:

1. Ensure `xdotool` is installed: `sudo apt install xdotool`.
2. If you are on **Wayland**, `xdotool` may be restricted. At the Ubuntu login screen, click the gear icon and select **"Ubuntu on Xorg"**.

### No Logs in Terminal

The app is designed to run in **Unbuffered Mode**. Ensure you are launching via `./run_zerog.sh` which uses the `python3 -u` flag.

---

## 🧪 R&D (Diagnostics)

To verify your hardware is compatible with the AI engine without launching the GUI:

```bash
python3 debug_model.py

```

*If this returns "ALL SYSTEMS GO," your hardware and drivers are correctly configured.*

**ZeroG: Don't let gravity hold back your thoughts.**

---

**Would you like me to help you create a `.desktop` file so you can launch ZeroG directly from your Ubuntu app drawer?**