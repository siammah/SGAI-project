import os
import math
import random
import tkinter as tk
from PIL import Image
import torch
import numpy as np
from torchvision import transforms

from gameplay.enums import ActionCost, State
from gameplay.humanoid import Humanoid
from models.DefaultCNN import DefaultCNN

import warnings


class Predictor(object):
    def __init__(self, classes=4, model_file=os.path.join('models', 'baseline.pth')):
        self.classes = classes
        self.net = None
        self.device = torch.device('cuda:0') if torch.cuda.is_available() else torch.device('cpu')
        self.transforms = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        self.is_model_loaded: bool = self._load_model(model_file)
        if not self.is_model_loaded:
            warnings.warn("Model not loaded, resorting to random prediction")

    def _load_model(self, weights_path, num_classes=4):
        try:
            self.net = DefaultCNN(num_classes)
            self.net.load_state_dict(torch.load(weights_path))
            return True
        except Exception as e: 
            print(e)
            return False

    def get_probs(self, img_):
        if self.is_model_loaded:
            img_ = self.transforms(img_).float().unsqueeze(0).to(self.device)
            with torch.no_grad():
                outputs = self.net(img_)
                probs = torch.nn.functional.softmax(outputs, 1)[0].cpu().numpy()
        else:
            probs = np.ones(self.classes) / self.classes
        return probs


class HeuristicInterface(object):
    def __init__(self, root, w, h, display=False, model_file=os.path.join('models', 'baseline.pth'),
                 img_data_root='data'):
        self.text = ""
        self.display = display
        self.img_data_root = img_data_root

        # load 
        self.predictor = Predictor(model_file=model_file)

        if self.display:
            self.canvas = tk.Canvas(root, width=math.floor(0.2 * w), height=math.floor(0.1 * h))
            self.canvas.place(x=math.floor(0.75 * w), y=math.floor(0.75 * h))
            self.label = tk.Label(self.canvas, text="Simon says...", font=("Courier New", 20))
            self.label.pack(side=tk.TOP)

            self.suggestion = tk.Label(self.canvas, text=self.text, font=("Courier New", 20))
            self.suggestion.pack(side=tk.TOP)

    def _load_model(self, weights_path, num_classes=4):
        try:
            self.net = DefaultCNN(num_classes)
            self.net.load_state_dict(torch.load(weights_path))
            return True
        except:  # file not found, maybe others?
            return False

    def suggest(self, humanoid, capacity_full=False):
        if self.predictor.is_model_loaded:
            action = self.get_model_suggestion(humanoid, capacity_full)
        else:
            action = self.get_random_suggestion()
        self.text = action.name
        if self.display:
            self.suggestion.config(text=self.text)

    def act(self, scorekeeper, humanoid):
        self.suggest(humanoid, scorekeeper.at_capacity())
        action = self.text
        if action == ActionCost.SKIP.name:
            scorekeeper.skip(humanoid)
        elif action == ActionCost.SQUISH.name:
            scorekeeper.squish(humanoid)
        elif action == ActionCost.SAVE.name:
            scorekeeper.save(humanoid)
        elif action == ActionCost.SCRAM.name:
            scorekeeper.scram(humanoid)
        else:
            raise ValueError("Invalid action suggested")

    @staticmethod
    def get_random_suggestion():
        return random.choice(list(ActionCost))

    def get_model_suggestion(self, humanoid, is_capacity_full) -> ActionCost:
        img_ = Image.open(os.path.join(self.img_data_root, humanoid.fp))
        probs: np.ndarray = self.predictor.get_probs(img_)

        predicted_ind: int = np.argmax(probs, 0)
        class_string = Humanoid.get_all_states()[predicted_ind]
        predicted_state = State(class_string)

        # given the model's class prediction, recommend an action
        recommended_action = self._map_class_to_action_default(predicted_state, is_capacity_full)
        return recommended_action

    @staticmethod
    def _map_class_to_action_default(predicted_state: State, is_capacity_full: bool = False) -> ActionCost:
        # map prediction to ActionCost to return the right thing; now aligned with Rob's pseudocode
        if is_capacity_full:
            return ActionCost.SCRAM
        if predicted_state is State.ZOMBIE:
            return ActionCost.SQUISH
        if predicted_state is State.INJURED:
            return ActionCost.SAVE
        if predicted_state is State.HEALTHY:
            return ActionCost.SAVE
        if predicted_state is State.CORPSE:
            return ActionCost.SQUISH
