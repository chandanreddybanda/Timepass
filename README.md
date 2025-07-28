# LLM Battleship Tournament

This project simulates a series of Battleship games between two configurable LLM-powered players to test their strategic capabilities. The results, including every move and board state, are stored in a SQLite database. A web-based visualizer is provided to review and analyze the games.

This project has been refactored to support pitting two different LLM players against each other, including local models run with **Ollama**.

## Project Structure

```
/
├── src/
│   ├── __init__.py       # Makes 'src' a Python package
│   ├── config.py         # All configuration, constants, and player setups
│   ├── database.py       # Handles SQLite database interactions
│   ├── game.py           # Core Battleship game logic
│   └── llm.py            # Logic for initializing and interacting with different LLM providers
├── .env                  # Stores API keys (ignored by git)
├── api.py                # Flask server to provide game data to the visualizer
├── main.py               # Main script to run the game simulation
├── GameVisualize.html    # The web-based visualizer
└── battleship.db         # SQLite database file (created after running main.py)
```

## Setup

1.  **Clone the repository.**

2.  **Install dependencies:**
    ```bash
    pip install google-generativeai flask flask-cors requests
    ```

3.  **(Optional) Install and run Ollama:**
    If you want to use a local model, you need to have [Ollama](https://ollama.com/) installed and running. You also need to pull the model you want to use, for example:
    ```bash
    ollama pull llama3
    ```

4.  **Create the environment file:**
    Create a file named `.env` in the root directory. Add the API keys for any cloud-based models you want to test. Ollama does not require a key.
    
    For the default configuration (Gemini vs. Ollama), your `.env` file only needs the Gemini key:
    ```
    GEMINI_API_KEY="YOUR_API_KEY_HERE"
    ```

5.  **Configure Players:**
    Open `src/config.py` to edit the `PLAYER1_CONFIG` and `PLAYER2_CONFIG` dictionaries. This is the most important step.
    
    -   **`provider`**: Set to `"google"` for Gemini models or `"ollama"` for local models.
    -   **`model`**: The specific model name (e.g., `"gemini-1.5-flash"` or `"llama3"`).
    -   **`api_key_env`**: The name of the environment variable holding the API key (set to `None` for Ollama).
    -   **`api_base`**: The API endpoint URL (set to `None` for Google, or your local Ollama URL, typically `"http://localhost:11434/api/generate"`).
    -   **`api_sleep_time`**: The delay after a player's turn to respect rate limits.

## How to Run

The process involves two main steps: running the simulation to populate the database and then running the web server to view the results.

**Step 1: Run the Game Simulation**

Execute the `main.py` script. This will read your configuration, initialize the configured LLM models, and play the specified number of games.

```bash
python3 main.py
```
This will create or update the `battleship.db` file with the new game data.

**Step 2: Run the Web Server and View the Visualization**

To view the results, start the Flask web server:

```bash
python3 api.py
```

The server will start and run in the foreground. Now, open your web browser and navigate to:

**http://127.0.0.1:5001**

You should see the LLM Battleship Tournament visualizer, ready to display the results of your custom matchup.