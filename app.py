import os
from flask import Flask, render_template, request, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename
from docx import Document
from docx2pdf import convert as docx2pdf_convert
import pandas as pd
from pdf2image import convert_from_path

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
CONVERTED_FOLDER = 'converted'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONVERTED_FOLDER'] = CONVERTED_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_file():
    file = request.files['file']
    convert_from = request.form['convert_from']
    convert_to = request.form['convert_to']

    if not file:
        return "No file uploaded."

    filename = secure_filename(file.filename)
    upload_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(upload_path)

    name, ext = os.path.splitext(filename)
    converted_filename = f"{name}.{convert_to}"
    converted_path = os.path.join(CONVERTED_FOLDER, converted_filename)

    try:
        if convert_from == 'docx' and convert_to == 'pdf':
            docx2pdf_convert(upload_path, converted_path)

        elif convert_from == 'docx' and convert_to == 'txt':
            doc = Document(upload_path)
            with open(converted_path, 'w', encoding='utf-8') as f:
                for para in doc.paragraphs:
                    f.write(para.text + '\n')

        elif convert_from == 'xlsx' and convert_to == 'csv':
            df = pd.read_excel(upload_path)
            df.to_csv(converted_path, index=False)

        elif convert_from == 'pdf' and convert_to == 'png':
            images = convert_from_path(upload_path)
            for i, img in enumerate(images):
                img_path = os.path.join(CONVERTED_FOLDER, f"{name}_{i + 1}.png")
                img.save(img_path, 'PNG')
            return redirect(url_for('download_image', prefix=name))  # special case

        else:
            return "Conversion not supported."

    except Exception as e:
        return f"Error: {str(e)}"

    return redirect(url_for('download_file', filename=converted_filename))

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(CONVERTED_FOLDER, filename, as_attachment=True)

@app.route('/download_images/<prefix>')
def download_image(prefix):
    files = [f for f in os.listdir(CONVERTED_FOLDER) if f.startswith(prefix) and f.endswith('.png')]
    if len(files) == 1:
        return send_from_directory(CONVERTED_FOLDER, files[0], as_attachment=True)
    return "<br>".join([f'<a href="/download/{f}">{f}</a>' for f in files])

if __name__ == '__main__':
    app.run(debug=True)
