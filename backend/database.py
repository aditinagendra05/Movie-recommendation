# database.py
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional

class DatabaseManager:
    def __init__(self, db_path: str = "movie_recommendations.db"):
        """Initialize database connection and create tables if they don't exist"""
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get a database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    
    def init_database(self):
        """Create tables if they don't exist"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create recommendations history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recommendation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                searched_movie_name TEXT NOT NULL,
                searched_movie_year TEXT,
                searched_movie_genres TEXT,
                language_preference TEXT,
                genre_weight REAL,
                overview_weight REAL,
                num_recommendations INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create recommended movies table (one-to-many relationship)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recommended_movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                history_id INTEGER NOT NULL,
                movie_title TEXT NOT NULL,
                original_title TEXT,
                language TEXT,
                release_date TEXT,
                rating REAL,
                overview TEXT,
                similarity_score REAL,
                genre_similarity REAL,
                overview_similarity REAL,
                genres TEXT,
                recommendation_rank INTEGER,
                FOREIGN KEY (history_id) REFERENCES recommendation_history(id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✓ Database initialized successfully")
    
    def save_recommendation(self, searched_movie: Dict, recommendations: List[Dict], 
                          language: str, genre_weight: float, overview_weight: float) -> int:
        """
        Save a recommendation session to the database
        Returns the history_id of the saved record
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Insert into recommendation_history
            cursor.execute('''
                INSERT INTO recommendation_history 
                (searched_movie_name, searched_movie_year, searched_movie_genres, 
                 language_preference, genre_weight, overview_weight, num_recommendations)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                searched_movie['title'],
                searched_movie.get('year', 'N/A'),
                json.dumps(searched_movie.get('genres', [])),
                language,
                genre_weight,
                overview_weight,
                len(recommendations)
            ))
            
            history_id = cursor.lastrowid
            
            # Insert recommended movies
            for rank, rec in enumerate(recommendations, 1):
                cursor.execute('''
                    INSERT INTO recommended_movies
                    (history_id, movie_title, original_title, language, release_date,
                     rating, overview, similarity_score, genre_similarity, 
                     overview_similarity, genres, recommendation_rank)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    history_id,
                    rec['title'],
                    rec.get('original_title', rec['title']),
                    rec.get('language', 'unknown'),
                    rec.get('release_date', 'N/A'),
                    rec.get('rating', 0),
                    rec.get('overview', ''),
                    rec.get('similarity', 0),
                    rec.get('genre_similarity', 0),
                    rec.get('overview_similarity', 0),
                    json.dumps(rec.get('genres', [])),
                    rank
                ))
            
            conn.commit()
            print(f"✓ Saved recommendation history (ID: {history_id})")
            return history_id
            
        except Exception as e:
            conn.rollback()
            print(f"Error saving to database: {e}")
            return -1
        finally:
            conn.close()
    
    def get_recent_history(self, limit: int = 10) -> List[Dict]:
        """Get recent recommendation history"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, searched_movie_name, searched_movie_year, 
                   searched_movie_genres, language_preference,
                   genre_weight, overview_weight, num_recommendations,
                   timestamp
            FROM recommendation_history
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'id': row['id'],
                'searched_movie': row['searched_movie_name'],
                'year': row['searched_movie_year'],
                'genres': json.loads(row['searched_movie_genres']),
                'language': row['language_preference'],
                'genre_weight': row['genre_weight'],
                'overview_weight': row['overview_weight'],
                'num_recommendations': row['num_recommendations'],
                'timestamp': row['timestamp']
            })
        
        return history
    
    def get_history_details(self, history_id: int) -> Optional[Dict]:
        """Get detailed information about a specific recommendation history"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get history record
        cursor.execute('''
            SELECT * FROM recommendation_history WHERE id = ?
        ''', (history_id,))
        
        history_row = cursor.fetchone()
        if not history_row:
            conn.close()
            return None
        
        # Get recommended movies
        cursor.execute('''
            SELECT * FROM recommended_movies 
            WHERE history_id = ?
            ORDER BY recommendation_rank
        ''', (history_id,))
        
        movie_rows = cursor.fetchall()
        conn.close()
        
        # Build result
        result = {
            'id': history_row['id'],
            'searched_movie': {
                'title': history_row['searched_movie_name'],
                'year': history_row['searched_movie_year'],
                'genres': json.loads(history_row['searched_movie_genres'])
            },
            'language': history_row['language_preference'],
            'genre_weight': history_row['genre_weight'],
            'overview_weight': history_row['overview_weight'],
            'timestamp': history_row['timestamp'],
            'recommendations': []
        }
        
        for movie in movie_rows:
            result['recommendations'].append({
                'title': movie['movie_title'],
                'original_title': movie['original_title'],
                'language': movie['language'],
                'release_date': movie['release_date'],
                'rating': movie['rating'],
                'overview': movie['overview'],
                'similarity': movie['similarity_score'],
                'genre_similarity': movie['genre_similarity'],
                'overview_similarity': movie['overview_similarity'],
                'genres': json.loads(movie['genres']),
                'rank': movie['recommendation_rank']
            })
        
        return result
    
    def get_statistics(self) -> Dict:
        """Get overall statistics from the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Total searches
        cursor.execute('SELECT COUNT(*) as count FROM recommendation_history')
        total_searches = cursor.fetchone()['count']
        
        # Total recommendations given
        cursor.execute('SELECT COUNT(*) as count FROM recommended_movies')
        total_recommendations = cursor.fetchone()['count']
        
        # Most searched movie
        cursor.execute('''
            SELECT searched_movie_name, COUNT(*) as count
            FROM recommendation_history
            GROUP BY searched_movie_name
            ORDER BY count DESC
            LIMIT 1
        ''')
        most_searched_row = cursor.fetchone()
        most_searched = {
            'movie': most_searched_row['searched_movie_name'] if most_searched_row else 'N/A',
            'count': most_searched_row['count'] if most_searched_row else 0
        }
        
        # Language preference distribution
        cursor.execute('''
            SELECT language_preference, COUNT(*) as count
            FROM recommendation_history
            GROUP BY language_preference
            ORDER BY count DESC
        ''')
        language_dist = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'total_searches': total_searches,
            'total_recommendations': total_recommendations,
            'most_searched': most_searched,
            'language_distribution': language_dist
        }
    
    def delete_history(self, history_id: int) -> bool:
        """Delete a specific recommendation history"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Delete recommended movies first (due to foreign key)
            cursor.execute('DELETE FROM recommended_movies WHERE history_id = ?', (history_id,))
            cursor.execute('DELETE FROM recommendation_history WHERE id = ?', (history_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting history: {e}")
            conn.rollback()
            conn.close()
            return False
    
    def clear_all_history(self) -> bool:
        """Clear all recommendation history"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM recommended_movies')
            cursor.execute('DELETE FROM recommendation_history')
            conn.commit()
            conn.close()
            print("✓ All history cleared")
            return True
        except Exception as e:
            print(f"Error clearing history: {e}")
            conn.rollback()
            conn.close()
            return False