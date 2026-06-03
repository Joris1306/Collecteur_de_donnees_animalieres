import struct
from PIL import Image

width = 160
height = 120
filename = "E:\\img.raw"

# Lire le RAW
with open(filename, "rb") as f:
    raw = f.read()

img = Image.new("RGB", (width, height))
pixels = img.load()

for y in range(height):
    for x in range(width):
        i = (y * width + x) * 2
        # Lire deux octets
        val = struct.unpack_from("<H", raw, i)[0]  # little endian
        # Extraire RGB565
        r = ((val >> 11) & 0x1F) << 3
        g = ((val >> 5) & 0x3F) << 2
        b = (val & 0x1F) << 3
        pixels[x, y] = (r, g, b)

# Sauvegarder en BMP ou PNG
img.save("img.bmp")
print("Conversion terminée !")
