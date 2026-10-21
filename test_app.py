import pytest
import os
import tempfile
from app import app, init_db, DATABASE

@pytest.fixture
def client():
    """Create a test client with a temporary database."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    # Override the DATABASE path
    original_db = DATABASE
    app.config['TESTING'] = True
    
    # Update the global DATABASE variable
    import app as app_module
    app_module.DATABASE = db_path
    
    # Initialize the database
    init_db()
    
    with app.test_client() as client:
        yield client
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)
    
    # Restore original database path
    app_module.DATABASE = original_db


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_shorten_valid_url(client):
    """Test shortening a valid URL."""
    response = client.post('/api/shorten',
                           json={'url': 'https://example.com/test'},
                           content_type='application/json')
    assert response.status_code == 201
    data = response.get_json()
    assert 'short_code' in data
    assert 'short_url' in data
    assert '/' + data['short_code'] in data['short_url']
    assert len(data['short_code']) == 6


def test_shorten_invalid_url_no_protocol(client):
    """Test shortening a URL without http/https protocol."""
    response = client.post('/api/shorten',
                           json={'url': 'ftp://example.com'},
                           content_type='application/json')
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'http' in data['error'].lower()


def test_shorten_invalid_url_missing_field(client):
    """Test shortening with missing URL field."""
    response = client.post('/api/shorten',
                           json={},
                           content_type='application/json')
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'url' in data['error'].lower()


def test_duplicate_url_returns_same_code(client):
    """Test that duplicate URLs return the same short code."""
    # First request
    response1 = client.post('/api/shorten',
                            json={'url': 'https://example.com/duplicate'},
                            content_type='application/json')
    assert response1.status_code == 201
    data1 = response1.get_json()
    first_code = data1['short_code']
    
    # Second request with same URL
    response2 = client.post('/api/shorten',
                            json={'url': 'https://example.com/duplicate'},
                            content_type='application/json')
    assert response2.status_code == 200
    data2 = response2.get_json()
    assert data2['short_code'] == first_code
    assert data2['short_code'] in data2['short_url']


def test_redirect_works(client):
    """Test that redirect works and returns 302."""
    # First create a short URL
    response = client.post('/api/shorten',
                           json={'url': 'https://example.com/redirect-test'},
                           content_type='application/json')
    assert response.status_code == 201
    data = response.get_json()
    short_code = data['short_code']
    
    # Test redirect
    response = client.get(f'/{short_code}')
    assert response.status_code == 302
    assert response.location == 'https://example.com/redirect-test'


def test_redirect_increments_clicks(client):
    """Test that redirect increments click count."""
    # Create a short URL
    response = client.post('/api/shorten',
                           json={'url': 'https://example.com/click-test'},
                           content_type='application/json')
    assert response.status_code == 201
    data = response.get_json()
    short_code = data['short_code']
    
    # Check initial click count
    stats_response = client.get(f'/api/stats/{short_code}')
    assert stats_response.status_code == 200
    stats_data = stats_response.get_json()
    initial_clicks = stats_data['click_count']
    assert initial_clicks == 0
    
    # Perform redirect
    client.get(f'/{short_code}')
    
    # Check incremented click count
    stats_response = client.get(f'/api/stats/{short_code}')
    assert stats_response.status_code == 200
    stats_data = stats_response.get_json()
    assert stats_data['click_count'] == 1


def test_unknown_code_returns_404(client):
    """Test that unknown short codes return 404."""
    response = client.get('/nonexistentcode')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data


def test_stats_endpoint(client):
    """Test the stats endpoint."""
    # Create a short URL
    response = client.post('/api/shorten',
                           json={'url': 'https://example.com/stats-test'},
                           content_type='application/json')
    assert response.status_code == 201
    data = response.get_json()
    short_code = data['short_code']
    
    # Get stats
    stats_response = client.get(f'/api/stats/{short_code}')
    assert stats_response.status_code == 200
    stats_data = stats_response.get_json()
    assert stats_data['short_code'] == short_code
    assert stats_data['original_url'] == 'https://example.com/stats-test'
    assert 'created_at' in stats_data
    assert 'click_count' in stats_data
    assert stats_data['click_count'] == 0


def test_stats_unknown_code(client):
    """Test stats endpoint with unknown code."""
    response = client.get('/api/stats/nonexistent')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data


def test_frontend_served(client):
    """Test that the frontend is served at root."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'URL Shortener' in response.data
    assert b'Shorten' in response.data


def test_cors_headers(client):
    """Test that CORS headers are present."""
    response = client.options('/api/shorten')
    assert response.status_code == 200
    assert 'Access-Control-Allow-Origin' in response.headers


def test_multiple_redirects_increment_clicks(client):
    """Test that multiple redirects increment click count correctly."""
    # Create a short URL
    response = client.post('/api/shorten',
                           json={'url': 'https://example.com/multi-click'},
                           content_type='application/json')
    assert response.status_code == 201
    data = response.get_json()
    short_code = data['short_code']
    
    # Perform multiple redirects
    for _ in range(5):
        client.get(f'/{short_code}')
    
    # Check final click count
    stats_response = client.get(f'/api/stats/{short_code}')
    assert stats_response.status_code == 200
    stats_data = stats_response.get_json()
    assert stats_data['click_count'] == 5
