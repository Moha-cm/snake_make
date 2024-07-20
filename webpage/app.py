import os
from flask import Flask, request, render_template, redirect, url_for
import pandas as pd
import plotly
import json
import plotly.express as px
import plotly.utils


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

    # Save uploaded files if needed
    # Example: save to 'uploads/' folder
    rawcounts_file.save(os.path.join(app.config['UPLOAD_FOLDER'], rawcounts_file.filename))
    metafile.save(os.path.join(app.config['UPLOAD_FOLDER'], metafile.filename))

    # Update uploaded_files list (can store filenames, etc.)
    uploaded_files.append((rawcounts_file.filename, metafile.filename))

    # Redirect to a new route where upload box is hidden
    return redirect(url_for('input_response'))

# Route to input_response after upload
@app.route('/input_response')
def input_response():
    global uploaded_files
    
    if not uploaded_files:
        return redirect(url_for('/upload'))
    else:
       

        def get_recent_files():
            if not uploaded_files:
                return None, None
            file_info = uploaded_files[-1]
            raw_counts_path = os.path.join(app.config['UPLOAD_FOLDER'], file_info[0])
            meta_data_path = os.path.join(app.config['UPLOAD_FOLDER'], file_info[1])
            return raw_counts_path, meta_data_path

        def read_data_files(raw_counts_path, meta_data_path):
            raw_counts_df = pd.read_csv(raw_counts_path)
            meta_data_df = pd.read_csv(meta_data_path)
            common_columns = [col for col in meta_data_df.columns if col in raw_counts_df.columns]
            return raw_counts_df, meta_data_df, common_columns

        raw_counts_path, meta_data_path = get_recent_files()
        if not raw_counts_path or not meta_data_path:
            return redirect(url_for('/upload'))
        
        raw_counts_df, meta_data_df, common_columns = read_data_files(raw_counts_path, meta_data_path)

        raw_counts_data = raw_counts_df.to_dict(orient='records')
        meta_data_data = meta_data_df.to_dict(orient='records')
        colnames_meta = list(meta_data_df.select_dtypes(exclude='number').columns)
        raw_counts_column = list(raw_counts_df.select_dtypes(exclude='number').columns)

        return render_template('input_response.html', raw_counts=raw_counts_data, meta_data=meta_data_data)



@app.route('/scatter_plot', methods=["GET", "POST"])
def scatter_plot():
    global uploaded_files

    def get_recent_files():
        if not uploaded_files:
            return None, None
        file_info = uploaded_files[-1]
        raw_counts_path = os.path.join(app.config['UPLOAD_FOLDER'], file_info[0])
        meta_data_path = os.path.join(app.config['UPLOAD_FOLDER'], file_info[1])
        return raw_counts_path, meta_data_path

    def read_data_files(raw_counts_path, meta_data_path):
        raw_counts_df = pd.read_csv(raw_counts_path)
        meta_data_df = pd.read_csv(meta_data_path)
        common_columns = [col for col in meta_data_df.columns if col in raw_counts_df.columns]
        return raw_counts_df, meta_data_df, common_columns

    raw_counts_path, meta_data_path = get_recent_files()
    if not raw_counts_path or not meta_data_path:
        return redirect(url_for('upload_form'))

    raw_counts_df, meta_data_df, common_columns = read_data_files(raw_counts_path, meta_data_path)
    colnames_meta = list(meta_data_df.select_dtypes(exclude='number').columns)
    raw_counts_column = list(raw_counts_df.select_dtypes(exclude='number').columns)

    if request.method == "POST":
        plot_x_axis = request.form.get('plot_x_axis')
        color_options = request.form.get('color_options')
        gene_name = request.form.get('gene')

        if not plot_x_axis or not color_options or not gene_name:
            return "All form fields are required.", 400

        gene_ids = pd.read_csv("ensembl_gene_ids.csv")
        filter_gene = gene_ids[gene_ids["Gene_name"] == gene_name]

        if filter_gene.empty:
            return "Gene not found.", 400
        
        filter_ensemble_version_id = filter_gene["ensembl_gene_id_version"].iloc[0]
        
        subset_columns = [plot_x_axis,filter_ensemble_version_id, color_options]

        dataset = pd.merge(meta_data_df, raw_counts_df, left_on=common_columns, right_on=common_columns)
        filter_dataset = dataset[subset_columns]
        filter_dataset.rename(columns={filter_ensemble_version_id: filter_gene["Gene_name"].iloc[0]}, inplace=True)
        filtered_gene = filter_gene["Gene_name"].iloc[0]
        fig = px.scatter(
            filter_dataset, 
            x=plot_x_axis, 
            y=filter_gene["Gene_name"].iloc[0],
            color=color_options,
            size=filter_gene["Gene_name"].iloc[0]
        )

        fig.update_layout(
            plot_bgcolor='white',
            title={
                'text': f"<b>{filtered_gene} Expression by {color_options.replace("_"," ").capitalize()}</b>",  # Make title bold
                'x': 0.5,  # Center the title
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {
                    'color': 'black'  # Change the font color to black
                }
            },
            xaxis={
                'showticklabels': False,  # Hide x-axis labels
                'showline': True,  # Show x-axis line
                'linecolor': 'black'  # Set x-axis border color to black
            },
            yaxis={
                'showticklabels': True,  # Show y-axis labels
                'showline': True,  # Show y-axis line
                'linecolor': 'black'  # Set y-axis border color to black
            })
       
        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        return render_template('scatter_plot.html', raw_counts=filter_dataset.to_dict(orient='records'), col_option=colnames_meta, exp_option=raw_counts_column, files_uploaded=True, graphJSON=graphJSON)

    return render_template('scatter_plot.html', col_option=colnames_meta, exp_option=raw_counts_column, files_uploaded=False)



@app.route('/box_plot', methods=["GET", "POST"])
def box_plot():
    global uploaded_files

    def get_recent_files():
        if not uploaded_files:
            return None, None
        file_info = uploaded_files[-1]
        raw_counts_path = os.path.join(app.config['UPLOAD_FOLDER'], file_info[0])
        meta_data_path = os.path.join(app.config['UPLOAD_FOLDER'], file_info[1])
        return raw_counts_path, meta_data_path

    def read_data_files(raw_counts_path, meta_data_path):
        raw_counts_df = pd.read_csv(raw_counts_path)
        meta_data_df = pd.read_csv(meta_data_path)
        common_columns = [col for col in meta_data_df.columns if col in raw_counts_df.columns]
        return raw_counts_df, meta_data_df, common_columns

    raw_counts_path, meta_data_path = get_recent_files()
    if not raw_counts_path or not meta_data_path:
        return redirect(url_for('upload_form'))

    raw_counts_df, meta_data_df, common_columns = read_data_files(raw_counts_path, meta_data_path)
    colnames_meta = list(meta_data_df.select_dtypes(exclude='number').columns)
    raw_counts_column = list(raw_counts_df.select_dtypes(exclude='number').columns)

    if request.method == "POST":
        plot_x_axis = request.form.get('plot_x_axis')
        color_options = request.form.get('color_options')
        gene_name = request.form.get('gene')

        if not plot_x_axis or not color_options or not gene_name:
            return "All form fields are required.", 400

        gene_ids = pd.read_csv("ensembl_gene_ids.csv")
        filter_gene = gene_ids[gene_ids["Gene_name"] == gene_name]

        if filter_gene.empty:
            return "Gene not found.", 400
        
        filter_ensemble_version_id = filter_gene["ensembl_gene_id_version"].iloc[0]
        
        subset_columns = [plot_x_axis,filter_ensemble_version_id, color_options]

        dataset = pd.merge(meta_data_df, raw_counts_df, left_on=common_columns, right_on=common_columns)
        filter_dataset = dataset[subset_columns]
        filter_dataset.rename(columns={filter_ensemble_version_id: filter_gene["Gene_name"].iloc[0]}, inplace=True)
        filtered_gene = filter_gene["Gene_name"].iloc[0]
        fig = px.box(
            filter_dataset, 
            x=plot_x_axis, 
            y=filter_gene["Gene_name"].iloc[0],
            color=color_options )
        
        fig.update_layout(
            plot_bgcolor='white',
            title={
                'text': f"<b>{filtered_gene} Expression by {color_options.replace("_"," ").capitalize()}</b>",  # Make title bold
                'x': 0.5,  # Center the title
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {
                    'color': 'black'  # Change the font color to black
                }
            },
            xaxis={
                'showticklabels': False,  # Hide x-axis labels
                'showline': True,  # Show x-axis line
                'linecolor': 'black'  # Set x-axis border color to black
            },
            yaxis={
                'showticklabels': True,  # Show y-axis labels
                'showline': True,  # Show y-axis line
                'linecolor': 'black'  # Set y-axis border color to black
            })
       
        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        return render_template('box_plot.html', raw_counts=filter_dataset.to_dict(orient='records'), col_option=colnames_meta, exp_option=raw_counts_column, files_uploaded=True, graphJSON=graphJSON)

    return render_template('box_plot.html', col_option=colnames_meta, files_uploaded=False)






      
        
    

if __name__ == '__main__':
    app.run(debug=True)
