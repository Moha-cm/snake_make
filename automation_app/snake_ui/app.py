import os
from flask import Flask, request, render_template, send_file
import subprocess
import pandas as pd

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def upload_form():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    param = request.form['param']  # Get the string parameter from the form
    if file.filename == '':
        return 'No selected file'
    if file and file.filename.endswith('.csv'):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        # Update the config.yaml file with uploaded file and string parameter
        with open('config.yaml', 'w') as config_file:
            config_file.write(f"uploaded_csv: '{file_path}'\n")
            config_file.write(f"param: '{param}'\n")

        # Adjust the environment and run Snakemake with Conda
        try:
            subprocess.run(['snakemake', '--cores', '1', '--use-conda'], check=True)
        except subprocess.CalledProcessError as e:
            return f"Error running Snakemake: {e}"

        # Load the processed CSV file into a DataFrame
        output_csv_path = 'results/final_output.csv'
        df = pd.read_csv(output_csv_path)

        # Render a new template to display the CSV file in a table
        return render_template('output.html', tables=[df.to_html(classes='data', header="true")])
    else:
        return 'Invalid file format. Please upload a CSV file.'

if __name__ == '__main__':
    app.run(debug=True)
