# CodeAlpha - Simple URL Shortener

A simple, secure URL shortener built with Flask and SQLite for CodeAlpha Internship (Task 1). Features a clean web interface, RESTful API, click tracking, and comprehensive test coverage.

## Overview

This URL shortener service allows users to convert long URLs into short, shareable links. It includes a modern web interface for quick shortening and a RESTful API for programmatic access. The service tracks click counts for analytics and uses cryptographically secure random codes to prevent enumeration attacks.

## Features

- 🌐 **Web Interface**: Clean, responsive frontend for easy URL shortening
- 🔗 **RESTful API**: Full API for programmatic access
- 📊 **Click Tracking**: Automatically tracks how many times each short URL is accessed
- 🔒 **Secure Codes**: Cryptographically secure random codes prevent enumeration
- 🔄 **Duplicate Detection**: Returns existing short code for previously shortened URLs
- 🌍 **CORS Enabled**: Cross-origin requests supported for API usage
- ✅ **Error Handling**: Consistent JSON error responses
- 📝 **Logging**: Comprehensive logging for debugging and monitoring
- 🧪 **Tested**: Comprehensive pytest test suite with 100% coverage of core functionality

## Tech Stack

- **Backend**: Python 3.14+, Flask 3.0.0
- **Database**: SQLite (built-in Python sqlite3)
- **Frontend**: Plain HTML, CSS, and vanilla JavaScript
- **Testing**: pytest 7.4.3
- **CORS**: flask-cors 4.0.0

## Setup Instructions

### Prerequisites

- Python 3.14 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd url-shortener
   ```

2. **Create a virtual environment**

   **Windows (PowerShell):**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate
   ```

   **Windows (Command Prompt):**
   ```cmd
   python -m venv venv
   venv\Scripts\activate.bat
   ```

   **Linux/Mac:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

   The application will start on `http://127.0.0.1:5000`

5. **Open in browser**
   Navigate to `http://127.0.0.1:5000` to use the web interface

## API Documentation

### Base URL
```
http://127.0.0.1:5000
```

### Endpoints

#### `GET /`
Serves the web interface.

**Response:** HTML page

---

#### `GET /health`
Health check endpoint.

**Response (200):**
```json
{
  "status": "ok"
}
```

---

#### `POST /api/shorten`
Create a short URL for a given original URL.

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "url": "https://example.com/very/long/url"
}
```

**Response (201 - New URL):**
```json
{
  "short_code": "Nw1wFP",
  "short_url": "http://127.0.0.1:5000/Nw1wFP"
}
```

**Response (200 - Existing URL):**
```json
{
  "short_code": "Nw1wFP",
  "short_url": "http://127.0.0.1:5000/Nw1wFP"
}
```

**Error Response (400):**
```json
{
  "error": "URL must start with http:// or https://"
}
```

**Error Response (400):**
```json
{
  "error": "Missing 'url' field"
}
```

---

#### `GET /api/stats/<short_code>`
Get statistics for a short code.

**Response (200):**
```json
{
  "short_code": "Nw1wFP",
  "original_url": "https://example.com/very/long/url",
  "created_at": "2026-10-21T08:45:33.821274+00:00",
  "click_count": 42
}
```

**Error Response (404):**
```json
{
  "error": "Short code not found"
}
```

---

#### `GET /<short_code>`
Redirect to the original URL.

**Response (302):**
```
Location: https://example.com/very/long/url
```

**Error Response (404):**
```json
{
  "error": "Short code not found"
}
```

---

### Example Usage with curl

```bash
# Create a short URL
curl -X POST http://127.0.0.1:5000/api/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/long/path"}'

# Get statistics
curl http://127.0.0.1:5000/api/stats/Nw1wFP

# Test redirect
curl -I http://127.0.0.1:5000/Nw1wFP
```

## Project Structure

```
url-shortener/
├── app.py                 # Flask application with all routes and database logic
├── requirements.txt       # Python dependencies
├── test_app.py           # Pytest test suite
├── .gitignore            # Git ignore file
├── README.md             # This file
├── templates/
│   └── index.html        # Frontend HTML template
└── instance/
    └── urls.db          # SQLite database (created automatically)
```

## Design Decisions

### Short Code Generation

This URL shortener uses **random alphanumeric codes** generated with Python's `secrets` module.

#### Trade-offs: Random Codes vs Hashing vs Base62

| Approach | Pros | Cons |
|----------|------|------|
| **Random Codes** (current) | - Cryptographically secure<br>- Unpredictable<br>- Fixed length<br>- No collision risk with proper check | - Requires database collision check<br>- Not reversible<br>- Slightly more storage per URL |
| **Hashing (MD5/SHA)** | - Deterministic (same URL = same code)<br>- No database check needed<br>- Can detect duplicates | - Hashes are long (needs truncation)<br>- Truncation increases collision risk<br>- Still requires database lookup<br>- Predictable pattern |
| **Base62 Encoding** | - Guaranteed unique (from auto-increment ID)<br>- No collision check needed<br>- Shortest possible codes<br>- Reversible to ID | - Sequential/predictable pattern<br>- Allows enumeration of all URLs<br>- Not cryptographically secure<br>- Requires ID before encoding |

#### Why Random Codes?

Random codes provide the best balance of security and usability:
- **Security**: Unpredictable prevents enumeration attacks
- **Usability**: Fixed 6-character codes are easy to share
- **Reliability**: Collision checking ensures uniqueness
- **Simplicity**: No need to manage IDs or handle hash collisions

With 62 characters (a-z, A-Z, 0-9), 6-character codes provide ~56 billion possible combinations, making collisions extremely unlikely.

### Database Choice

SQLite was chosen for its simplicity and zero-configuration requirements. It's perfect for development and small-scale deployments. For production with high traffic, consider PostgreSQL or MySQL.

### Frontend Approach

The frontend uses plain HTML, CSS, and vanilla JavaScript to keep dependencies minimal and the project easy to understand. No build step or framework is required.

## Future Improvements

Potential enhancements for production deployment:

- **Custom Aliases**: Allow users to choose their own short codes
- **URL Expiry**: Add expiration dates for short URLs
- **Rate Limiting**: Implement rate limiting to prevent abuse
- **Authentication**: Add user accounts and authentication
- **Analytics Dashboard**: Web interface for viewing click statistics
- **QR Code Generation**: Generate QR codes for short URLs
- **Docker Support**: Containerize the application for easy deployment
- **Production Database**: Migrate to PostgreSQL or MySQL
- **Redis Caching**: Add caching layer for frequently accessed URLs
- **API Keys**: Require API keys for programmatic access
- **HTTPS Support**: Enable HTTPS for secure connections
- **Webhook Notifications**: Send notifications on URL creation or clicks

## Testing

The project includes comprehensive pytest tests covering all functionality.

### Running Tests

```bash
# Activate virtual environment first (see Setup Instructions)

# Run all tests with verbose output
pytest test_app.py -v

# Run specific test
pytest test_app.py::test_shorten_valid_url -v

# Run with coverage
pip install pytest-cov
pytest test_app.py --cov=app --cov-report=html
```

### Test Coverage

The test suite includes:

- ✅ Health endpoint check
- ✅ Shortening valid URLs
- ✅ Rejecting invalid URLs (missing protocol, missing field)
- ✅ Duplicate URL detection (returns same code)
- ✅ Redirect functionality (302 response)
- ✅ Click count increment on redirect
- ✅ 404 for unknown short codes
- ✅ Stats endpoint functionality
- ✅ Frontend serving
- ✅ CORS headers
- ✅ Multiple redirect click tracking

All tests use a temporary SQLite database that is cleaned up after each test run.


## Author

Your Name - (https://github.com/somuuvg100)
