from flask import Flask, request, redirect, url_for, send_file
import pandas as pd
import zipfile
import os
import shutil

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
EXTRACT_FOLDER = 'extracted'
MERGED_FILE = 'combined_dataset.csv'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['EXTRACT_FOLDER'] = EXTRACT_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXTRACT_FOLDER, exist_ok=True)

@app.route('/')
def upload_form():
    return '''
    <html>
        <body>
            <h1>Upload a ZIP file containing CSV files</h1>
            <form action="/upload" method="post" enctype="multipart/form-data">
                <input type="file" name="file">
                <input type="submit">
            </form>
        </body>
    </html>
    '''

@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        if uploaded_file and uploaded_file.filename.endswith('.zip'):
            zip_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
            uploaded_file.save(zip_path)
            print(f"Uploaded ZIP file saved to {zip_path}")

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(app.config['EXTRACT_FOLDER'])
                print(f"Extracted files to {app.config['EXTRACT_FOLDER']}")

            dataframes = []
            csv_files = [f for f in os.listdir(app.config['EXTRACT_FOLDER']) if f.endswith('.csv')]
            if not csv_files:
                return "No CSV files found in the ZIP archive.", 400
            
            for filename in csv_files:
                file_path = os.path.join(app.config['EXTRACT_FOLDER'], filename)
                print(f"Reading CSV file: {file_path}")
                df = pd.read_csv(file_path)
                print(f"DataFrame columns: {df.columns.tolist()}")
                dataframes.append(df)

            # Check if any DataFrames were loaded
            if not dataframes:
                return "No CSV files found in the ZIP archive.", 400

            # Concatenate DataFrames
            merged_df = pd.concat(dataframes, axis=0, ignore_index=True)

            # Save the merged DataFrame
            merged_df.to_csv(MERGED_FILE, index=False)
            print(f"Merged DataFrame saved to {MERGED_FILE}")

            # Delete extracted files after merging
            try:
                shutil.rmtree(app.config['EXTRACT_FOLDER'])
                print(f"Deleted extracted files in {app.config['EXTRACT_FOLDER']}")
            except Exception as e:
                print(f"Error deleting extracted files: {str(e)}")

            return redirect(url_for('download_file'))
        else:
            return "Uploaded file is not a ZIP archive.", 400

@app.route('/download')
def download_file():
    try:
        return send_file(MERGED_FILE, as_attachment=True)
    finally:
        # Delete the merged CSV file after download
        try:
            os.remove(MERGED_FILE)
            print(f"Deleted merged file {MERGED_FILE}")
        except Exception as e:
            print(f"Error deleting merged file: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)
