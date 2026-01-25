#!/bin/bash

current_dir=$(pwd)
IMAGE_DIR="${current_dir}/image"
# echo $IMAGE_DIR
output="output"

if [ ! -f "file.json" ]; then
    python -m speciesnet.scripts.run_model --folders "image" --predictions_json "file.json"
fi

echo 
echo 
echo 
echo 

python adapt_json.py file.json

# exit 0 

python -m megadetector.visualization.visualize_detector_output "adapted_file.json" ${output} --images_dir "${IMAGE_DIR}"
