import time
import os
import logging
from src import config, database, game, llm

def setup_logging():
    """Configures the root logger to write to all_logs.log."""
    # Wipe the log file for a clean run
    if os.path.exists("all_logs.log"):
        os.remove("all_logs.log")
        print("Previous log file wiped.")

    # Configure logging
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_handler = logging.FileHandler('all_logs.log')
    log_handler.setFormatter(log_formatter)
    
    # Get the root logger and add the handler
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Prevent duplicate handlers if this function is ever called again
    if not root_logger.handlers:
        root_logger.addHandler(log_handler)
    
    logging.info("Logging configured.")


def run_simulation():
    """Runs the full tournament between two configured LLM players."""
    
    setup_logging()

    # Initialize the LLM models based on the configuration
    llm.initialize_models()
    
    # Initialize the database
    database.init_db()

    player_configs = {
        config.PLAYER1_CONFIG["name"]: config.PLAYER1_CONFIG,
        config.PLAYER2_CONFIG["name"]: config.PLAYER2_CONFIG,
    }

    for i in range(config.NUMBER_OF_GAMES):
        player1_name = config.PLAYER1_CONFIG["name"]
        player2_name = config.PLAYER2_CONFIG["name"]
        
        game_id = database.create_new_game(player1_name, player2_name)
        logging.info(f"--- Starting Game {game_id}/{config.NUMBER_OF_GAMES} ({player1_name} vs {player2_name}) ---")
        print(f"\n--- Starting Game {game_id}/{config.NUMBER_OF_GAMES} ({player1_name} vs {player2_name}) ---")
        
        current_game = game.BattleshipGame(
            game_id,
            player1_name=player1_name,
            player2_name=player2_name
        )
        
        player_moves = {p_name: [] for p_name in player_configs.keys()}

        while not current_game.winner:
            current_game.turn += 1
            current_player_name = current_game.player_names[(current_game.turn - 1) % 2]
            current_player_config = player_configs[current_player_name]
            
            print(f"\nTurn {current_game.turn}: {current_player_name}'s move.")

            opponent_view = current_game.get_opponent_view(current_player_name)
            own_ships_status = [
                {"name": s["name"], "length": s["length"], "hits": s["hits"], "sunk": s["sunk"]}
                for s in current_game.players[current_player_name]["ships"]
            ]

            row, col = llm.get_llm_move(
                current_player_name,
                opponent_view,
                own_ships_status,
                player_moves[current_player_name]
            )
            
            player_moves[current_player_name].append({"shot": (row, col)})
            result = current_game.process_shot(current_player_name, row, col)
            print(f"Result: {result}")
            
            player_moves[current_player_name][-1]["result"] = result
            
            # Apply the correct rate limit for the current player
            sleep_time = current_player_config["api_sleep_time"]
            if sleep_time > 0:
                print(f"Waiting for {sleep_time} seconds...")
                time.sleep(sleep_time)

        logging.info(f"--- Game {game_id} Over! Winner: {current_game.winner} in {current_game.turn} turns. ---")
        print(f"\n--- Game {game_id} Over! Winner: {current_game.winner} in {current_game.turn} turns. ---")
        database.update_game_winner(game_id, current_game.winner, current_game.turn)

    print("\n--- Simulation Complete ---")
    logging.info("--- Simulation Complete ---")

if __name__ == "__main__":
    run_simulation()