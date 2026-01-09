from pynput import keyboard

def on_press(key):
    print(f"Key Pressed: {key}")

def on_release(key):
    if key == keyboard.Key.esc:
        return False

print("Listening... Press 'Ctrl' or any key. Press 'Esc' to stop.")
with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()