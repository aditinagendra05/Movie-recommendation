import React, { useState } from "react";

function App() {
  const [movieName, setMovieName] = useState("");
  const [language, setLanguage] = useState("English");
  const [genreWeight, setGenreWeight] = useState(0.5);
  const [overviewWeight, setOverviewWeight] = useState(0.5);

  const [searchedMovie, setSearchedMovie] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const getRecommendations = async () => {
    if (!movieName.trim()) {
      setError("Please enter a movie name.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:5000/api/recommend", {
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
        return;
      }

      setSearchedMovie(data.searched_movie);
      setRecommendations(data.recommendations);
    } catch (err) {
      setError(
        "Failed to connect to server. Make sure backend is running on port 5000."
      );
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">

      <h1 className="text-3xl font-bold mb-6">🎬 Movie Recommender</h1>

      {/* INPUT FORM */}
      <div className="bg-gray-800 p-6 rounded-xl shadow-lg mb-8">
        <input
          type="text"
          placeholder="Enter a movie name..."
          className="w-full p-3 rounded-md text-black mb-4"
          value={movieName}
          onChange={(e) => setMovieName(e.target.value)}
        />

        <button
          onClick={getRecommendations}
          className="bg-blue-600 hover:bg-blue-700 px-5 py-2 rounded-md"
        >
          Get Recommendations
        </button>
      </div>

      {/* ERROR BOX */}
      {error && (
        <p className="bg-red-600 p-3 rounded-md mb-4">{error}</p>
      )}

      {/* LOADING */}
      {loading && <p className="text-yellow-400 mb-4">Loading...</p>}

      {/* SEARCHED MOVIE */}
      {searchedMovie && (
        <h2 className="text-xl font-semibold mb-4">
          Results based on:{" "}
          <span className="text-blue-400">{searchedMovie}</span>
        </h2>
      )}

      {/* RECOMMENDATIONS GRID */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {recommendations.map((rec, index) => (
          <div
            key={index}
            className="bg-gray-800 p-4 rounded-lg shadow-lg hover:scale-105 transition"
          >
            <h3 className="text-xl font-bold mb-2">{rec.title}</h3>

            <p className="text-gray-300 text-sm mb-1">
              <strong>Year:</strong> {rec.year}
            </p>

            <p className="text-gray-300 text-sm mb-1">
              <strong>Rating:</strong> {rec.rating}
            </p>

            <p className="text-gray-300 text-sm mb-1">
              <strong>Language:</strong> {rec.language}
            </p>

            <p className="text-gray-300 text-sm mb-1">
              <strong>Genres:</strong> {rec.genres}
            </p>

            <p className="text-gray-400 text-sm mt-2">
              {rec.overview}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
