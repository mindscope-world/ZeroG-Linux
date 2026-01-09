import os
import urllib.request
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AssetGenerator")

# Icons from Lucide (Open Source) - Choosing sleek, minimalist designs
# We'll download the SVG versions and you can use them directly in PyQt6
ICONS = {
    "mic_idle.png": "https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/mic.svg",
    "mic_active.path": "https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/mic-2.svg",
    "processing.png": "https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/refresh-cw.svg",
    "success.png": "https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/check-circle-2.svg",
    "error.png": "https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/alert-triangle.svg"
}

def generate():
    asset_dir = os.path.join(os.getcwd(), "zerog", "assets")
    
    if not os.path.exists(asset_dir):
        os.makedirs(asset_dir)
        logger.info(f"Created directory: {asset_dir}")

    for filename, url in ICONS.items():
        filepath = os.path.join(asset_dir, filename)
        try:
            logger.info(f"Downloading {filename}...")
            urllib.request.urlretrieve(url, filepath)
        except Exception as e:
            logger.error(f"Failed to download {filename}: {e}")

    logger.info("✅ All assets localized. ZeroG is visual-ready.")

if __name__ == "__main__":
    generate()