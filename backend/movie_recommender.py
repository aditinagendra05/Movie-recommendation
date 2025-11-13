# movie_recommender.py
import numpy as np
import requests
from typing import List, Dict, Optional
from collections import Counter
import re
import time

class MovieRecommender:
    def __init__(self, api_key: str):
        """
        Initialize the Movie Recommender with TMDb API
        Get your free API key from: https://www.themoviedb.org/settings/api
        """
        self.api_key = "845f13ea36ee14d6ed50333f70783cb7"
        self.base_url = "https://api.themoviedb.org/3"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9'
        })
    
    def _make_request(self, url: str, params: dict, max_retries: int = 3) -> Optional[dict]:
        """Make API request with retry logic"""
        for attempt in range(max_retries):
            try:
                time.sleep(0.5)  # Small delay between requests
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.ConnectionError as e:
                print(f"Connection error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # Wait before retry
                    continue
                return None
            except Exception as e:
                print(f"Error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                return None
        return None
    
    def search_movie(self, movie_name: str) -> Optional[Dict]:
        """Search for a movie by name"""
        url = f"{self.base_url}/search/movie"
        params = {
            "api_key": self.api_key,
            "query": movie_name
        }
        
        try:
            print(f"Searching for '{movie_name}'...")
            data = self._make_request(url, params)
            
            if data and data.get('results'):
                print(f"✓ Found {len(data['results'])} results")
                print(f"  Top result: {data['results'][0]['title']} ({data['results'][0].get('release_date', 'N/A')[:4]})")
                return data['results'][0]
            
            print(f"No results found for '{movie_name}'")
            return None
            
        except Exception as e:
            print(f"Error searching movie: {e}")
            return None
    
    def get_movie_details(self, movie_id: int) -> Optional[Dict]:
        """Get detailed information about a movie"""
        url = f"{self.base_url}/movie/{movie_id}"
        params = {
            "api_key": self.api_key,
            "append_to_response": "keywords,credits"
        }
        
        try:
            data = self._make_request(url, params)
            return data
        except Exception as e:
            print(f"Error getting movie details: {e}")
            return None
    
    def create_genre_vector(self, movie: Dict) -> np.ndarray:
        """Create a genre feature vector from movie data"""
        genre_ids = [g['id'] for g in movie.get('genres', [])]
        
        # Common genre IDs in TMDb
        all_genres = [28, 12, 16, 35, 80, 99, 18, 10751, 14, 36, 27, 10402, 9648, 10749, 878, 10770, 53, 10752, 37]
        genre_vector = np.array([1 if gid in genre_ids else 0 for gid in all_genres], dtype=float)
        
        return genre_vector
    
    def preprocess_text(self, text: str) -> List[str]:
        """Preprocess text: lowercase, remove punctuation, tokenize"""
        if not text:
            return []
        
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s]', '', text)
        tokens = text.split()
        
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'been', 'be',
                     'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                     'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
        
        tokens = [t for t in tokens if t not in stop_words and len(t) > 2]
        
        return tokens
    
    def create_tfidf_vector(self, text: str, vocabulary: Dict[str, int], idf: Dict[str, float]) -> np.ndarray:
        """Create TF-IDF vector for a text"""
        tokens = self.preprocess_text(text)
        
        tf = Counter(tokens)
        total_terms = len(tokens) if tokens else 1
        
        vector = np.zeros(len(vocabulary))
        for term, count in tf.items():
            if term in vocabulary:
                idx = vocabulary[term]
                tf_value = count / total_terms
                idf_value = idf.get(term, 0)
                vector[idx] = tf_value * idf_value
        
        return vector
    
    def build_vocabulary_and_idf(self, all_overviews: List[str]) -> tuple:
        """Build vocabulary and calculate IDF from all movie overviews"""
        all_tokens = []
        doc_tokens = []
        
        for overview in all_overviews:
            tokens = self.preprocess_text(overview)
            all_tokens.extend(tokens)
            doc_tokens.append(set(tokens))
        
        unique_terms = sorted(set(all_tokens))
        vocabulary = {term: idx for idx, term in enumerate(unique_terms)}
        
        num_docs = len(all_overviews)
        idf = {}
        
        for term in unique_terms:
            doc_count = sum(1 for doc in doc_tokens if term in doc)
            idf[term] = np.log(num_docs / (doc_count + 1)) + 1
        
        return vocabulary, idf
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors using NumPy"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def calculate_combined_similarity(self, input_genre_vec: np.ndarray, input_overview_vec: np.ndarray,
                                     movie_genre_vec: np.ndarray, movie_overview_vec: np.ndarray,
                                     genre_weight: float = 0.7, overview_weight: float = 0.3) -> tuple:
        """
        Calculate combined similarity using weighted formula
        Returns: (combined_similarity, genre_similarity, overview_similarity)
        """
        cosine_sim_genre = self.cosine_similarity(input_genre_vec, movie_genre_vec)
        cosine_sim_overview = self.cosine_similarity(input_overview_vec, movie_overview_vec)
        combined_similarity = genre_weight * cosine_sim_genre + overview_weight * cosine_sim_overview
        
        return combined_similarity, cosine_sim_genre, cosine_sim_overview
    
    def get_recommendations(self, movie_name: str, language: str = "mixed", 
                          num_recommendations: int = 5,
                          genre_weight: float = 0.7,
                          overview_weight: float = 0.3) -> Dict:
        """
        Get movie recommendations based on a given movie
        Returns a dictionary with search results and recommendations
        """
        # Search for the input movie
        input_movie = self.search_movie(movie_name)
        if not input_movie:
            return {
                "success": False,
                "error": f"Movie '{movie_name}' not found!",
                "searched_movie": None,
                "recommendations": []
            }
        
        # Get detailed info for input movie
        input_movie_details = self.get_movie_details(input_movie['id'])
        if not input_movie_details:
            return {
                "success": False,
                "error": "Failed to get movie details",
                "searched_movie": None,
                "recommendations": []
            }
        
        # Prepare searched movie info
        searched_movie_info = {
            "title": input_movie['title'],
            "year": input_movie.get('release_date', 'N/A')[:4] if input_movie.get('release_date') else 'N/A',
            "genres": [g['name'] for g in input_movie_details.get('genres', [])],
            "overview": input_movie_details.get('overview', 'No overview available'),
            "rating": input_movie.get('vote_average', 0),
            "language": input_movie.get('original_language', 'unknown').upper()
        }
        
        # Map language preference
        language_map = {
            'hindi': 'hi',
            'english': 'en',
            'mixed': None
        }
        
        lang_code = language_map.get(language.lower())
        
        # Get similar movies
        similar_movies = self._fetch_similar_movies(input_movie['id'], lang_code)
        
        if not similar_movies:
            return {
                "success": True,
                "searched_movie": searched_movie_info,
                "recommendations": [],
                "message": "No similar movies found for the selected language"
            }
        
        # Get all movie details with delay to avoid connection reset
        all_movie_details = []
        for i, movie in enumerate(similar_movies[:30]):  # Limit to 30 for performance
            details = self.get_movie_details(movie['id'])
            if details:
                all_movie_details.append((movie, details))
            
            # Add small delay every 5 requests
            if (i + 1) % 5 == 0:
                time.sleep(1)
        
        # Build vocabulary and IDF
        all_overviews = [input_movie_details.get('overview', '')] + \
                       [details.get('overview', '') for _, details in all_movie_details]
        vocabulary, idf = self.build_vocabulary_and_idf(all_overviews)
        
        # Create feature vectors for input movie
        input_genre_vec = self.create_genre_vector(input_movie_details)
        input_overview_vec = self.create_tfidf_vector(
            input_movie_details.get('overview', ''), vocabulary, idf
        )
        
        # Calculate similarities
        recommendations = []
        for movie, details in all_movie_details:
            genre_vec = self.create_genre_vector(details)
            overview_vec = self.create_tfidf_vector(details.get('overview', ''), vocabulary, idf)
            
            combined_sim, genre_sim, overview_sim = self.calculate_combined_similarity(
                input_genre_vec, input_overview_vec,
                genre_vec, overview_vec,
                genre_weight, overview_weight
            )
            
            recommendations.append({
                'title': movie['title'],
                'original_title': movie.get('original_title', movie['title']),
                'language': movie.get('original_language', 'unknown').upper(),
                'release_date': movie.get('release_date', 'N/A'),
                'rating': float(movie.get('vote_average', 0)),
                'overview': movie.get('overview', 'No overview available'),
                'similarity': float(combined_sim),
                'genre_similarity': float(genre_sim),
                'overview_similarity': float(overview_sim),
                'genres': [g['name'] for g in details.get('genres', [])]
            })
        
        # Sort by similarity and return top N
        recommendations.sort(key=lambda x: x['similarity'], reverse=True)
        
        return {
            "success": True,
            "searched_movie": searched_movie_info,
            "recommendations": recommendations[:num_recommendations],
            "total_found": len(recommendations)
        }
    
    def _fetch_similar_movies(self, movie_id: int, language_code: Optional[str] = None) -> List[Dict]:
        """Fetch similar movies from TMDb API"""
        all_movies = []
        
        try:
            # Get recommendations
            url = f"{self.base_url}/movie/{movie_id}/recommendations"
            params = {"api_key": self.api_key, "page": 1}
            data = self._make_request(url, params)
            if data:
                all_movies.extend(data.get('results', []))
            
            time.sleep(1)  # Delay between requests
            
            # Get similar movies
            url = f"{self.base_url}/movie/{movie_id}/similar"
            data = self._make_request(url, params)
            if data:
                all_movies.extend(data.get('results', []))
            
            # Filter by language if specified
            if language_code:
                all_movies = [m for m in all_movies if m.get('original_language') == language_code]
                
                # If not enough, discover more
                if len(all_movies) < 20:
                    discovered = self._discover_movies_by_language(language_code)
                    all_movies.extend(discovered)
            
            # Remove duplicates
            seen = set()
            unique_movies = []
            for movie in all_movies:
                if movie['id'] not in seen and movie['id'] != movie_id:
                    seen.add(movie['id'])
                    unique_movies.append(movie)
            
            return unique_movies
            
        except Exception as e:
            print(f"Error fetching similar movies: {e}")
            return []
    
    def _discover_movies_by_language(self, language_code: str) -> List[Dict]:
        """Discover movies in a specific language"""
        try:
            url = f"{self.base_url}/discover/movie"
            params = {
                "api_key": self.api_key,
                "with_original_language": language_code,
                "sort_by": "popularity.desc",
                "page": 1
            }
            
            data = self._make_request(url, params)
            return data.get('results', []) if data else []
        except Exception as e:
            print(f"Error discovering movies: {e}")
            return []