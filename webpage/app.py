import os
from flask import Flask, request, render_template, redirect, url_for
import pandas as pd

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# Store file information
uploaded_files = []

# Index page
@app.route('/')
def upload_form():
    return render_template('index.html', files_uploaded=len(uploaded_files) > 0)

# Upload endpoint
@app.route('/upload', methods=['POST'])
def upload_files():
    rawcounts_file = request.files['rawcounts']
    metafile = request.files['metafile']
    gene_name = request.form['gene']

    # Save uploaded files if needed
    # Example: save to 'uploads/' folder
    rawcounts_file.save(os.path.join(app.config['UPLOAD_FOLDER'], rawcounts_file.filename))
    metafile.save(os.path.join(app.config['UPLOAD_FOLDER'], metafile.filename))

    # Update uploaded_files list (can store filenames, etc.)
    uploaded_files.append((rawcounts_file.filename, metafile.filename, gene_name))

    # Redirect to a new route where upload box is hidden
    return redirect(url_for('input_response'))

# Route to input_response after upload
@app.route('/input_response')
def input_response():
   return render_template('input_response.html', files_uploaded=len(uploaded_files) > 0)


@app.route('/scatter_plot')
def scatter_plot():
    global uploaded_files  # Use global to ensure access outside this function scope

    if not uploaded_files:
        return "No files uploaded yet"
    
    # To get the most recent file
    file_info = uploaded_files[-1]
    raw_counts_path = os.path.join(app.config['UPLOAD_FOLDER'], file_info[0])
    meta_data_path = os.path.join(app.config['UPLOAD_FOLDER'], file_info[1])
    
    raw_counts_df = pd.read_csv(raw_counts_path)
    meta_data_df = pd.read_csv(meta_data_path)

    # Convert DataFrame to a list of dictionaries
    raw_counts_data = raw_counts_df.to_dict(orient='records')
    meta_data_df = meta_data_df.to_dict(orient='records')

    # Pass data to the template
    return render_template('scatter_plot.html', raw_counts=raw_counts_data, meta_data=meta_data_df)


if __name__ == '__main__':
    app.run(debug=True)
