import sys 
from PIL import Image
import json


def main():
    # img = Image.open("mouse.jpg").convert("RGB")
    # img.save("TEMP.PNG")
    # pixels = list(img.getdata())

    # # Write raw binary bytes instead of hex strings
    # raw_bytes = bytes([val for r, g, b in pixels for val in (r, g, b)])

    # with open("output_.txt", "wb") as f:  # Note: "wb" for binary write
    #     f.write(raw_bytes)

    # with open("properties.json", "w") as f:
    #     json.dump({"width": img.width, "height": img.height}, f)

    with open("mouse.jpg", "rb") as f:
        image_buffer = f.read()

    image_buffer = " ".join(f"{b:02x}" for b in image_buffer)

    with open("mouse.txt",'w') as f:
        f.write(image_buffer)


if __name__ == "__main__":
    main()