import random
import json
from . import config
from . import database

class BattleshipGame:
    """Manages the state and logic of a single game of Battleship."""
    def __init__(self, game_id, player1_name="LLM_1", player2_name="LLM_2"):
        self.game_id = game_id
        self.players = {
            player1_name: {"board": self._create_board(), "ships": self._create_ships()},
            player2_name: {"board": self._create_board(), "ships": self._create_ships()},
        }
        self.player_names = [player1_name, player2_name]
        self.turn = 0
        self.winner = None
        self._place_all_ships_randomly()
        database.save_initial_boards(self.game_id, self.players)

    def _create_board(self):
        """Creates an empty board."""
        return [["W" for _ in range(config.GRID_SIZE)] for _ in range(config.GRID_SIZE)]

    def _create_ships(self):
        """Creates a deep copy of the ship configuration for a player."""
        return [
            {"name": ship["name"], "length": ship["length"], "hits": 0, "sunk": False, "positions": []}
            for ship in config.SHIPS_CONFIG
        ]

    def _place_all_ships_randomly(self):
        """Randomly places all ships for both players."""
        for player_data in self.players.values():
            for ship in player_data["ships"]:
                self._place_single_ship(player_data["board"], ship)

    def _place_single_ship(self, board, ship):
        """Places one ship on the board, ensuring no collisions."""
        placed = False
        while not placed:
            horizontal = random.choice([True, False])
            row = random.randint(0, config.GRID_SIZE - 1)
            col = random.randint(0, config.GRID_SIZE - 1)
            if self._can_place(board, ship["length"], row, col, horizontal):
                for i in range(ship["length"]):
                    if horizontal:
                        board[row][col + i] = "S"
                        ship["positions"].append((row, col + i))
                    else:
                        board[row + i][col] = "S"
                        ship["positions"].append((row + i, col))
                placed = True

    def _can_place(self, board, length, row, col, horizontal):
        """Checks if a ship can be placed at a given location."""
        if horizontal:
            if col + length > config.GRID_SIZE: return False
            return all(board[row][col + i] == "W" for i in range(length))
        else:
            if row + length > config.GRID_SIZE: return False
            return all(board[row + i][col] == "W" for i in range(length))

    def get_opponent_view(self, player_name):
        """Returns the opponent's board as seen by the player (no ships visible)."""
        opponent_name = self.player_names[1] if player_name == self.player_names[0] else self.player_names[0]
        opponent_board = self.players[opponent_name]["board"]
        return [
            [cell if cell in ["H", "M"] else "W" for cell in row]
            for row in opponent_board
        ]

    def process_shot(self, player_name, row, col):
        """Processes a shot, updates the board, and returns the result."""
        opponent_name = self.player_names[1] if player_name == self.player_names[0] else self.player_names[0]
        opponent_data = self.players[opponent_name]
        target_cell = opponent_data["board"][row][col]
        result = ""

        if target_cell == "S":
            opponent_data["board"][row][col] = "H"
            result = "HIT"
            for ship in opponent_data["ships"]:
                if (row, col) in ship["positions"]:
                    ship["hits"] += 1
                    if ship["hits"] == ship["length"]:
                        ship["sunk"] = True
                        result = f"SUNK {ship['name']}"
                    break
        elif target_cell == "W":
            opponent_data["board"][row][col] = "M"
            result = "MISS"
        else: # Already shot here
            result = "DUPLICATE"

        self._check_win_condition()
        
        # Record the turn to the database
        board_views = {
            self.player_names[0]: self.get_opponent_view(self.player_names[0]),
            self.player_names[1]: self.get_opponent_view(self.player_names[1]),
        }
        # The database schema has fixed column names, so we map our dynamic players to them.
        database.record_turn(
            self.game_id, 
            self.turn, 
            player_name, 
            (row, col), 
            result, 
            {
                "LLM_1": board_views[self.player_names[0]],
                "LLM_2": board_views[self.player_names[1]],
            }
        )
        
        return result

    def _check_win_condition(self):
        """Checks if a player has won the game."""
        for name, data in self.players.items():
            if all(ship["sunk"] for ship in data["ships"]):
                self.winner = self.player_names[1] if name == self.player_names[0] else self.player_names[0]
                break
