import sqlite3
import secrets
import string
import logging
from flask import Flask, jsonify, request, redirect, render_template
from flask_cors import CORS
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
DATABASE = 'instance/urls.db'

# Enable CORS for all routes
CORS(app)

# Database connection helper
def get_db():
    """Create and return a database connection with row factory."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Database initialization
def init_db():
    """Initialize the database with the urls table and index."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            short_code TEXT UNIQUE NOT NULL,
            original_url TEXT NOT NULL,
            created_at TEXT NOT NULL,
            click_count INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_short_code ON urls(short_code)')
    conn.commit()
    conn.close()
    logger.info("Database initialized")

# Database operations
def insert_url(short_code, original_url):
    """Insert a new URL into the database."""
    conn = get_db()
    cursor = conn.cursor()
    created_at = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        'INSERT INTO urls (short_code, original_url, created_at, click_count) VALUES (?, ?, ?, 0)',
        (short_code, original_url, created_at)
    )
    conn.commit()
    conn.close()
    logger.info(f"Inserted URL: {short_code} -> {original_url}")

def get_url_by_code(short_code):
    """Retrieve URL data by short code."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM urls WHERE short_code = ?', (short_code,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_url_by_original(original_url):
    """Retrieve URL data by original URL."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM urls WHERE original_url = ?', (original_url,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def increment_clicks(short_code):
    """Increment the click count for a short code."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE urls SET click_count = click_count + 1 WHERE short_code = ?', (short_code,))
    conn.commit()
    conn.close()
    logger.info(f"Incremented clicks for: {short_code}")

# Short code generation
def generate_short_code(length=6):
    """Generate a unique random short code."""
    alphabet = string.ascii_letters + string.digits
    while True:
        code = ''.join(secrets.choice(alphabet) for _ in range(length))
        if not get_url_by_code(code):
            return code

# Error handlers
@app.errorhandler(400)
def bad_request(error):
    """Handle 400 Bad Request errors."""
    logger.warning(f"Bad request: {error}")
    return jsonify({"error": "Bad request", "message": str(error)}), 400

@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors."""
    logger.warning(f"Not found: {error}")
    return jsonify({"error": "Not found", "message": str(error)}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server errors."""
    logger.error(f"Internal error: {error}")
    return jsonify({"error": "Internal server error", "message": str(error)}), 500

# Routes
@app.route('/')
def index():
    """Serve the frontend HTML page."""
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"})

@app.route('/api/shorten', methods=['POST'])
def shorten():
    """Create a short URL for the given original URL."""
    data = request.get_json()
    
    if not data or 'url' not in data:
        logger.warning("Missing 'url' field in request")
        return jsonify({"error": "Missing 'url' field"}), 400
    
    url = data['url'].strip()
    
    # Validate URL
    if not url.startswith(('http://', 'https://')):
        logger.warning(f"Invalid URL protocol: {url}")
        return jsonify({"error": "URL must start with http:// or https://"}), 400
    
    # Check if URL already exists
    existing = get_url_by_original(url)
    if existing:
        short_url = f"{request.host_url}{existing['short_code']}"
        logger.info(f"Returning existing short code: {existing['short_code']}")
        return jsonify({
            "short_code": existing['short_code'],
            "short_url": short_url
        }), 200
    
    # Generate new short code
    short_code = generate_short_code()
    insert_url(short_code, url)
    
    short_url = f"{request.host_url}{short_code}"
    logger.info(f"Created new short URL: {short_code}")
    return jsonify({
        "short_code": short_code,
        "short_url": short_url
    }), 201

@app.route('/api/stats/<short_code>')
def get_stats(short_code):
    """Get statistics for a short code."""
    url_data = get_url_by_code(short_code)
    
    if not url_data:
        logger.warning(f"Short code not found: {short_code}")
        return jsonify({"error": "Short code not found"}), 404
    
    return jsonify({
        "short_code": url_data['short_code'],
        "original_url": url_data['original_url'],
        "created_at": url_data['created_at'],
        "click_count": url_data['click_count']
    })

@app.route('/<short_code>')
def redirect_to_url(short_code):
    """Redirect short code to original URL."""
    url_data = get_url_by_code(short_code)
    
    if not url_data:
        logger.warning(f"Short code not found: {short_code}")
        return jsonify({"error": "Short code not found"}), 404
    
    increment_clicks(short_code)
    logger.info(f"Redirecting {short_code} to {url_data['original_url']}")
    return redirect(url_data['original_url'], code=302)

if __name__ == '__main__':
    init_db()
    logger.info("Starting Flask application")
    app.run(debug=True, host='127.0.0.1', port=5000)
