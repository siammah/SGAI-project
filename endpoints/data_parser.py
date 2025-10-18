import random
import os
import string
from gameplay.humanoid import Humanoid
from gameplay.enums import State, HumanType

STATE_FOLDERS = ['zombie', 'injured', 'healthy', 'corpse']

class DataParser(object):
    """
    Parses the input data photos by folder and filename, not metadata.
    """
    def __init__(self, data_fp, test_images_folder="data/test_images"):
        # Store the full test_images path (e.g., 'data/data/test_images')
        self.fp = os.path.join(data_fp, test_images_folder)
        # Build a dict: state_name -> list of image filenames
        self.state_to_files = {}
        for state in STATE_FOLDERS:
            folder = os.path.join(self.fp, state)
            if os.path.isdir(folder):
                self.state_to_files[state] = sorted([f for f in os.listdir(folder) if f.endswith('.png')])
            else:
                self.state_to_files[state] = []
        # Build all possible (state, idx) pairs
        self.all_pairs = []
        for state, files in self.state_to_files.items():
            for idx in range(len(files)):
                self.all_pairs.append((state, idx))
        self.unvisited = self.all_pairs.copy()
        self.visited = []

    def reset(self):
        self.unvisited = self.all_pairs.copy()
        self.visited = []

    def get_random(self):
        if not self.unvisited:
            raise ValueError("No humanoids remain")
        pair = random.choice(self.unvisited)
        self.unvisited.remove(pair)
        self.visited.append(pair)
        state, idx = pair
        filename = self.state_to_files[state][idx]
        # Store the full path to the image
        fp = os.path.join(self.fp, state, filename)
        # Use filename for state info
        state_info = datarow_to_state(filename, parent=state)

        humanoid = Humanoid(fp=fp, state=state_info, ht=state_info['role'])
        return humanoid

# Instead of datarow, just use filename
# Example: z_do_0199_n_r_s_cropped.png
# Example: p_0199_n_r_i_cropped.png
# Example: p_c_0199_n_r_cropped.png

def datarow_to_state(filename, parent=None):
    # Remove extension
    name = filename.replace('.png', '')
    parts = name.split('_')
    # Split by underscores
    roles = parts[0]
    role = ""
    posture = ""
    weather = ""
    time = ""


    #remove the last part of parts (it is always the word cropped)
    parts.pop()

    #iterate through the list and remove the part if it has a number in it ( we lowk don't need the number)
    for part in parts:
        if any(char.isdigit() for char in part):
            parts.remove(part)
        #check for weather
        if any(char=='r' for char in part):
            weather="rain"


        #check for posture
    if parent == 'corpse' or parent == 'injured':
        posture="injured"
    else:
        posture="standing"


    #if weather is not set, set it to sunny
    if weather == "":
        weather="sunny"

    #if time is not set, set it to day
    if weather=="rain":
        time="night"
    else:
        time="day"

    print(name)
    #this is the variable that contains the role of the humanoid
    
    #seejal 
    if roles == 'h' or roles == 'z' or roles == 'c':
        role = HumanType.DEFAULT.value
    elif roles == 'g':
        role = HumanType.ELDERLY.value
    elif roles == 'do':
        role = HumanType.DOCTOR.value
    elif roles == 'm':
        role = HumanType.BUSINESS.value
    elif roles == 'p':
        role = HumanType.POLICE.value
    # Return as dict for now
    return {
        'raw': filename,
        'role': role,
        'parent': parent,
        'posture': posture,
        'weather': weather,
        'time': time,
    }
