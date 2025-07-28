import sqlite3
import json
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # This will enable CORS for all routes
DB_FILE = "battleship.db"

def query_db(query, args=(), one=False):
    """Helper function to query the database and return results."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/')
def index():
    """Serves the main HTML visualizer page."""
    return send_from_directory('.', 'GameVisualize.html')

@app.route('/api/summary')
def get_summary():
    """Provides a dynamic summary of win counts for all players."""
    # Get all distinct winners from the database
    winners_query = query_db("SELECT DISTINCT winner FROM games WHERE winner IS NOT NULL")
    player_names = [row['winner'] for row in winners_query]
    
    # Get all games to count wins
    all_games = query_db("SELECT winner FROM games WHERE winner IS NOT NULL")
    
    win_counts = {name: 0 for name in player_names}
    for game in all_games:
        if game['winner'] in win_counts:
            win_counts[game['winner']] += 1
            
    total_games = len(all_games)
    
    return jsonify({
        "total_games": total_games,
        "win_counts": win_counts
    })

@app.route('/api/games')
def get_games():
    """Returns a list of all completed games with player names."""
    games = query_db("SELECT game_id, winner, turns, player1_name, player2_name FROM games WHERE winner IS NOT NULL ORDER BY game_id DESC")
    return jsonify([dict(ix) for ix in games])

@app.route('/api/game/<int:game_id>')
def get_game_details(game_id):
    """Returns the detailed history for a specific game."""
    # Get all moves for the game
    moves = query_db("SELECT * FROM moves WHERE game_id = ? ORDER BY turn ASC", [game_id])
    if not moves:
        return jsonify({"error": "Game not found or has no moves"}), 404
        
    # Get the initial board placements
    boards = query_db("SELECT player_name, ship_placements FROM boards WHERE game_id = ?", [game_id])
    
    final_boards = {}
    for board in boards:
        final_boards[board['player_name']] = json.loads(board['ship_placements'])

    # Structure the history
    history = []
    for move in moves:
        history.append({
            "turn": move['turn'],
            "player": move['player_name'],
            "shot": (move['shot_row'], move['shot_col']),
            "result": move['result'],
            "boards": {
                "LLM_1": json.loads(move['board_state_llm1']),
                "LLM_2": json.loads(move['board_state_llm2'])
            }
        })
        
    game_info = query_db("SELECT * FROM games WHERE game_id = ?", [game_id], one=True)

    return jsonify({
        "game_id": game_id,
        "winner": game_info['winner'],
        "turns": game_info['turns'],
        "player1_name": game_info['player1_name'],
        "player2_name": game_info['player2_name'],
        "history": history,
        "final_boards": final_boards
    })

@app.route('/api/game/latest')
def get_latest_game():
    """
    Provides data for the most recent game, whether it's finished or in-progress.
    This is used for the "Live View".
    """
    latest_game = query_db("SELECT game_id FROM games ORDER BY game_id DESC LIMIT 1", one=True)
    if not latest_game:
        return jsonify({"error": "No games found"}), 404
    return get_game_details(latest_game['game_id'])

@app.route('/api/raw/<string:table_name>')
def get_raw_table(table_name):
    """Returns all data from a specified table."""
    # Whitelist allowed table names to prevent SQL injection
    if table_name not in ['games', 'boards', 'moves']:
        return jsonify({"error": "Invalid table name"}), 400
    
    data = query_db(f"SELECT * FROM {table_name}")
    return jsonify([dict(ix) for ix in data])


if __name__ == '__main__':
    app.run(debug=True, port=5001)
