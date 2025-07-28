import os

# --- Environment ---
# Create a .env file in the root directory to store your API keys.
# Example .env content:
# GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
# ANTHROPIC_API_KEY="YOUR_ANTHROPIC_API_KEY" 
# Ollama does not require an API key by default.

# --- Player 1 Configuration ---
# PLAYER1_CONFIG = {
#     # "name": "Gemini-Flash",
#     # "provider": "google", # 'google' or 'ollama'
#     # "model": "gemini-2.5-flash-lite",
#     # "api_key_env": "GEMINI_API_KEY", # Environment variable for the API key
#     # "api_base": None, # Not needed for Google
#     # "api_sleep_time": 4, # Seconds to wait after this player's turn
#     # "temperature": 1.0,
# }

PLAYER1_CONFIG = {
    "name": "Gemma-1",
    "provider": "ollama", # 'google' or 'ollama'
    "model": "gemma3:1b", # The model name as defined in Ollama
    "api_key_env": None, # Not needed for local Ollamaoll
    "api_base": "http://localhost:11434/api/generate", # Ollama's API endpoint
    "api_sleep_time": 0, # Local models are fast, so no sleep time is needed
    "temperature": 0.8,
}

# --- Player 2 Configuration ---
# This is an example of how to configure a local Ollama model.
PLAYER2_CONFIG = {
    "name": "Gemma-2",
    "provider": "ollama", # 'google' or 'ollama'
    "model": "gemma3:1b", # The model name as defined in Ollama
    "api_key_env": None, # Not needed for local Ollamaoll
    "api_base": "http://localhost:11434/api/generate", # Ollama's API endpoint
    "api_sleep_time": 0, # Local models are fast, so no sleep time is needed
    "temperature": 0.8,
}


# --- General Game Settings ---
NUMBER_OF_GAMES = 2 # Set to a higher number for a full tournament
GRID_SIZE = 10
SHIPS_CONFIG = [
    {"name": "Carrier", "length": 5},
    {"name": "Battleship", "length": 4},
    {"name": "Cruiser", "length": 3},
    {"name": "Submarine", "length": 3},
    {"name": "Destroyer", "length": 2},
]

# --- Database ---
DB_FILE = "battleship.db"

# --- LLM Settings ---
LLM_REQUEST_TIMEOUT = 60 # Increased timeout for potentially slower local models
LLM_RETRY_ATTEMPTS = 3
