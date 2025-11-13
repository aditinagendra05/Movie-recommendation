# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from movie_recommender import MovieRecommender
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Initialize the recommender with API key
TMDB_API_KEY = os.getenv('TMDB_API_KEY', 'YOUR_API_KEY_HERE')
recommender = MovieRecommender(TMDB_API_KEY)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "Movie Recommender API is running"
    }), 200

@app.route('/api/recommend', methods=['POST'])
def recommend():
    """
    Get movie recommendations
    
    Expected JSON payload:
    {
        "movieName": "URI: The Surgical Strike",
        "language": "hindi",
        "genreWeight": 0.7,
        "overviewWeight": 0.3
    }
    """
    try:
        # Get data from request
        data = request.get_json()
        
        # Validate required fields
        if not data or 'movieName' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required field: movieName"
            }), 400
        
        movie_name = data['movieName']
        language = data.get('language', 'mixed')
        genre_weight = float(data.get('genreWeight', 0.7))
        overview_weight = float(data.get('overviewWeight', 0.3))
        
        # Validate weights
        if genre_weight < 0 or genre_weight > 1 or overview_weight < 0 or overview_weight > 1:
            return jsonify({
                "success": False,
                "error": "Weights must be between 0 and 1"
            }), 400
        
        if abs(genre_weight + overview_weight - 1.0) > 0.01:
            return jsonify({
                "success": False,
                "error": "Weights must sum to 1.0"
            }), 400
        
        # Get recommendations
        result = recommender.get_recommendations(
            movie_name=movie_name,
            language=language,
            num_recommendations=5,
            genre_weight=genre_weight,
            overview_weight=overview_weight
        )
        
        return jsonify(result), 200
        
    except ValueError as ve:
        return jsonify({
            "success": False,
            "error": f"Invalid input: {str(ve)}"
        }), 400
    except Exception as e:
        print(f"Error in recommend endpoint: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error. Please try again later."
        }), 500

@app.route('/api/search', methods=['GET'])
def search_movie():
    """
    Search for a movie by name
    Query parameter: q (movie name)
    """
    try:
        movie_name = request.args.get('q', '')
        
        if not movie_name:
            return jsonify({
                "success": False,
                "error": "Missing query parameter: q"
            }), 400
        
        movie = recommender.search_movie(movie_name)
        
        if movie:
            return jsonify({
                "success": True,
                "movie": movie
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": f"Movie '{movie_name}' not found"
            }), 404
            
    except Exception as e:
        print(f"Error in search endpoint: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500

if __name__ == '__main__':
    print("Starting Movie Recommender API...")
    print(f"Using TMDb API Key: {TMDB_API_KEY[:10]}..." if TMDB_API_KEY != 'YOUR_API_KEY_HERE' else "WARNING: Using placeholder API key")
    print("Server running on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)