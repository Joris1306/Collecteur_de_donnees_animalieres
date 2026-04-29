#!/bin/bash
# Launch the application using the Python 3.12 environment with SpeciesNet AI support

cd "$(dirname "$0")"

# Activate the SpeciesNet-enabled venv
source .venv-speciesnet/bin/activate

# Export environment variables to ensure logging and AI are enabled
export PYTHONUNBUFFERED=1
export FLASK_APP=app.py
export FLASK_ENV=development

# Run the application
python app.py
