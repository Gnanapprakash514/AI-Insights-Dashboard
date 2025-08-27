from flask import Flask, render_template, request, redirect, url_for, send_file
from werkzeug.utils import secure_filename
import os
import pandas as pd
import plotly.express as px
import plotly.io as pio

# ----------------------
# Flask app setup
# ----------------------
app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'datasets')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

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
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            return redirect(url_for('view_file', filename=filename))
        else:
            return "Unsupported file type. Only CSV or XLSX allowed."
    return render_template('upload.html')


@app.route('/view/<filename>')
def view_file(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return f"File '{filename}' not found!"
    try:
        # Read dataset
        if filename.endswith('.csv'):
            df = pd.read_csv(filepath)
        elif filename.endswith('.xlsx'):
            df = pd.read_excel(filepath)
        else:
            return "Unsupported file format"

        # Table HTML
        table_html = df.to_html(classes='table', index=False)

        # Dataset insights
        shape_info = f"Rows: {df.shape[0]}, Columns: {df.shape[1]}"
        columns_html = pd.DataFrame(df.dtypes, columns=['Data Type']).to_html(classes='table', index=True)
        summary_html = df.describe(include='all').to_html(classes='table', index=True)
        missing_html = df.isnull().sum().to_frame('Missing Values').to_html(classes='table', index=True)
        duplicates_html = pd.DataFrame({'Duplicate Rows': [df.duplicated().sum()]}).to_html(classes='table', index=False)

        # Simple type issues check
        type_issues = {}
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64']:
                invalid_count = df[pd.to_numeric(df[col], errors='coerce').isna()].shape[0]
                if invalid_count > 0:
                    type_issues[col] = invalid_count
        type_issues_html = pd.DataFrame.from_dict(type_issues, orient='index', columns=['Invalid Entries']).to_html(classes='table') if type_issues else "<p>No type issues found</p>"

        # --------------------
        # Plotly charts
        # --------------------
        charts = []
        numeric_cols = df.select_dtypes(include='number').columns.tolist()
        for col in numeric_cols[:3]:
            fig = px.histogram(df, x=col, title=f'Distribution of {col}')
            charts.append(pio.to_html(fig, full_html=False))

        cat_cols = df.select_dtypes(include='object').columns.tolist()
        for col in cat_cols[:3]:
            top_vals = df[col].value_counts().nlargest(5)
            fig = px.bar(top_vals, x=top_vals.index, y=top_vals.values, title=f'Top 5 categories of {col}')
            charts.append(pio.to_html(fig, full_html=False))

        return render_template(
            'view.html',
            filename=filename,
            table_html=table_html,
            shape_info=shape_info,
            columns_html=columns_html,
            summary_html=summary_html,
            missing_html=missing_html,
            duplicates_html=duplicates_html,
            type_issues_html=type_issues_html,
            charts=charts
        )

    except Exception as e:
        return f"Error reading file: {e}"


@app.route('/clean/<filename>', methods=['POST'])
def clean_file(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return f"File '{filename}' not found!"
    try:
        # Load dataset
        if filename.endswith('.csv'):
            df = pd.read_csv(filepath)
        elif filename.endswith('.xlsx'):
            df = pd.read_excel(filepath)
        else:
            return "Unsupported file format"

        # --------------------
        # Handle missing values
        # --------------------
        missing_option = request.form.get('missing_option', 'none')
        if missing_option == 'mean':
            for col in df.select_dtypes(include='number').columns:
                df[col].fillna(df[col].mean(), inplace=True)
        elif missing_option == 'median':
            for col in df.select_dtypes(include='number').columns:
                df[col].fillna(df[col].median(), inplace=True)
        elif missing_option == 'mode':
            for col in df.columns:
                df[col].fillna(df[col].mode()[0], inplace=True)
        elif missing_option == 'drop':
            df.dropna(inplace=True)

        # --------------------
        # Remove duplicates
        # --------------------
        if request.form.get('remove_duplicates'):
            df.drop_duplicates(inplace=True)

        # --------------------
        # Save cleaned dataset
        # --------------------
        if filename.startswith("cleaned_"):
            clean_filename = filename  # Don't add another "cleaned_"
        else:
            clean_filename = "cleaned_" + filename

        clean_filepath = os.path.join(app.config['UPLOAD_FOLDER'], clean_filename)
        if filename.endswith('.csv'):
            df.to_csv(clean_filepath, index=False)
        else:
            df.to_excel(clean_filepath, index=False)

        return redirect(url_for('view_file', filename=clean_filename))

    except Exception as e:
        return f"Error cleaning file: {e}"


@app.route('/download/<filename>')
def download_file(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return f"File '{filename}' not found!"
    return send_file(filepath, as_attachment=True)


@app.route('/dashboard/<filename>')
def dashboard(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return f"File '{filename}' not found!"
    try:
        # Read dataset
        if filename.endswith('.csv'):
            df = pd.read_csv(filepath)
        elif filename.endswith('.xlsx'):
            df = pd.read_excel(filepath)
        else:
            return "Unsupported file format"

        # Dataset insights
        shape_info = f"Rows: {df.shape[0]}, Columns: {df.shape[1]}"
        columns_html = pd.DataFrame(df.dtypes, columns=['Data Type']).to_html(classes='table', index=True)
        summary_html = df.describe(include='all').to_html(classes='table', index=True)
        missing_html = df.isnull().sum().to_frame('Missing Values').to_html(classes='table', index=True)
        duplicates_html = pd.DataFrame({'Duplicate Rows': [df.duplicated().sum()]}).to_html(classes='table', index=False)

        type_issues = {}
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64']:
                invalid_count = df[pd.to_numeric(df[col], errors='coerce').isna()].shape[0]
                if invalid_count > 0:
                    type_issues[col] = invalid_count
        type_issues_html = pd.DataFrame.from_dict(type_issues, orient='index', columns=['Invalid Entries']).to_html(classes='table') if type_issues else "<p>No type issues found</p>"

        # Charts
        charts = []
        numeric_cols = df.select_dtypes(include='number').columns.tolist()
        for col in numeric_cols[:3]:
            fig = px.histogram(df, x=col, title=f'Distribution of {col}')
            charts.append(pio.to_html(fig, full_html=False))
        cat_cols = df.select_dtypes(include='object').columns.tolist()
        for col in cat_cols[:3]:
            top_vals = df[col].value_counts().nlargest(5)
            fig = px.bar(top_vals, x=top_vals.index, y=top_vals.values, title=f'Top 5 categories of {col}')
            charts.append(pio.to_html(fig, full_html=False))

        return render_template(
            'dashboard.html',
            filename=filename,
            shape_info=shape_info,
            columns_html=columns_html,
            summary_html=summary_html,
            missing_html=missing_html,
            duplicates_html=duplicates_html,
            type_issues_html=type_issues_html,
            charts=charts
        )

    except Exception as e:
        return f"Error reading file: {e}"


if __name__ == '__main__':
    app.run(debug=True)
