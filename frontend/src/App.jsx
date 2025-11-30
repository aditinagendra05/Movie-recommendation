import React, { useState, useEffect } from "react";

const API_BASE_URL = "http://localhost:5000/api";

function App() {
  const [movieName, setMovieName] = useState("");
  const [language, setLanguage] = useState("mixed");
  const [genreWeight, setGenreWeight] = useState(0.7);
  const [overviewWeight, setOverviewWeight] = useState(0.3);

  const [searchedMovie, setSearchedMovie] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // History state
  const [showHistory, setShowHistory] = useState(false);
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [selectedHistory, setSelectedHistory] = useState(null);
  const [statistics, setStatistics] = useState(null);

  // Update overview weight when genre weight changes
  const handleGenreWeightChange = (value) => {
    const newGenreWeight = parseFloat(value);
    setGenreWeight(newGenreWeight);
    setOverviewWeight(1 - newGenreWeight);
  };

  // Fetch history
  const fetchHistory = async () => {
    setHistoryLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/history?limit=20`);
      const data = await response.json();
      
      if (data.success) {
        setHistory(data.history);
      }
    } catch (err) {
      console.error("Error fetching history:", err);
    } finally {
      setHistoryLoading(false);
    }
  };

  // Fetch statistics
  const fetchStatistics = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/statistics`);
      const data = await response.json();
      
      if (data.success) {
        setStatistics(data.statistics);
      }
    } catch (err) {
      console.error("Error fetching statistics:", err);
    }
  };

  // Load history details
  const loadHistoryDetails = async (historyId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/history/${historyId}`);
      const data = await response.json();
      
      if (data.success) {
        setSelectedHistory(data.details);
        setSearchedMovie(data.details.searched_movie);
        setRecommendations(data.details.recommendations);
        setShowHistory(false);
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    } catch (err) {
      console.error("Error loading history details:", err);
    }
  };

  // Delete history item
  const deleteHistoryItem = async (historyId) => {
    if (!window.confirm("Are you sure you want to delete this history item?")) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/history/${historyId}`, {
        method: 'DELETE'
      });
      const data = await response.json();
      
      if (data.success) {
        fetchHistory();
        if (selectedHistory?.id === historyId) {
          setSelectedHistory(null);
          setSearchedMovie(null);
          setRecommendations([]);
        }
      }
    } catch (err) {
      console.error("Error deleting history:", err);
    }
  };

  // Clear all history
  const clearAllHistory = async () => {
    if (!window.confirm("Are you sure you want to clear all history? This cannot be undone.")) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/history/clear`, {
        method: 'DELETE'
      });
      const data = await response.json();
      
      if (data.success) {
        setHistory([]);
        setSelectedHistory(null);
        setSearchedMovie(null);
        setRecommendations([]);
        fetchStatistics();
      }
    } catch (err) {
      console.error("Error clearing history:", err);
    }
  };

  // Get recommendations
  const getRecommendations = async () => {
    if (!movieName.trim()) {
      setError("Please enter a movie name.");
      return;
    }

    setLoading(true);
    setError("");
    setSearchedMovie(null);
    setRecommendations([]);
    setSelectedHistory(null);

    try {
      const response = await fetch(`${API_BASE_URL}/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          movieName,
          language,
          genreWeight,
          overviewWeight,
        }),
      });

      const data = await response.json();

      if (!data.success) {
        setError(data.error || "Failed to get recommendations");
        setSearchedMovie(null);
        setRecommendations([]);
        return;
      }

      setSearchedMovie(data.searched_movie);
      setRecommendations(data.recommendations || []);
      
      if (data.recommendations.length === 0) {
        setError(data.message || "No recommendations found for this movie.");
      }

      // Refresh history after successful recommendation
      fetchHistory();
      fetchStatistics();
    } catch (err) {
      setError(
        "Failed to connect to server. Make sure backend is running on http://localhost:5000"
      );
      console.error("Error:", err);
    } finally {
      setLoading(false);
    }
  };

  // Load history on component mount
  useEffect(() => {
    fetchHistory();
    fetchStatistics();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 text-white p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl md:text-5xl font-bold mb-2 bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-600">
              🎬 Movie Recommender
            </h1>
            <p className="text-gray-400">
              Powered by AI - Get personalized movie recommendations
            </p>
          </div>
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded-lg font-semibold transition-all flex items-center gap-2"
          >
            📜 {showHistory ? "Hide History" : "View History"}
          </button>
        </div>

        {/* Statistics Bar */}
        {statistics && !showHistory && (
          <div className="bg-gray-800/50 backdrop-blur-lg p-4 rounded-xl mb-6 border border-gray-700">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div>
                <p className="text-gray-400 text-sm">Total Searches</p>
                <p className="text-2xl font-bold text-purple-400">{statistics.total_searches}</p>
              </div>
              <div>
                <p className="text-gray-400 text-sm">Movies Recommended</p>
                <p className="text-2xl font-bold text-pink-400">{statistics.total_recommendations}</p>
              </div>
              <div>
                <p className="text-gray-400 text-sm">Most Searched</p>
                <p className="text-lg font-bold text-yellow-400 truncate">{statistics.most_searched.movie}</p>
              </div>
              <div>
                <p className="text-gray-400 text-sm">Search Count</p>
                <p className="text-2xl font-bold text-green-400">{statistics.most_searched.count}</p>
              </div>
            </div>
          </div>
        )}

        {/* History View */}
        {showHistory ? (
          <div className="bg-gray-800/50 backdrop-blur-lg p-6 rounded-xl shadow-2xl mb-8 border border-gray-700">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold">Recommendation History</h2>
              {history.length > 0 && (
                <button
                  onClick={clearAllHistory}
                  className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg text-sm transition-all"
                >
                  Clear All History
                </button>
              )}
            </div>

            {historyLoading ? (
              <div className="text-center py-8">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-500"></div>
              </div>
            ) : history.length === 0 ? (
              <div className="text-center py-12 text-gray-400">
                <p className="text-4xl mb-2">📭</p>
                <p>No history yet. Start by searching for a movie!</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-[600px] overflow-y-auto">
                {history.map((item) => (
                  <div
                    key={item.id}
                    className="bg-gray-700/50 p-4 rounded-lg hover:bg-gray-700 transition-all cursor-pointer border border-gray-600 hover:border-purple-500"
                  >
                    <div className="flex justify-between items-start gap-4">
                      <div className="flex-1" onClick={() => loadHistoryDetails(item.id)}>
                        <h3 className="font-bold text-lg text-purple-300">
                          {item.searched_movie}
                        </h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm text-gray-300 mt-2">
                          <p>📅 {item.year}</p>
                          <p>🌐 {item.language}</p>
                          <p>🎯 {item.num_recommendations} recommendations</p>
                          <p>🕒 {new Date(item.timestamp).toLocaleDateString()}</p>
                        </div>
                        <p className="text-xs text-gray-400 mt-1">
                          Genre: {(item.genre_weight * 100).toFixed(0)}% | Overview: {(item.overview_weight * 100).toFixed(0)}%
                        </p>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteHistoryItem(item.id);
                        }}
                        className="bg-red-600/50 hover:bg-red-600 px-3 py-1 rounded text-sm transition-all"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <>
            {/* INPUT FORM */}
            <div className="bg-gray-800/50 backdrop-blur-lg p-6 rounded-xl shadow-2xl mb-8 border border-gray-700">
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">Movie Name</label>
                <input
                  type="text"
                  placeholder="e.g., The Dark Knight, URI, Dangal..."
                  className="w-full p-3 rounded-lg text-black bg-white focus:ring-2 focus:ring-purple-500 outline-none"
                  value={movieName}
                  onChange={(e) => setMovieName(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && getRecommendations()}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Language Preference</label>
                  <select
                    className="w-full p-3 rounded-lg text-black bg-white focus:ring-2 focus:ring-purple-500 outline-none"
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                  >
                    <option value="mixed">Mixed (All Languages)</option>
                    <option value="hindi">Hindi</option>
                    <option value="english">English</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Recommendation Balance
                  </label>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-gray-400 whitespace-nowrap">Story Focus</span>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={genreWeight}
                      onChange={(e) => handleGenreWeightChange(e.target.value)}
                      className="flex-1 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
                    />
                    <span className="text-xs text-gray-400 whitespace-nowrap">Genre Focus</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1 text-center">
                    Genre: {(genreWeight * 100).toFixed(0)}% | Overview: {(overviewWeight * 100).toFixed(0)}%
                  </p>
                </div>
              </div>

              <button
                onClick={getRecommendations}
                disabled={loading}
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:from-gray-600 disabled:to-gray-700 px-6 py-3 rounded-lg font-semibold transition-all transform hover:scale-[1.02] active:scale-[0.98] disabled:cursor-not-allowed"
              >
                {loading ? "Searching..." : "Get Recommendations"}
              </button>
            </div>

            {/* ERROR BOX */}
            {error && (
              <div className="bg-red-500/20 border border-red-500 p-4 rounded-lg mb-6 backdrop-blur-sm">
                <p className="text-red-200">❌ {error}</p>
              </div>
            )}

            {/* LOADING */}
            {loading && (
              <div className="text-center mb-8">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500 mb-2"></div>
                <p className="text-yellow-400">Analyzing movies...</p>
              </div>
            )}

            {/* SEARCHED MOVIE INFO */}
            {searchedMovie && (
              <div className="bg-gradient-to-r from-purple-800/30 to-pink-800/30 backdrop-blur-lg p-6 rounded-xl shadow-2xl mb-8 border border-purple-500/30">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h2 className="text-2xl font-bold mb-3">
                      🎯 Based on: <span className="text-purple-400">{searchedMovie.title}</span>
                    </h2>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-400">Year:</span>
                        <p className="font-semibold">{searchedMovie.year}</p>
                      </div>
                      <div>
                        <span className="text-gray-400">Rating:</span>
                        <p className="font-semibold">⭐ {searchedMovie.rating?.toFixed(1)}/10</p>
                      </div>
                      <div>
                        <span className="text-gray-400">Language:</span>
                        <p className="font-semibold">{searchedMovie.language}</p>
                      </div>
                      <div>
                        <span className="text-gray-400">Genres:</span>
                        <p className="font-semibold">{searchedMovie.genres?.join(", ")}</p>
                      </div>
                    </div>
                    <p className="text-gray-300 text-sm mt-4 italic">{searchedMovie.overview}</p>
                  </div>
                  {selectedHistory && (
                    <span className="bg-yellow-600 text-white text-xs px-3 py-1 rounded ml-4">
                      From History
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* RECOMMENDATIONS GRID */}
            {recommendations.length > 0 && (
              <>
                <h2 className="text-2xl font-bold mb-6 text-center">
                  ✨ Recommended Movies ({recommendations.length})
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {recommendations.map((rec, index) => (
                    <div
                      key={index}
                      className="bg-gray-800/50 backdrop-blur-lg p-5 rounded-xl shadow-xl hover:shadow-2xl hover:scale-[1.03] transition-all duration-300 border border-gray-700 hover:border-purple-500"
                    >
                      <div className="flex justify-between items-start mb-3">
                        <h3 className="text-xl font-bold text-purple-300 flex-1">
                          {rec.title}
                        </h3>
                        <span className="bg-purple-600 text-white text-xs font-bold px-2 py-1 rounded ml-2">
                          #{rec.rank || index + 1}
                        </span>
                      </div>

                      <div className="space-y-2 text-sm mb-3">
                        <p className="text-gray-300">
                          <span className="text-gray-400">📅 Year:</span>{" "}
                          {rec.release_date ? rec.release_date.split("-")[0] : "N/A"}
                        </p>

                        <p className="text-gray-300">
                          <span className="text-gray-400">⭐ Rating:</span>{" "}
                          {rec.rating.toFixed(1)}/10
                        </p>

                        <p className="text-gray-300">
                          <span className="text-gray-400">🌐 Language:</span>{" "}
                          {rec.language}
                        </p>

                        <p className="text-gray-300">
                          <span className="text-gray-400">🎭 Genres:</span>{" "}
                          {rec.genres.join(", ")}
                        </p>

                        <p className="text-gray-300">
                          <span className="text-gray-400">🎯 Match:</span>{" "}
                          <span className="text-green-400 font-bold">
                            {(rec.similarity * 100).toFixed(1)}%
                          </span>
                        </p>
                      </div>

                      <p className="text-gray-400 text-xs leading-relaxed line-clamp-3">
                        {rec.overview}
                      </p>

                      <div className="mt-3 pt-3 border-t border-gray-700 text-xs">
                        <div className="flex justify-between text-gray-500">
                          <span>Genre: {(rec.genre_similarity * 100).toFixed(0)}%</span>
                          <span>Story: {(rec.overview_similarity * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}

            {/* No results message */}
            {!loading && searchedMovie && recommendations.length === 0 && !error && (
              <div className="text-center text-gray-400 py-12">
                <p className="text-2xl mb-2">🔍</p>
                <p>No recommendations found. Try a different movie or language preference.</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default App;