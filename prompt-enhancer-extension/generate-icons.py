#!/usr/bin/env python3
# Generate PNG icons for Chrome extension

from PIL import Image, ImageDraw, ImageFont
import os

# Create icons directory if it doesn't exist
icons_dir = 'icons'
if not os.path.exists(icons_dir):
    os.makedirs(icons_dir)

def create_icon(size):
    # Create image with gradient-like background
    img = Image.new('RGB', (size, size), color='#764ba2')
    draw = ImageDraw.Draw(img)
    
    # Draw rounded rectangle background
    draw.rectangle([0, 0, size, size], fill='#667eea')
    
    # Add a simple gradient effect
    for i in range(size):
        color_value = int(102 + (118-102) * i / size)  # Gradient from #667eea to #764ba2
        draw.line([(i, 0), (i, size)], fill=(color_value, 126, 234 - int(114 * i / size)))
    
    # Add sparkles emoji or text
    try:
        # Try to get a font
        font_size = int(size * 0.6)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        # Use default font if truetype not available
        font = ImageFont.load_default()
    
    # Draw text (sparkles emoji or "PE")
    text = "✨"
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except:
        text_width = size * 0.6
        text_height = size * 0.6
    
    x = (size - text_width) / 2
    y = (size - text_height) / 2
    
    try:
        draw.text((x, y), text, fill='white', font=font)
    except:
        # Fallback to "PE" if emoji fails
        text = "PE"
        draw.text((size * 0.2, size * 0.3), text, fill='white', font=font)
    
    # Save PNG
    output_path = os.path.join(icons_dir, f'icon{size}.png')
    img.save(output_path, 'PNG')
    print(f'✓ Created {output_path}')

# Generate icons
sizes = [16, 48, 128]
for size in sizes:
    create_icon(size)

print('\n✓ All PNG icons generated successfully!')
