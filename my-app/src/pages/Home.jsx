import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import "./App.css";

function InputBar() {
  const navigate = useNavigate();
  return (
    <div className="search-bar">
      <input placeholder="Enter Zip Code" />
      <button
        onClick={() => {
          navigate("/seatings");
        }}
      >
        Search
      </button>
    </div>
  );
}

function ExitButton({ setModal }) {
  return <button onClick={() => setModal(false)}>&times;</button>;
}

function MovieModal({ visible, setModal, movieImg, movieTitle, movieDesc }) {
  return visible ? (
    <div className="movie-modal">
      <div className="modal-img">
        <ExitButton setModal={setModal} />
        <img src={movieImg} />
      </div>
      <div className="modal-content">
        <div className="modal-text">
          <h1>{movieTitle}</h1>
          <p>
            {movieDesc.length > 200
              ? movieDesc.substring(0, 200) + "..."
              : movieDesc}
          </p>
        </div>
        <InputBar />
      </div>
    </div>
  ) : (
    <></>
  );
}

function Home() {
  const [movies, setMovies] = useState([]);
  const [curMovie, setCurMovie] = useState({});
  const [toggleModal, setToggleModal] = useState(false);

  useEffect(() => {
    async function getMovies() {
      console.log("movie fetching began.");
      const response = await fetch("http://127.0.0.1:8000/");
      const data = await response.json();
      setMovies(data);
    }
    getMovies();
  }, []);
  return (
    <>
      <h1>Hi</h1>
      <MovieModal
        visible={toggleModal}
        setModal={setToggleModal}
        movieImg={curMovie.banner}
        movieTitle={curMovie.title}
        movieDesc={curMovie.description}
      />
      <div className="movie-container">
        {movies.map((movie) => (
          <img
            key={movie.slug}
            src={movie.poster}
            className="movie-poster"
            onClick={() => {
              setToggleModal(true);
              setCurMovie(movie);
            }}
          />
        ))}
      </div>
    </>
  );
}

export default Home;
