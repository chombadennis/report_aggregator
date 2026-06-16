import os
from PIL import Image, ImageDraw

def crop_circle_exact(image_path, output_path):
    img = Image.open(image_path).convert("RGBA")
    width, height = img.size
    print(f"Original image size: {width}x{height}")
    
    # Crop to the exact circular boundaries
    left, top, right, bottom = 138, 383, 888, 1134
    print(f"Cropping exact logo bounds: left={left}, top={top}, right={right}, bottom={bottom}")
    cropped = img.crop((left, top, right, bottom))
    
    # Resize to square
    size = 750
    # Use LANCZOS for resizing
    cropped = cropped.resize((size, size), Image.Resampling.LANCZOS)
    
    # Create circular mask
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    
    # Apply mask
    cropped.putalpha(mask)
    
    # Save as PNG
    cropped.save(output_path, "PNG")
    print(f"Saved exact circular masked logo to {output_path}")

if __name__ == "__main__":
    logo_in = "../frontend/public/neuralaxis-logo.png"
    logo_out = "../frontend/public/neuralaxis-logo-circular.png"
    crop_circle_exact(logo_in, logo_out)
