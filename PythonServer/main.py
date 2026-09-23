from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from FindMoviesPlaying import get_movies_with_images

app = FastAPI(title="Caribbean Cinemas")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Allow any origin
    allow_credentials=False,  # Must be False when using "*"
    allow_methods=["*"],      # Allow all HTTP methods
    allow_headers=["*"],      # Allow all headers
)

@app.get("/")
def welcome_message():
    return get_movies_with_images() 

@app.get("/seatings")
def get_seatings():
    return {}