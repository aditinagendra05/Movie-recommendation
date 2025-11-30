# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from movie_recommender import MovieRecommender
from database import DatabaseManager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# FIX: More specific CORS configuration
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
        "methods": ["GET", "POST", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Initialize the recommender with API key
TMDB_API_KEY = os.getenv('TMDB_API_KEY', 'YOUR_API_KEY_HERE')
recommender = MovieRecommender(TMDB_API_KEY)

# Initialize database
db = DatabaseManager()

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
    """
    try:
        data = request.get_json()
        
        if not data or 'movieName' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required field: movieName"
            }), 400
        
        movie_name = data['movieName']
        movie_id = data.get('movieId')  # Optional: specific movie ID
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
            movie_id=movie_id,
            language=language,
            num_recommendations=5,
            genre_weight=genre_weight,
            overview_weight=overview_weight
        )
        
        # Save to database if successful
        if result.get('success') and result.get('searched_movie') and result.get('recommendations'):
            history_id = db.save_recommendation(
                searched_movie=result['searched_movie'],
                recommendations=result['recommendations'],
                language=language,
                genre_weight=genre_weight,
                overview_weight=overview_weight
            )
            result['history_id'] = history_id
        
        return jsonify(result), 200
        
    except ValueError as ve:
        return jsonify({
            "success": False,
            "error": f"Invalid input: {str(ve)}"
        }), 400
    except Exception as e:
        print(f"Error in recommend endpoint: {e}")
        import traceback
        traceback.print_exc()  # Print full error for debugging
        return jsonify({
            "success": False,
            "error": "Internal server error. Please try again later."
        }), 500

@app.route('/api/search-movies', methods=['GET'])
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
        
        return jsonify({
            "success": True,
            "movie": movie,
            "count": len(movie) if isinstance(movie, list) else (1 if movie else 0)
        }), 200
            
    except Exception as e:
        print(f"Error in search endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get recent recommendation history"""
    try:
        limit = request.args.get('limit', 10, type=int)
        history = db.get_recent_history(limit=limit)
        
        return jsonify({
            "success": True,
            "history": history,
            "count": len(history)
        }), 200
        
    except Exception as e:
        print(f"Error in history endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

@app.route('/api/history/<int:history_id>', methods=['GET'])
def get_history_details(history_id):
    """Get detailed information about a specific recommendation"""
    try:
        details = db.get_history_details(history_id)
        
        if details:
            return jsonify({
                "success": True,
                "details": details
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "History not found"
            }), 404
            
    except Exception as e:
        print(f"Error in history details endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get overall statistics"""
    try:
        stats = db.get_statistics()
        
        return jsonify({
            "success": True,
            "statistics": stats
        }), 200
        
    except Exception as e:
        print(f"Error in statistics endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

@app.route('/api/history/<int:history_id>', methods=['DELETE'])
def delete_history(history_id):
    """Delete a specific recommendation history"""
    try:
        success = db.delete_history(history_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "History deleted successfully"
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Failed to delete history"
            }), 500
            
    except Exception as e:
        print(f"Error in delete history endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

@app.route('/api/history/clear', methods=['DELETE'])
def clear_history():
    """Clear all recommendation history"""
    try:
        success = db.clear_all_history()
        
        if success:
            return jsonify({
                "success": True,
                "message": "All history cleared successfully"
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Failed to clear history"
            }), 500
            
    except Exception as e:
        print(f"Error in clear history endpoint: {e}")
        import traceback
        traceback.print_exc()
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
    print("="*60)
    print("Starting Movie Recommender API...")
    print("="*60)
    
    # Check API key
    if TMDB_API_KEY == 'YOUR_API_KEY_HERE':
        print("⚠️  WARNING: Using placeholder API key!")
        print("   Get your API key from: https://www.themoviedb.org/settings/api")
    else:
        print(f"✓ Using TMDb API Key: {TMDB_API_KEY[:10]}...")
    
    print(f"✓ Database initialized at: movie_recommendations.db")
    print(f"✓ Server running on http://localhost:5000")
    print(f"✓ CORS enabled for http://localhost:3000")
    print("="*60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)