from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os
import pandas as pd

# ----------------------
# Flask app setup
# ----------------------
app = Flask(__name__)

# Folder to save uploaded datasets
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'datasets')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

# ----------------------
# Helper functions
# ----------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ----------------------
# Routes
# ----------------------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file part"
        file = request.files['file']
        if file.filename == '':
            return "No selected file"
        if file and allowed_file(file.filename):
            # Secure the filename
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            # Save the file
            file.save(filepath)
            print("Uploaded file saved at:", filepath)
            # Redirect to view page
            return redirect(url_for('view_file', filename=filename))
        else:
            return "Unsupported file type. Only CSV or XLSX allowed."
    return render_template('upload.html')

from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os
import pandas as pd

# ----------------------
# Flask app setup
# ----------------------
app = Flask(__name__)

# Folder to save uploaded datasets
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'datasets')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

# ----------------------
# Helper functions
# ----------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ----------------------
# Routes
# ----------------------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file part"
        file = request.files['file']
        if file.filename == '':
            return "No selected file"
        if file and allowed_file(file.filename):
            # Secure the filename
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            # Save the file
            file.save(filepath)
            print("Uploaded file saved at:", filepath)
            # Redirect to view page
            return redirect(url_for('view_file', filename=filename))
        else:
            return "Unsupported file type. Only CSV or XLSX allowed."
    return render_template('upload.html')

@app.route('/view/<filename>')
def view_file(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return f"File '{filename}' not found in datasets folder!"

    try:
        # Read CSV or Excel
        if filename.endswith('.csv'):
            df = pd.read_csv(filepath)
        elif filename.endswith('.xlsx'):
            df = pd.read_excel(filepath)
        else:
            return "Unsupported file format"

        # Convert dataframe to HTML
        table_html = df.to_html(classes='table', index=False)
        return render_template('view.html', filename=filename, table_html=table_html)

    except Exception as e:
        return f"Error reading file: {e}"


if __name__ == '__main__':
    app.run(debug=True)
