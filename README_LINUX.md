# 🛰️ ZeroG for Linux (Ubuntu)

### "The voice typing tool so good, you'll forget how to type."

Welcome to the Linux sector. This version of ZeroG has been refitted to run on **Ubuntu (X11)**, replacing Apple Silicon dependencies with high-performance Linux alternatives like **Faster-Whisper** and **xdotool**.

---

## 🚀 Flight Systems (Linux Refit)

* **Engine:** Powered by `Faster-Whisper` with `int8` quantization for near-instant inference on both CPUs and NVIDIA GPUs.
* **Sensors:** Uses `pynput` for global hotkey detection via the Linux `input` group.
* **Thrusters:** Text injection handled via `xdotool` and `xclip` for universal compatibility across Linux applications.

---

## 🛠️ Pre-Flight Check (Installation)

### Prerequisites

* **Ubuntu 22.04+** (Recommended)
* **Python 3.10+**
* **X11 Session** (Standard Ubuntu. If using Wayland, see *Turbulence* below.)

### 1. Board the Ship

Clone the repository and enter the launchpad:

```bash
git clone https://github.com/antonynjoro/MacDictate.git
cd MacDictate

```

### 2. Ignition (Setup Script)

Run the automated Linux setup script. This will install system dependencies (`xdotool`, `xclip`), create your virtual environment, and set hardware permissions.

```bash
chmod +x setup_linux.sh
./setup_linux.sh

```

### 3. Clearance Codes (Permissions)

Linux requires your user to be part of specific hardware groups to access the keyboard and microphone without `root` privileges. **You must reboot your machine after the setup script finishes** for these changes to take effect:

* `input`: For detecting the **Left Control** hotkey.
* `audio`: For capturing your voice.

---

## 🛫 Takeoff

To launch ZeroG in the background:

```bash
chmod +x run_zerog.sh
./run_zerog.sh

```

### Flight Controls

* **Transmit:** Hold **Left Control**. Speak. Release to paste.
* **Auto-Pilot:** Press **Left Control** once. Speak. ZeroG will auto-detect silence and "cut the feed" to paste.
* **Gravity Assist (Gemini):** Hold **Left Control + Q**. Speak. Release to have Gemini format and professionalize your text.

---

## 🕹️ Configuration

The system uses a `.env` file for adjustments:

* `GOOGLE_API_KEY`: Add your key from Google AI Studio to enable Gemini thrusters.
* `DEBUG=True`: Enable this to see telemetry in `zerog.log`.

---

## ⚠️ Turbulence (Troubleshooting)

### Wayland Support

Ubuntu's default "Wayland" session has high security protocols that prevent global key-listening. If ZeroG doesn't respond to the Control key:

1. Log out of Ubuntu.
2. Click your name.
3. Click the **Gear Icon** in the bottom right corner.
4. Select **"Ubuntu on Xorg"**.
5. Log back in.

### No Text Injection

Ensure `xdotool` is functioning. ZeroG uses it to simulate `Ctrl+V`.

```bash
sudo apt install xdotool xclip

```

### Audio Hardware Lock

If the microphone isn't responding, check `pavucontrol` (PulseAudio Volume Control) to ensure the Python process has access to the correct input device.

---

## 🧪 R&D (Development)

To run simulation scenarios on Linux:

```bash
source .venv/bin/activate
python -m pytest tests/

```

**ZeroG: Don't let gravity hold back your thoughts.**


