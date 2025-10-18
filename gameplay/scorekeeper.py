from gameplay.enums import ActionCost, ActionState, Points, Multiplier
import pandas as pd
import os   
import re   
import uuid
import random
import datetime


MAP_ACTION_STR_TO_INT = {s.value:i for i,s in enumerate(ActionState)}
MAP_ACTION_INT_TO_STR = [s.value for s in ActionState]

class ScoreKeeper(object):
    # Class variable to track if any game has been played before
    _first_game_ever = True
    
    def __init__(self, shift_len, capacity, total_rounds=1, game_id=None, operator_name="", player_name=""):
        
        self.shift_len = int(shift_len)  # seconds
        self.capacity = capacity
        self.total_rounds = total_rounds
        self.current_round = 1
        
        self.actions = 4
        
        self.logger = []
        self.all_logs = []
        
        self.game_id = game_id or str(uuid.uuid4())
        self.terminated = False
        
        # Set timestamp when game starts
        self.game_start_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Include milliseconds
        
        # Store operator and player names
        self.operator_name = operator_name
        self.player_name = player_name
        
        # Initialize meters only once per game
        self.military = 500
        self.hra = 500
        self.scientist = 500
        self.medic = 500

        self.total_score = {
            "humans_saved": 0, 
            "humans_killed": 0,
            "zombies_saved": 0,
            "zombies_killed": 0,
            "corpses_encountered": 0
        }

        self.round_score = {
            "humans_saved": 0,
            "humans_killed": 0,
            "zombies_saved": 0,
            "zombies_killed": 0,
            "corpses_encountered": 0
        }



        self.reset()
    
    def _clamp_meter_value(self, value):
        """Clamp meter values between 0 and 1000"""
        return max(0, min(1000, value))
    
    def _calculate_meter_changes(self, humanoid, action):
        """
        Calculate meter changes based on the specific requirements.
        Returns a dict with meter changes: {'military': change, 'hra': change, 'scientist': change, 'medic': change}
        """
        changes = {'military': 0, 'hra': 0, 'scientist': 0, 'medic': 0}
        
        if humanoid.is_zombie():
            if action == 'save':
                # Zombie save: Military: -40, Doctor: -40, HRA: +40, Scientist: +80
                changes['military'] = -40
                changes['medic'] = -40
                changes['hra'] = 40
                changes['scientist'] = 80
            elif action == 'skip':

                changes['military'] = -20
            elif action == 'squish':

                changes['military'] = 40
                changes['hra'] = -40
                changes['scientist'] = -20
                
        elif humanoid.is_corpse():
            if action == 'save':
                # Corpse save: Military: no change, Doctor: -20, HRA: no change, Scientist: no change
                changes['medic'] = -20
            elif action == 'skip':
                # Corpse skip: Military: -20, Doctor: no change, HRA: no change, Scientist: no change
                changes['military'] = -20
            elif action == 'squish':
                # Corpse squish: Military: no change, Doctor: no change, HRA: -20, Scientist: no change
                changes['hra'] = -20
                
        elif humanoid.is_healthy_business() or humanoid.is_healthy_doctor() or humanoid.is_healthy_elderly() or humanoid.is_healthy_police():
            if action == 'save':
                # Healthy baseline save: Military: +40, Doctor: no change, HRA: +40, Scientist: no change
                changes['military'] = 40
                changes['hra'] = 40
            elif action == 'skip':
                # Healthy baseline skip: Military: -20, Doctor: no change, HRA: no change, Scientist: no change
                changes['military'] = -20
            elif action == 'squish':
                # Healthy baseline squish: Military: -20, Doctor: -40, HRA: -40, Scientist: no change
                changes['military'] = -20
                changes['medic'] = -40
                changes['hra'] = -40
                
            # Apply role modifications
            if humanoid.is_healthy_business():
                if action == 'save':
                    changes['scientist'] += 20  # Business save: +20 Scientist
                elif action == 'squish':
                    changes['scientist'] += 60  # Business squish: +60 Scientist
            elif humanoid.is_healthy_doctor():
                if action == 'save':
                    changes['medic'] += 40  # Doctor save: +40 Doctor
                elif action == 'squish':
                    changes['medic'] -= 20  # Doctor squish: -20 Doctor
            elif humanoid.is_healthy_elderly():
                if action == 'save':
                    changes['military'] -= 80  # Elderly save: -80 Military
                    changes['medic'] += 20  # Elderly save: +20 Doctor
                elif action == 'skip':
                    changes['medic'] -= 20  # Elderly skip: -20 Doctor
            elif humanoid.is_healthy_police():
                if action == 'save':
                    changes['military'] += 40  # Police save: +40 Military
                    changes['hra'] -= 20  # Police save: -20 HRA
                elif action == 'skip':
                    changes['hra'] -= 20  # Police skip: -20 HRA
                elif action == 'squish':
                    changes['military'] -= 20  # Police squish: -20 Military
                
        elif humanoid.is_injured_business() or humanoid.is_injured_doctor() or humanoid.is_injured_elderly() or humanoid.is_injured_police():
            if action == 'save':
                # Injured baseline save: Military: -20, Doctor: +40, HRA: +40, Scientist: no change
                changes['military'] = -20
                changes['medic'] = 40
                changes['hra'] = 40
            elif action == 'skip':
                # Injured baseline skip: Military: no change, Doctor: -40, HRA: no change, Scientist: no change
                changes['medic'] = -40
            elif action == 'squish':
                # Injured baseline squish: Military: no change, Doctor: -40, HRA: -20, Scientist: no change
                changes['medic'] = -40
                changes['hra'] = -20
                
            # Apply role modifications
            if humanoid.is_injured_business():
                if action == 'save':
                    changes['scientist'] += 20  # Business save: +20 Scientist
                elif action == 'squish':
                    changes['scientist'] += 60  # Business squish: +60 Scientist
            elif humanoid.is_injured_doctor():
                if action == 'save':
                    changes['medic'] += 40  # Doctor save: +40 Doctor
                elif action == 'squish':
                    changes['medic'] -= 20  # Doctor squish: -20 Doctor
            elif humanoid.is_injured_elderly():
                if action == 'save':
                    changes['military'] -= 80  # Elderly save: -80 Military
                    changes['medic'] += 20  # Elderly save: +20 Doctor
                elif action == 'skip':
                    changes['medic'] -= 20  # Elderly skip: -20 Doctor
            elif humanoid.is_injured_police():
                if action == 'save':
                    changes['military'] += 40  # Police save: +40 Military
                    changes['hra'] -= 20  # Police save: -20 HRA
                elif action == 'skip':
                    changes['hra'] -= 20  # Police skip: -20 HRA
                elif action == 'squish':
                    changes['military'] -= 20  # Police squish: -20 Military
                
        return changes

    def _get_round_duration(self):
        """Get the duration for the current round"""
        if self.current_round == 1 and self._first_game_ever:
            # First round is always 120 seconds for the very first game
            return 120
        else:
            # Subsequent rounds are random between 30 and 90 seconds
            return random.randint(30, 90)
    
    def mark_game_played(self):
        """Mark that a game has been played (for tracking first game ever)"""
        self._first_game_ever = False

        
    def reset(self):
        """
        resets scorekeeper on new environment (per round)
        Only resets round-specific state, not meters.
        """
        self.ambulance = {
            "zombie": 0,
            "injured": 0,
            "healthy": 0,
            "corpse": 0
        }
        self.round_score = {
            "humans_saved": 0,
            "humans_killed": 0,
            "zombies_saved": 0,
            "zombies_killed": 0,
            "corpses_encountered": 0
        }



        # Remove meter resets here!
        # self.military = 500
        # self.hra = 500
        # self.scientist = 500
        # self.medic = 500

        # Set remaining time based on current round
        self.remaining_time = self._get_round_duration()
        # Store the round duration for logging
        self.round_duration = self.remaining_time
        
        self.all_logs.append(self.logger)
        self.logger = []
    
    def log(self, humanoid, action, game_number, round_number):
        if self.terminated:
            return
        """
        logs current action taken against a humanoid
        humanoid : the humanoid presented
        action : the action taken
        game_number : the current game number (from UI)
        round_number : the current round number (from UI)
        """
        # Extract detailed state info
        state_info = humanoid.state if isinstance(humanoid.state, dict) else {}
        log_entry = {
            "action": action,
            "humanoid_fp": humanoid.fp,
            "role": state_info.get("role", ""),
            "state": state_info.get("parent", ""),
            "posture": state_info.get("posture", ""),
            "weather": state_info.get("weather", ""),
            "time": state_info.get("time", ""),
            "remaining_time": self.remaining_time,
            "round_duration": self.round_duration,
            "capacity": self.get_current_capacity(),
            "military": self.military,
            "hra": self.hra,
            "scientist": self.scientist,
            "medic": self.medic,
            "game_number": game_number,
            "round_number": round_number,
            "game_instance_id": self.game_id,
            "start_timestamp": self.game_start_timestamp,
            "operator_name": self.operator_name,
            "player_name": self.player_name
        }
        self.logger.append(log_entry)
        self.save_log_entry(log_entry)  # Save just this action

# IF YOU DON"T WANT TO LOG, JUST CALL TERMINATE_GAME()
 # python main.py terminate --game_id <GAME_ID>


    def save_log_entry(self, log_entry):
        """
        Saves a single log.csv file (comma-separated, for Excel/Sheets)
        and a log_pretty.txt file (aligned columns, for human reading).
        """

        columns = [
            ("Action", "action"),
            ("FileName", "humanoid_fp"),
            ("Role", "role"),
            ("State", "state"),
            ("Posture", "posture"),  
            ("Weather", "weather"),
            ("TimeOfDay", "time"),
            ("TimeRemaining", "remaining_time"),
            ("RoundDuration", "round_duration"),
            ("Capacity", "capacity"),
            ("Military", "military"),
            ("HRA", "hra"),
            ("Scientist", "scientist"),
            ("Medic", "medic"),
            ("GameNumber", "game_number"),
            ("RoundNumber", "round_number"),
            ("GameInstanceID", "game_instance_id"),
            ("StartTimestamp", "start_timestamp"),
            ("OperatorName", "operator_name"),
            ("PlayerName", "player_name")
        ]
        col_names = [c[0] for c in columns]
        row_dict = {c[0]: log_entry.get(c[1], "") for c in columns}

        # --- Write CSV (comma-separated, for Excel/Sheets) ---
        df = pd.DataFrame([row_dict], columns=col_names)
        file_exists = os.path.isfile('log.csv')
        write_header = not file_exists or os.path.getsize('log.csv') == 0
        df.to_csv('log.csv', mode='a', header=write_header, index=False)

        # --- Write Pretty Log (aligned columns, for human reading) ---
        pretty_file = 'log_pretty.txt'
        # Read all existing rows (if any)
        rows = []
        file_exists = os.path.isfile(pretty_file) and os.path.getsize(pretty_file) > 0
        if file_exists:
            with open(pretty_file, 'r') as f:
                lines = f.readlines()
            # Skip header
            for line in lines[1:]:
                row = re.split(r'  +', line.rstrip('\n'))
                if len(row) < len(col_names):
                    row += [''] * (len(col_names) - len(row))
                rows.append(row)
        # Add the new row
        new_row = [str(row_dict.get(col, "")) for col in col_names]
        rows.append(new_row)
        # Calculate max width for each column (header or any row)
        all_rows = [col_names] + rows
        widths = [max(len(str(r[i])) for r in all_rows) for i in range(len(col_names))]
        # Write all rows back out, aligned
        with open(pretty_file, 'w') as f:
            header = "  ".join(f"{col_names[i]:<{widths[i]}}" for i in range(len(col_names)))
            f.write(header + "\n")
            for r in rows:
                line = "  ".join(f"{r[i]:<{widths[i]}}" for i in range(len(col_names)))
                f.write(line + "\n")
        
        

    def save(self, humanoid):
        """
        saves the humanoid
        updates scorekeeper
        """
        print(f"[ScoreKeeper] save called: state={getattr(humanoid, 'state', None)}, ht={getattr(humanoid, 'ht', None)}")
        self.remaining_time -= ActionCost.SAVE.value
        
        # Apply meter changes using the calculation method
        changes = self._calculate_meter_changes(humanoid, 'save')
        self.military = self._clamp_meter_value(self.military + changes['military'])
        self.hra = self._clamp_meter_value(self.hra + changes['hra'])
        self.scientist = self._clamp_meter_value(self.scientist + changes['scientist'])
        self.medic = self._clamp_meter_value(self.medic + changes['medic'])
        
        # Simple scoring logic
        if humanoid.is_zombie():
            # Zombie saved - add to ambulance and count as saved
            self.ambulance["zombie"] += 1
            self.round_score["zombies_saved"] += 1
            self.total_score["zombies_saved"] += 1
            print(f"[ScoreKeeper] Zombie saved! Ambulance capacity now: {self.get_current_capacity()}, Ambulance contents: {self.ambulance}")
        elif humanoid.is_corpse():
            # Corpse saved - add to ambulance and count as encountered
            self.ambulance["corpse"] += 1
            self.round_score["corpses_encountered"] += 1
            self.total_score["corpses_encountered"] += 1
            print(f"[ScoreKeeper] Corpse saved - counted as encountered")
        else:
            # Human saved - add to ambulance and count as saved
            if humanoid.is_injured_business() or humanoid.is_injured_doctor() or humanoid.is_injured_elderly() or humanoid.is_injured_police():
                self.ambulance["injured"] += 1
            else:
                self.ambulance["healthy"] += 1
            self.round_score["humans_saved"] += 1
            self.total_score["humans_saved"] += 1
            print(f"[ScoreKeeper] Human saved! Ambulance capacity now: {self.get_current_capacity()}, Ambulance contents: {self.ambulance}")

        print(f"[ScoreKeeper] After save: military={self.military}, hra={self.hra}, scientist={self.scientist}, medic={self.medic}")

    def squish(self, humanoid):
        """
        squishes the humanoid
        updates scorekeeper
        """
        print(f"[ScoreKeeper] squish called: state={getattr(humanoid, 'state', None)}, ht={getattr(humanoid, 'ht', None)}")
        self.remaining_time -= ActionCost.SQUISH.value
        
        # Apply meter changes using the calculation method
        changes = self._calculate_meter_changes(humanoid, 'squish')
        self.military = self._clamp_meter_value(self.military + changes['military'])
        self.hra = self._clamp_meter_value(self.hra + changes['hra'])
        self.scientist = self._clamp_meter_value(self.scientist + changes['scientist'])
        self.medic = self._clamp_meter_value(self.medic + changes['medic'])
        
        # Simple scoring logic
        if humanoid.is_zombie():
            self.round_score["zombies_killed"] += 1
            self.total_score["zombies_killed"] += 1
            print(f"[ScoreKeeper] Zombie squished!")
        elif humanoid.is_corpse():
            # Corpses are already dead - can't be killed, but count as encountered
            self.round_score["corpses_encountered"] += 1
            self.total_score["corpses_encountered"] += 1
            print(f"[ScoreKeeper] Corpse squished - counted as encountered")
        else:
            # Human killed
            self.round_score["humans_killed"] += 1
            self.total_score["humans_killed"] += 1
            print(f"[ScoreKeeper] Human squished!")

        print(f"[ScoreKeeper] After squish: military={self.military}, hra={self.hra}, scientist={self.scientist}, medic={self.medic}")

    def skip(self, humanoid):
        """
        skips the humanoid
        updates scorekeeper
        """
        print(f"[ScoreKeeper] skip called: state={getattr(humanoid, 'state', None)}, ht={getattr(humanoid, 'ht', None)}")
        self.remaining_time -= ActionCost.SKIP.value
        
        # Apply meter changes using the calculation method
        changes = self._calculate_meter_changes(humanoid, 'skip')
        self.military = self._clamp_meter_value(self.military + changes['military'])
        self.hra = self._clamp_meter_value(self.hra + changes['hra'])
        self.scientist = self._clamp_meter_value(self.scientist + changes['scientist'])
        self.medic = self._clamp_meter_value(self.medic + changes['medic'])
        
        # Simple scoring logic
        if humanoid.is_zombie():
            # Zombies don't count as killed when skipped
            print(f"[ScoreKeeper] Zombie skipped - not counted as killed")
        elif humanoid.is_corpse():
            # Corpses don't count as killed when skipped, but count as encountered
            self.round_score["corpses_encountered"] += 1
            self.total_score["corpses_encountered"] += 1
            print(f"[ScoreKeeper] Corpse skipped - counted as encountered")
        else:
            # Human skipped - not counted as killed
            print(f"[ScoreKeeper] Human skipped - not counted as killed")

        print(f"[ScoreKeeper] After skip: military={self.military}, hra={self.hra}, scientist={self.scientist}, medic={self.medic}")

    def scram(self, humanoid=None):
        """
        scrams
        updates scorekeeper
        """
        print(f"[ScoreKeeper] scram called: state={getattr(humanoid, 'state', None)}, ht={getattr(humanoid, 'ht', None)}")
        self.remaining_time -= ActionCost.SCRAM.value
        
        # Just reset ambulance capacity - all counting was done during save/squish/skip
        print(f"[ScoreKeeper] SCRAM: Clearing ambulance capacity")
        self.ambulance["zombie"] = 0
        self.ambulance["injured"] = 0
        self.ambulance["healthy"] = 0
        self.ambulance["corpse"] = 0
        print(f"[ScoreKeeper] After scram: military={self.military}, hra={self.hra}, scientist={self.scientist}, medic={self.medic}")

    def available_action_space(self):
        """
        returns available action space as a list of bools
        """
        action_dict = {s.value:True for s in ActionState}
        if self.remaining_time <= 0:
            action_dict['save'] = False
            action_dict['squish'] = False
            action_dict['skip'] = False
        if self.at_capacity():
            action_dict['save'] = False
        return [action_dict[s.value] for s in ActionState]
        
    # do_action or return false if not possible
    def map_do_action(self, idx, humanoid):
        """
        does an action on a humanoid. Intended for RL use.
        
        idx : the action index 
        """
        if idx == 0:
            if self.remaining_time <= 0 or self.at_capacity():
                return False
            self.save(humanoid)
        elif idx == 1:
            if self.remaining_time <= 0:
                return False
            self.squish(humanoid)
        elif idx == 2:
            if self.remaining_time <= 0:
                return False
            self.skip(humanoid)
        elif idx == 3:
            self.scram(humanoid)
        else:
            raise ValueError("action index range exceeded")
        return True
        
    def get_cumulative_reward(self):
        """
        returns cumulative reward (current score)
        Note: the score can be denoted as anything, not set in stone
        """
        humans_saved = self.round_score["humans_saved"]
        humans_killed = self.round_score["humans_killed"]
        # Humans in ambulance will be saved (excluding corpses)
        humans_in_ambulance = self.ambulance["injured"] + self.ambulance["healthy"]
        humans_saved += humans_in_ambulance
        return humans_saved - humans_killed
    
    def get_military_meter(self):
        return self.military


    def get_medic_meter(self):
        return self.medic


    def get_hra_meter(self):
        return self.hra
   
    def get_scientist_meter(self):
        return self.scientist


    def get_current_capacity(self):
        return sum(self.ambulance.values())

    def at_capacity(self):
        return sum(self.ambulance.values()) >= self.capacity

    def get_score(self):
        self.scram()  # This updates round_score and total_score
        return self.total_score

    def get_round_score(self):
        """
        Returns the current round's scores for display purposes.
        """
        return dict(self.round_score)



    def reset_meters(self):
        """
        Resets all meters to their initial value (500).
        Call this when the game ends.
        """
        self.military = 500
        self.hra = 500
        self.scientist = 500
        self.medic = 500

    def next_round(self):
        if self.current_round < self.total_rounds:
            self.reset()
            self.current_round += 1
            return True
        else:
            # Game is over, but don't reset meters yet - they need to be displayed on game over screen
            # Meters will be reset when a new game starts (in play_again or end_game)
            return False  # Game is over
    
    @staticmethod
    def get_action_idx(class_string):
        return MAP_ACTION_STR_TO_INT[class_string]
    
    @staticmethod
    def get_action_string(class_idx):
        return MAP_ACTION_INT_TO_STR[class_idx]
    
    @staticmethod
    def get_all_actions():
        return MAP_ACTION_INT_TO_STR

    def terminate_game(self):
        """Mark this game as terminated. No further logs will be written."""
        self.terminated = True

    def end_game(self):
        """
        Resets all meters and round/game state for a new game.
        Call this when the user clicks END GAME.
        """
        # Save final scores before resetting
        final_score = dict(self.total_score)
        # Don't reset meters here - they need to be displayed on game over screen
        # Meters will be reset when a new game starts (in play_again)
        self.current_round = 1
        self.terminated = False
        self.reset()  # This resets round_score but not total_score
        self.all_logs = []
        # Don't reset total_score - it should persist across games
        return final_score  # Return final score before resetting
