from PIL import Image, ImageEnhance
import sys
import math
import json
import os
import io

BASE = os.path.dirname(__file__)
INPUT_TXT = os.path.join(BASE,"stream.txt")
INPUT_JPEG = os.path.join(BASE,"stream.txt")
OUTPUT_IMAGE = os.path.join(BASE,"output.png")
JSON_PROPERTIES = os.path.join(BASE,"properties.json")
CIBLE_IMAGE = os.path.join(BASE,"CIBLE.PNG")

def namestr(obj, namespace = globals()):
    _list = [name for name in namespace if namespace[name] is obj]
    if len(_list) == 1:
        return _list[0]
    else:
        return _list

def debug(var):
    print(f"{namestr(var)} = {var}")

def bytes_from_file(filename):
    with open(filename, 'rb') as f:
        hex_bytes = bytes(f.read())
    return hex_bytes
    
def img_from_bytes(src_bytes = INPUT_TXT):

    width = json.load(open(JSON_PROPERTIES))["width"]
    height = json.load(open(JSON_PROPERTIES))["height"]
    _bytes = bytes_from_file(src_bytes)

    mode = "RGB"
    
    try:
        imtest = Image.frombytes(mode=mode, size=(width, height), data=_bytes)
        return imtest
    except Exception as e:
        print(f"Error: {e}")
        print(f"_bytes = {_bytes}")
        print(f"len(_bytes)//3 = {len(_bytes)//3}")
        print(f"math.sqrt(len(_bytes)//3) = {math.sqrt(len(_bytes)//3)}")
        sys.exit(0)

def apply_adaptive_filter(img):
    """
    Applies an adaptive filter to correct the new Orange/Red color bias.
    The goal is to reduce Red and boost Green/Blue to achieve the target brown/tan palette.
    """
    
    # Load the pixel data
    pixels = img.load()
    width, height = img.size
    
    for x in range(width):
        for y in range(height):
            r, g, b = pixels[x, y]
            
            # Normalize R/G/B (0.0 to 1.0)
            r_norm = r / 255.0
            g_norm = g / 255.0
            b_norm = b / 255.0
            
            # --- Custom Color Mapping Formula for Orange Bias ---
            # 1. Reduce Red channel aggressively (gamma > 1.0 or high power)
            # 2. Boost Green and Blue channels (gamma < 1.0 or low power)
            
            # Example values to shift orange/red to brown/tan:
            # Dampen Red (e.g., power of 1.2 or 1.3)
            new_r = int(255 * (r_norm**1.1)) 
            
            # Boost Green (e.g., power of 0.8)
            new_g = int(255 * (g_norm**1.1 * 1.1)) 
            
            # Boost Blue (e.g., power of 0.9)
            new_b = int(255 * (b_norm**0.4)) 
            
            # Clamp values to 0-255
            final_r = max(0, min(255, new_r))
            final_g = max(0, min(255, new_g))
            final_b = max(0, min(255, new_b))
            
            pixels[x, y] = (final_r, final_g, final_b)

    # 2. Final Contrast Polish (helps define the pixel edges better)
    enhancer = ImageEnhance.Contrast(img)
    final_img = enhancer.enhance(1.1) # Small contrast boost
    
    return final_img

def levels_adjustment_filter(img):
    """
    Applies a linear levels adjustment (color scaling) where R=94, G=104, B=114
    is mapped to R=255, G=255, B=255.
    """
    # Target input color to be mapped to 255
    _current = (110, 134, 98)
    _target = (70, 87, 79)
    R_target_in = _current[0]
    G_target_in = _current[1]
    B_target_in = _current[2]
    
    # Calculate scaling factors
    S_R = _target[0] / R_target_in
    S_G = _target[1] / G_target_in
    S_B = _target[2] / B_target_in
    
    # Convert to RGB if not already
    img = img.convert("RGB")
    
    # Load the pixel data for direct manipulation
    pixels = img.load()
    width, height = img.size
    
    # Apply the scaling transformation
    for x in range(width):
        for y in range(height):
            r, g, b = pixels[x, y]
            
            # Apply scaling and clamp at 255 (full white)
            new_r = min(255, int(r * S_R))
            new_g = min(255, int(g * S_G))
            new_b = min(255, int(b * S_B))
            
            pixels[x, y] = (new_r, new_g, new_b)

        # pixel = img.getpixel((0, 0))
        # print(pixel)
        # print(f"decount = {decount}")
        # input("Press Enter to continue...")
        # if pixel[0] == 255 and pixel[1] == 255 and pixel[2] == 255:
        #     break
        # else:
        #     decount -= 1

    return img

def img_from_jpeg_buff(filename):
    with open(filename, "r") as f:
        hex_string = f.read()
    # print(hex_string)
    hex_string = hex_string.replace(" ", "")

    hex_bytes = bytes.fromhex(hex_string)

    image = Image.open(io.BytesIO(hex_bytes))
    
    return image

def main():
    # img = levels_adjustment_filter(img_from_bytes())

    # img = img_from_bytes(INPUT_TXT)
    img = levels_adjustment_filter(img_from_jpeg_buff(INPUT_JPEG))
    # img = img_from_jpeg_buff(INPUT_JPEG)
    cible = Image.open(CIBLE_IMAGE).convert("RGB")

    pixel_img = img.getpixel((0, 0))
    pixel_cible = cible.getpixel((0, 0))

    print(f"_current = {pixel_img}\n_target = {pixel_cible}")

    # img.show()
    img.save(OUTPUT_IMAGE)

if __name__ == '__main__':
    main()