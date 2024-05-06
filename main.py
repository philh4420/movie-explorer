from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session
from flask_caching import Cache
from flask_bootstrap import Bootstrap
from dotenv import load_dotenv
import os
import requests

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')  # Use a fallback if not set
Bootstrap(app)

# Setup cache
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# API Key and base URL from TMDB
API_KEY = os.getenv("TMDB_API_KEY")
TMDB_URL = "https://api.themoviedb.org/3/"

@app.route('/', methods=['GET', 'POST'])
@cache.cached(timeout=3600, query_string=True)
def home():
    page = request.args.get('page', 1, type=int)
    region = request.args.get('region', default='GB')
    today_date = datetime.now()
    two_years_later = today_date + timedelta(days=730)

    date_today_str = today_date.strftime('%Y-%m-%d')
    date_two_years_str = two_years_later.strftime('%Y-%m-%d')

    params = {
        'api_key': API_KEY,
        'primary_release_date.gte': date_today_str,
        'primary_release_date.lte': date_two_years_str,
        'region': region,
        'language': 'en-GB',
        'page': page,
        'append_to_response': 'details,videos'
    }
    response = requests.get(f"{TMDB_URL}discover/movie", params=params)
    if response.status_code == 200:
        data = response.json()
        if 'results' in data:
            movies_sorted = sorted(data['results'], key=lambda x: x.get('release_date', ''))
            total_pages = data['total_pages']
            return render_template('index.html', movies=movies_sorted, region=region, page=page, total_pages=total_pages)
        else:
            error_message = "No results found."
    else:
        error_message = f"Failed to fetch data: {response.status_code}"

    return render_template('index.html', error=error_message, region=region, page=page)

@app.route('/movie/<int:movie_id>')
def movie_details(movie_id):
    params = {
        'api_key': API_KEY,
        'append_to_response': 'videos,credits,reviews'
    }
    response = requests.get(f"{TMDB_URL}movie/{movie_id}", params=params)
    if response.status_code != 200:
        return render_template('error.html', message="Failed to fetch movie details.")
    movie_info = response.json()
    return render_template('movie_details.html', movie=movie_info)

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == "POST":
        query = request.form['search']
        params = {
            'api_key': API_KEY,
            'query': query,
            'include_adult': 'false'
        }
        response = requests.get(f"{TMDB_URL}search/movie", params=params)
        if response.status_code != 200:
            return render_template('search.html', error="Failed to retrieve results.")
        search_results = response.json()['results']
        return render_template('search.html', movies=search_results)
    return render_template('search.html')

if __name__ == "__main__":
    app.run(debug=True)
