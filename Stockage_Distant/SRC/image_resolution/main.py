from PIL import Image
import utils
import os
import sys
import numpy as np

def main():
    # Ground truth label
    true_label = "north american river otter"

    # Load original image
    img = Image.open("example.jpeg")
    base_height, base_width = img.size
    print(f"Original resolution = {base_width}x{base_height}")
    temp_file = os.path.join('temp',"resized.jpg")

    resolution = []
    resolution.append(np.linspace(start=base_width, stop=100, num=4, dtype=int).tolist())
    resolution.append(list(range(100,10,-10)))
    resolution = list(utils.flatten(resolution))
    resolution = list(set(resolution))
    resolution.sort(reverse=True)

    print(resolution)

    # Test progressively smaller sizes
    for width in resolution:
        new_height = (width * base_height) // base_width
        resized = img.resize((new_height,width))
        print(f"Resizing to {width}x{new_height}")
        # resized.show()
        
        resized.save(temp_file)

        prediction = utils.predict_species(temp_file)

        # try:
        #     input("Press Enter to continue...")
        # except KeyboardInterrupt:
        #     sys.exit(0)
        # continue
    
        print(f"Resolution={width}x{new_height} → Predicted: {prediction}")

        if prediction != true_label:
            print(f"❌ Model failed at {width}x{new_height}")
            print(f"✅ Minimum usable resolution = {(width + 100)}x{((width + 100) * base_height) // base_width}")
            break

if __name__ == "__main__":
    main()
