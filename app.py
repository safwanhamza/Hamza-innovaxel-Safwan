from flask import Flask, request, jsonify, redirect, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random
import string

app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class URL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(500), nullable=False)
    short_code = db.Column(db.String(10), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    access_count = db.Column(db.Integer, default=0)

# Generates a short code to shorten url
def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

# Initializes DB
with app.app_context():
    db.create_all()

# Homepage/input to shorten URLs
@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

# Handle URL shortening from form
@app.route('/shorten', methods=['POST'])
def shorten_url_form():
    original_url = request.form.get('original_url')

    if not original_url:
        return render_template('index.html', error="URL is required")

    short_code = generate_short_code()
    while URL.query.filter_by(short_code=short_code).first():
        short_code = generate_short_code()

    new_url = URL(original_url=original_url, short_code=short_code)
    db.session.add(new_url)
    db.session.commit()

    short_url = request.host_url + short_code  # Construct full short URL

    return render_template('index.html', short_url=short_url, short_code=short_code)

# Redirect to Original URL
@app.route('/<short_code>')
def redirect_to_original(short_code):
    url_entry = URL.query.filter_by(short_code=short_code).first()
    if not url_entry:
        return "Short URL not found", 404

    url_entry.access_count += 1
    db.session.commit()
    return redirect(url_entry.original_url)

# Get URL Statistics Page
@app.route('/shorten/<short_code>/stats', methods=['GET'])
def get_url_stats_page(short_code):
    url_entry = URL.query.filter_by(short_code=short_code).first()
    if not url_entry:
        return "Short URL not found", 404

    return render_template('stats.html',
                           original_url=url_entry.original_url,
                           short_code=url_entry.short_code,
                           created_at=url_entry.created_at,
                           updated_at=url_entry.updated_at,
                           access_count=url_entry.access_count)

# Handle URL Update from Form
@app.route('/update', methods=['POST'])
def update_url_form():
    short_code = request.form.get('short_code')
    new_url = request.form.get('new_url')

    if not short_code or not new_url:
        return render_template('index.html', error="Short code and new URL are required")

    url_entry = URL.query.filter_by(short_code=short_code).first()
    if not url_entry:
        return render_template('index.html', error="Short URL not found")

    url_entry.original_url = new_url
    db.session.commit()

    return render_template('index.html', short_url=request.host_url + short_code, short_code=short_code)

# Get All Short URLs
@app.route('/shorten/all', methods=['GET'])
def get_all_urls():
    urls = URL.query.all()
    if not urls:
        return render_template('all_urls.html', error="No shortened URLs found.")

    return render_template('all_urls.html', urls=urls)

# Handle Short Code Update from Form
@app.route('/update-short-code', methods=['POST'])
def update_short_code_form():
    old_short_code = request.form.get('old_short_code')
    new_short_code = request.form.get('new_short_code')

    if not old_short_code or not new_short_code:
        return render_template('all_urls.html', error="Both old and new short codes are required.")

    url_entry = URL.query.filter_by(short_code=old_short_code).first()
    
    if not url_entry:
        return render_template('all_urls.html', error="Short URL not found.")

    # Check if new short code is already taken
    if URL.query.filter_by(short_code=new_short_code).first():
        return render_template('all_urls.html', error="New short code is already in use. Choose a different one.")

    url_entry.short_code = new_short_code
    db.session.commit()

    return get_all_urls()  # Redirect back to all URLs page


# Handle URL Deletion from Form
@app.route('/delete', methods=['POST'])
def delete_url_form():
    short_code = request.form.get('short_code')

    if not short_code:
        return render_template('all_urls.html', error="Short code is required.")

    url_entry = URL.query.filter_by(short_code=short_code).first()
    if not url_entry:
        return render_template('all_urls.html', error="Short URL not found.")

    db.session.delete(url_entry)
    db.session.commit()

    return get_all_urls()  # Redirect back to all URLs page


if __name__ == "__main__":
    app.run(debug=True)
