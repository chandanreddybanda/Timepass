import sqlite3
import json
from . import config

def init_db():
    """Initializes the SQLite database and creates tables if they don't exist."""
    conn = sqlite3.connect(config.DB_FILE)
    cursor = conn.cursor()
    
    # Games table: Stores overall information for each game
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS games (
        game_id INTEGER PRIMARY KEY AUTOINCREMENT,
        winner TEXT,
        turns INTEGER,
        start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        end_time DATETIME,
        player1_name TEXT,
        player2_name TEXT
    )
    """)
    
    # Add columns if they don't exist for backward compatibility
    try:
        cursor.execute("ALTER TABLE games ADD COLUMN player1_name TEXT")
        cursor.execute("ALTER TABLE games ADD COLUMN player2_name TEXT")
    except sqlite3.OperationalError:
        # Columns likely already exist
        pass
    
    # Boards table: Stores the initial ship placements for each player in a game
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS boards (
        board_id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_id INTEGER,
        player_name TEXT,
        ship_placements TEXT,
        FOREIGN KEY (game_id) REFERENCES games (game_id)
    )
    """)
    
    # Moves table: Records every single move made in every game
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS moves (
        move_id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_id INTEGER,
        turn INTEGER,
        player_name TEXT,
        shot_row INTEGER,
        shot_col INTEGER,
        result TEXT,
        board_state_llm1 TEXT,
        board_state_llm2 TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (game_id) REFERENCES games (game_id)
    )
    """)
    
    conn.commit()
    conn.close()
    print("Database initialized.")

def save_initial_boards(game_id, players):
    """Saves the starting board layouts to the database."""
    conn = sqlite3.connect(config.DB_FILE)
    cursor = conn.cursor()
    for name, data in players.items():
        cursor.execute(
            "INSERT INTO boards (game_id, player_name, ship_placements) VALUES (?, ?, ?)",
            (game_id, name, json.dumps(data["board"]))
        )
    conn.commit()
    conn.close()

def record_turn(game_id, turn_number, player_name, shot, result, board_views):
    """Records the game state for the current turn into the database."""
    conn = sqlite3.connect(config.DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO moves (game_id, turn, player_name, shot_row, shot_col, result, board_state_llm1, board_state_llm2)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            game_id,
            turn_number,
            player_name,
            shot[0],
            shot[1],
            result,
            json.dumps(board_views["LLM_1"]),
            json.dumps(board_views["LLM_2"]),
        )
    )
    conn.commit()
    conn.close()

def create_new_game(player1_name, player2_name):
    """Creates a new game entry in the DB and returns the game_id."""
    conn = sqlite3.connect(config.DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO games (player1_name, player2_name, turns) VALUES (?, ?, 0)",
        (player1_name, player2_name)
    )
    game_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return game_id

def update_game_winner(game_id, winner, turns):
    """Updates the game record with the winner and final turn count."""
    conn = sqlite3.connect(config.DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE games SET winner = ?, turns = ?, end_time = CURRENT_TIMESTAMP WHERE game_id = ?",
        (winner, turns, game_id)
    )
    conn.commit()
    conn.close()
