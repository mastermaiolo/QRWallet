import os
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

capsules = [
    {
        'file': '/home/maggio/Projectos/QRWallet/photos/photo_1_2026-10-08_21-18-47.jpg',
        'cx': 986, 'cy': 1342, 'w': 860, 'h': 1790,
    },
    {
        'file': '/home/maggio/Projectos/QRWallet/photos/photo_2_2026-10-08_21-18-47.jpg',
        'cx': 898, 'cy': 1350, 'w': 842, 'h': 1775,
    },
    {
        'file': '/home/maggio/Projectos/QRWallet/photos/photo_3_2026-10-08_21-18-47.jpg',
        'cx': 880, 'cy': 1326, 'w': 765, 'h': 1585,
    }
]

# Standardized output size
CANVAS_W = 400
CANVAS_H = 820
TARGET_WATCH_W = 340
TARGET_WATCH_H = 710

normalized_frames = []

for idx, cap in enumerate(capsules):
    im = Image.open(cap['file']).convert('RGBA')
    cx, cy, w, h = cap['cx'], cap['cy'], cap['w'], cap['h']
    
    # Pill mask
    mask = Image.new('L', im.size, 0)
    draw = ImageDraw.Draw(mask)
    box = (cx - w/2, cy - h/2, cx + w/2, cy + h/2)
    draw.rounded_rectangle(box, radius=w/2, fill=255)
    
    # Slight feathering on the bezel rim
    mask_blurred = mask.filter(ImageFilter.GaussianBlur(3))
    
    # Mask out table
    isolated = Image.new('RGBA', im.size, (0, 0, 0, 0))
    isolated.paste(im, (0, 0), mask_blurred)
    
    # Crop tightly to capsule
    cropped = isolated.crop((int(cx - w/2), int(cy - h/2), int(cx + w/2), int(cy + h/2)))
    
    # Resize to exact target watch size using LANCZOS
    resized = cropped.resize((TARGET_WATCH_W, TARGET_WATCH_H), Image.Resampling.LANCZOS)
    
    # Place on canvas (centered)
    canvas = Image.new('RGBA', (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    # Add a subtle dark OLED-style shadow/glow for realism against white/dark GitHub themes
    glow = Image.new('RGBA', (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    paste_x = (CANVAS_W - TARGET_WATCH_W) // 2
    paste_y = (CANVAS_H - TARGET_WATCH_H) // 2
    glow_box = (paste_x - 4, paste_y - 4, paste_x + TARGET_WATCH_W + 4, paste_y + TARGET_WATCH_H + 4)
    glow_draw.rounded_rectangle(glow_box, radius=TARGET_WATCH_W/2, fill=(0, 0, 0, 160))
    glow_blurred = glow.filter(ImageFilter.GaussianBlur(8))
    
    canvas = Image.alpha_composite(canvas, glow_blurred)
    canvas.paste(resized, (paste_x, paste_y), resized)
    
    normalized_frames.append(canvas)
    canvas.save(f'/home/maggio/Projectos/QRWallet/photos/frame_{idx+1}.png')

print("Generating GIF with smooth transitions...")

# Build frames with cross-fading
# Durations list in milliseconds
all_frames = []
durations = []

def cross_fade(f1, f2, steps=6, step_dur=35):
    f_arr1 = np.array(f1, dtype=float)
    f_arr2 = np.array(f2, dtype=float)
    frames = []
    for s in range(1, steps):
        alpha = s / float(steps)
        blended = (1.0 - alpha) * f_arr1 + alpha * f_arr2
        frames.append(Image.fromarray(np.uint8(blended), 'RGBA'))
    return frames

# Frame 1: App drawer
all_frames.append(normalized_frames[0])
durations.append(1800)

# Transition 1 -> 2
t1 = cross_fade(normalized_frames[0], normalized_frames[1], steps=5, step_dur=40)
all_frames.extend(t1)
durations.extend([40] * len(t1))

# Frame 2: Shortcut menu
all_frames.append(normalized_frames[1])
durations.append(2200)

# Transition 2 -> 3
t2 = cross_fade(normalized_frames[1], normalized_frames[2], steps=5, step_dur=40)
all_frames.extend(t2)
durations.extend([40] * len(t2))

# Frame 3: QR Code
all_frames.append(normalized_frames[2])
durations.append(2500)

# Transition 3 -> 1
t3 = cross_fade(normalized_frames[2], normalized_frames[0], steps=5, step_dur=40)
all_frames.extend(t3)
durations.extend([40] * len(t3))

# Save GIF
# For best compatibility on GitHub, save transparent or dark background GIF
# Let's create both: transparent GIF and dark background GIF (#0B0D0F matching MAIOLO README)
gif_path = '/home/maggio/Projectos/QRWallet/photos/qrwallet_band_preview.gif'
rgb_frames = []
for f in all_frames:
    # Blend onto #050505 background (pure dark editorial canvas)
    bg = Image.new('RGB', (CANVAS_W, CANVAS_H), (5, 5, 5))
    bg.paste(f, (0, 0), f)
    rgb_frames.append(bg.convert('P', palette=Image.Palette.ADAPTIVE, colors=256))

rgb_frames[0].save(
    gif_path,
    save_all=True,
    append_images=rgb_frames[1:],
    duration=durations,
    loop=0,
    optimize=True
)

print(f"GIF saved to {gif_path}, size: {os.path.getsize(gif_path) / 1024:.1f} KB")

# Also copy to assets/readme/ so it can be directly embedded in GitHub README
readme_asset = '/home/maggio/Projectos/QRWallet/assets/readme/qrwallet-live-demo.gif'
import shutil
shutil.copyfile(gif_path, readme_asset)
print(f"Copied to {readme_asset}")
