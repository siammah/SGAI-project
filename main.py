import argparse
import os
from endpoints.data_parser import DataParser
from endpoints.heuristic_interface import HeuristicInterface
from endpoints.training_interface import TrainInterface
from endpoints.inference_interface import InferInterface

from gameplay.scorekeeper import ScoreKeeper
from gameplay.ui import UI
from gameplay.enums import ActionCost
from model_training.rl_training import train

from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

import uuid
import pandas as pd
import random

# random comment 
class Main(object):
    """
    Base class for the SGAI 2025 game
    """
    def __init__(self, mode, log, game_time=60):
        #Cursor
        self.data_fp = "data/data"
        self.data_parser = DataParser(self.data_fp, test_images_folder="test_images")

        #original
        #self.data_fp = os.getenv("SGAI_DATA", default='data')
        #self.data_parser = DataParser(self.data_fp)

        shift_length = game_time  # now in seconds
        capacity = 12
        total_rounds = 3  # Number of rounds before final game over
        self.scorekeeper = ScoreKeeper(shift_length, capacity, total_rounds)

        if mode == 'heuristic':   # Run in background until all humanoids are processed
            # TODO investigate why this just kills everything (follow humanoid to prediction to actions to scorekeeper)
            simon = HeuristicInterface(None, None, None, display = False)
            while len(self.data_parser.unvisited) > 0:
                if self.scorekeeper.remaining_time <= 0:
                    print('Ran out of time')
                    break
                else:
                    humanoid = self.data_parser.get_random()
                    action = simon.get_model_suggestion(humanoid, self.scorekeeper.at_capacity())
                    if action == ActionCost.SKIP:
                        self.scorekeeper.skip(humanoid)
                    elif action == ActionCost.SQUISH:
                        self.scorekeeper.squish(humanoid)
                    elif action == ActionCost.SAVE:
                        self.scorekeeper.save(humanoid)
                    elif action == ActionCost.SCRAM:
                        self.scorekeeper.scram(humanoid)
                    else:
                        raise ValueError("Invalid action suggested")
            #if log:
               # self.scorekeeper.save_log()
            print("RL equiv reward:",self.scorekeeper.get_cumulative_reward())
            print(self.scorekeeper.get_score())
        elif mode == 'train':  # RL training script
            env = TrainInterface(None, None, None, self.data_parser, self.scorekeeper, display=False,)
            train(env)
        elif mode == 'infer':  # RL training script
            simon = InferInterface(None, None, None, self.data_parser, self.scorekeeper, display=False,)
            while len(simon.data_parser.unvisited) > 0:
                if simon.scorekeeper.remaining_time <= 0:
                    break
                else:
                    humanoid = self.data_parser.get_random()
                    simon.act(humanoid)
            self.scorekeeper = simon.scorekeeper
           # if log:
               # self.scorekeeper.save_log()
            print("RL equiv reward:",self.scorekeeper.get_cumulative_reward())
            print(self.scorekeeper.get_score())
        else: # Launch UI gameplay
            self.ui = UI(self.data_parser, self.scorekeeper, self.data_fp, log = log, suggest = False)


def terminate_game_log(game_id):
    """Remove all log entries for the given game_id from log.csv, robustly handling legacy/space-delimited rows."""
    import os
    log_path = 'log.csv'
    header = [
        "Action", "FileName", "Role", "State", "Posture", "Weather", "TimeOfDay",
        "TimeRemaining", "Capacity", "GameNumber", "RoundNumber", "GameInstanceID"
    ]
    if not os.path.isfile(log_path):
        print(f"Log file {log_path} does not exist.")
        return
    with open(log_path, 'r') as f:
        lines = f.readlines()
    # Find the header line (must contain all header columns)
    header_line_idx = None
    for i, line in enumerate(lines):
        if all(col in line for col in header):
            header_line_idx = i
            break
    if header_line_idx is None:
        print("No valid header found in log file.")
        return
    # Parse rows after the header
    data_lines = lines[header_line_idx+1:]
    valid_rows = []
    for line in data_lines:
        # Try splitting by comma first, then by two or more spaces
        if line.strip() == '':
            continue
        if ',' in line:
            row = [x.strip() for x in line.strip().split(',')]
        else:
            import re
            row = re.split(r'\s{2,}', line.strip())
        if len(row) != len(header):
            continue  # skip malformed rows
        row_dict = dict(zip(header, row))
        if row_dict.get('GameInstanceID') != game_id:
            valid_rows.append(row_dict)
    # Write back clean CSV
    import csv
    with open(log_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for row in valid_rows:
            writer.writerow(row)
    print(f"Removed log entries for game ID {game_id}. Cleaned log file written.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Team Quantum Game CLI")
    parser.add_argument('command', nargs='?', default=None, help="Command to run (e.g., terminate)")
    parser.add_argument('--game_id', type=str, help="Game instance ID to terminate")
    parser.add_argument('--log', action='store_true', help="Enable logging")
    parser.add_argument('--mode', type=str, default=None, help="Game mode")
    parser.add_argument('--game_time', type=str, default='60', help="Game time in seconds, or 'random' for a random time between 15 and 60 seconds")
    args = parser.parse_args()

    if args.command == 'terminate' and args.game_id:
        terminate_game_log(args.game_id)
    elif args.command == 'endgame':
        mode = args.mode or 'ui'
        log = args.log
        game = Main(mode, log)
        if hasattr(game, 'scorekeeper'):
            game.scorekeeper.end_game()
            print("Game ended and meters reset to 500.")
    else:
        # Existing logic for running the game
        mode = args.mode or 'ui'
        log = args.log
        if args.game_time == 'random':
            game_time = random.randint(15, 60)
            print(f"Random game time selected: {game_time} seconds")
        else:
            try:
                game_time = int(args.game_time)
            except ValueError:
                print("Invalid value for --game_time. Must be an integer or 'random'. Defaulting to 60 seconds.")
                game_time = 60
        game = Main(mode, log, game_time=game_time)
        # Print the game instance ID after game creation
        if hasattr(game, 'scorekeeper') and hasattr(game.scorekeeper, 'game_id'):
            print(f"Game Instance ID: {game.scorekeeper.game_id}")
