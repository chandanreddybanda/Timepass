import os
import json
import time
import random
import requests
import logging
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from . import config

# --- Logging Setup ---
# The logger is now configured in main.py. We just get it here.
logger = logging.getLogger(__name__)

# --- Model Management ---
initialized_models = {}

shot_schema = {
    "type": "object",
    "properties": {
        "row": {"type": "integer", "description": "The row to target (0-9)."},
        "col": {"type": "integer", "description": "The column to target (0-9)."},
    },
    "required": ["row", "col"],
}

def initialize_models():
    """Initializes the generative models based on the player configurations."""
    player_configs = [config.PLAYER1_CONFIG, config.PLAYER2_CONFIG]
    for player_config in player_configs:
        player_name = player_config["name"]
        provider = player_config["provider"]
        
        if provider == "google":
            api_key = os.environ.get(player_config["api_key_env"])
            if not api_key:
                logger.warning(f"API key '{player_config['api_key_env']}' not found for {player_name}. This player will use random moves.")
                initialized_models[player_name] = {"provider": "random"}
                continue
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(
                    model_name=player_config["model"],
                    generation_config={
                        "response_mime_type": "application/json",
                        "temperature": player_config["temperature"],
                    },
                )
                initialized_models[player_name] = {"provider": "google", "instance": model}
                logger.info(f"Successfully initialized Google model '{player_config['model']}' for player {player_name}.")
            except Exception as e:
                logger.error(f"Failed to initialize Google model for {player_name}. Error: {e}. This player will use random moves.")
                initialized_models[player_name] = {"provider": "random"}

        elif provider == "ollama":
            initialized_models[player_name] = {"provider": "ollama", "config": player_config}
            logger.info(f"Configured Ollama model '{player_config['model']}' for player {player_name}.")
        
        else:
            logger.warning(f"Unknown provider '{provider}' for {player_name}. This player will use random moves.")
            initialized_models[player_name] = {"provider": "random"}


def get_llm_move(player_name, opponent_view, own_ships_status, past_moves):
    """
    Gets a valid move from the appropriate LLM, with a self-correcting retry strategy.
    """
    model_info = initialized_models.get(player_name, {"provider": "random"})
    error_history = []

    for attempt in range(config.LLM_RETRY_ATTEMPTS):
        error_context = ""
        if error_history:
            error_context = "\nIMPORTANT: You have made invalid moves. Please correct your strategy based on the following errors:\n"
            for error in error_history:
                error_context += f"- {error}\n"
            error_context += "Choose a new, valid coordinate from the available 'W' cells."

        prompt = f"""
        You are a world-class Battleship player, {player_name}. It's your turn.
        Your goal: Sink all enemy ships on the 10x10 grid.
        Coordinates are (row, col), from (0, 0) to (9, 9).
        'W' = Water (unknown), 'H' = Hit, 'M' = Miss.
        {error_context}
        Your Fleet Status: {json.dumps(own_ships_status, indent=2)}
        Enemy Waters (Your View): {json.dumps(opponent_view, indent=2)}
        Your Recent Moves (last 10): {json.dumps(past_moves[-10:], indent=2)}
        Analyze the board. Think strategically. Provide your next shot as a JSON object with 'row' and 'col'.
        Do not fire at a location you have already targeted ('H' or 'M').
        """
        logger.info(f"Attempt {attempt+1} for {player_name}. Prompt:\n{prompt}")

        try:
            if model_info["provider"] == "google":
                move = _get_google_move(player_name, model_info["instance"], prompt)
            elif model_info["provider"] == "ollama":
                move = _get_ollama_move(player_name, model_info["config"], prompt)
            else:
                break

            row, col = move["row"], move["col"]
            if not (0 <= row < config.GRID_SIZE and 0 <= col < config.GRID_SIZE):
                error_history.append(f"Your choice ({row}, {col}) was out of bounds. The grid is {config.GRID_SIZE}x{config.GRID_SIZE}.")
                logger.warning(f"Invalid move from {player_name}: out of bounds.")
            elif opponent_view[row][col] != 'W':
                error_history.append(f"Your choice ({row}, {col}) was invalid because that location has already been targeted (it is '{opponent_view[row][col]}').")
                logger.warning(f"Invalid move from {player_name}: location already targeted.")
            else:
                # --- FIX: Restore the command-line log for a successful move ---
                provider_name = model_info.get("provider", "Unknown").capitalize()
                print(f"{player_name} ({provider_name}) chooses ({row}, {col}).")
                return row, col

        except Exception as e:
            error_history.append(f"The model returned an invalid response. Error: {e}")
            logger.error(f"Error processing LLM response for {player_name} (attempt {attempt+1}): {e}")
            time.sleep(2)

    return get_random_move(opponent_view, player_name)


def _get_google_move(player_name, model, prompt):
    """Makes a single API call to a Google (Gemini) model."""
    full_prompt = [prompt, "Output JSON:", json.dumps(shot_schema, indent=2)]
    response = model.generate_content(
        full_prompt,
        safety_settings={
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
    )
    logger.info(f"Raw Google response for {player_name}: {response.text}")
    return json.loads(response.text)


def _get_ollama_move(player_name, player_config, prompt):
    """Makes a single API call to a local Ollama model."""
    payload = {
        "model": player_config["model"],
        "prompt": prompt,
        "format": "json",
        "stream": False,
        "options": {"temperature": player_config["temperature"]}
    }
    response = requests.post(
        player_config["api_base"],
        json=payload,
        timeout=config.LLM_REQUEST_TIMEOUT
    )
    response.raise_for_status()
    response_data = response.json()
    logger.info(f"Raw Ollama response for {player_name}: {response_data}")
    return json.loads(response_data.get("response", "{}"))


def get_random_move(opponent_view, player_name="Player"):
    """Generates a random valid move as a fallback."""
    logger.warning(f"Player {player_name} is making a random move after failing all retry attempts.")
    print(f"Player {player_name} is making a random move.")
    while True:
        row, col = random.randint(0, 9), random.randint(0, 9)
        if opponent_view[row][col] == 'W':
            print(f"{player_name} (Random) chooses ({row}, {col}).")
            return row, col