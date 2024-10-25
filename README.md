# co_po_matrix_generator
upload your syllabus in text format with co's, a co-po mapping matrix will be generated. even you can adjust the threshold of similarity for mapping co with po
Here are the step-by-step instructions to deploy this application on your local machine:

Prerequisites:

Install Python 3.7 or higher from https://www.python.org/downloads/
Verify installation by running: python --version
Download the Project:

Download all project files to your local machine
Keep the folder structure intact
Setup Environment:

Open terminal/command prompt
Navigate to project folder: cd path/to/project
Install dependencies using: pip install -r requirements.txt
This will install: streamlit, pandas, spacy, and required models
Run the Application:

In the project directory, run: streamlit run main.py
The application will automatically open in your default web browser
If it doesn't open automatically, visit: http://localhost:8501
Using the Application:

Upload your syllabus text files
Adjust similarity threshold using the slider
Download generated matrices as CSV files
Common Issues:

If spaCy model fails to load, run: python -m spacy download en_core_web_sm
Make sure all files (main.py, utils/, data/, assets/) are in their correct locations
Would you like any clarification on any of these steps?
