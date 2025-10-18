from gameplay.enums import State
from gameplay.enums import HumanType


MAP_CLASS_STR_TO_INT = {s.value:i for i,s in enumerate(State)}
MAP_CLASS_INT_TO_STR = [s.value for s in State]


MAP_CLASS_STR_TO_INT_HT = {s.value:i for i,s in enumerate(HumanType)}
MAP_CLASS_INT_TO_STR_HT = [s.value for s in HumanType]


class Humanoid(object):
    """
    Are they a human or a zombie???
    """
   
    def __init__(self, fp, state, ht, value = 0):
        self.fp = fp
        self.state = state
        self.ht = ht
        # self.value = value


    def is_zombie(self):
        ht_val = self.ht.value if hasattr(self.ht, 'value') else self.ht

        if self.is_corpse():
            return False
        return (
            self.state.get('state') == State.ZOMBIE.value or
            self.state.get('parent') == State.ZOMBIE.value or
            self.state.get('posture') == State.ZOMBIE.value or 
            ht_val == HumanType.DEFAULT.value
        )


    def is_injured_business(self):
        ht_val = self.ht.value if hasattr(self.ht, 'value') else self.ht
        return (
            (self.state.get('posture') == State.INJURED.value or self.state.get('state') == State.INJURED.value or self.state.get('parent') == State.INJURED.value)
            and ht_val == HumanType.BUSINESS.value
        )


    def is_injured_doctor(self):
        ht_val = self.ht.value if hasattr(self.ht, 'value') else self.ht
        return (
            (self.state.get('posture') == State.INJURED.value or self.state.get('state') == State.INJURED.value or self.state.get('parent') == State.INJURED.value)
            and ht_val == HumanType.DOCTOR.value
        )
   
    def is_injured_elderly(self):
        ht_val = self.ht.value if hasattr(self.ht, 'value') else self.ht
        return (
            (self.state.get('posture') == State.INJURED.value or self.state.get('state') == State.INJURED.value or self.state.get('parent') == State.INJURED.value)
            and ht_val == HumanType.ELDERLY.value
        )


    def is_injured_police(self):
        ht_val = self.ht.value if hasattr(self.ht, 'value') else self.ht
        return (
            (self.state.get('posture') == State.INJURED.value or self.state.get('state') == State.INJURED.value or self.state.get('parent') == State.INJURED.value)
            and ht_val == HumanType.POLICE.value
        )


    def is_healthy_business(self):
        ht_val = self.ht.value if hasattr(self.ht, 'value') else self.ht
        return (
            (self.state.get('posture') == State.HEALTHY.value or self.state.get('state') == State.HEALTHY.value or self.state.get('parent') == State.HEALTHY.value)
            and ht_val == HumanType.BUSINESS.value
        )


    def is_healthy_doctor(self):
        ht_val = self.ht.value if hasattr(self.ht, 'value') else self.ht
        return (
            (self.state.get('posture') == State.HEALTHY.value or self.state.get('state') == State.HEALTHY.value or self.state.get('parent') == State.HEALTHY.value)
            and ht_val == HumanType.DOCTOR.value
        )


    def is_healthy_elderly(self):
        ht_val = self.ht.value if hasattr(self.ht, 'value') else self.ht
        return (
            (self.state.get('posture') == State.HEALTHY.value or self.state.get('state') == State.HEALTHY.value or self.state.get('parent') == State.HEALTHY.value)
            and ht_val == HumanType.ELDERLY.value
        )


    def is_healthy_police(self):
        ht_val = self.ht.value if hasattr(self.ht, 'value') else self.ht
        return (
            (self.state.get('posture') == State.HEALTHY.value or self.state.get('state') == State.HEALTHY.value or self.state.get('parent') == State.HEALTHY.value)
            and ht_val == HumanType.POLICE.value
        )


    def is_corpse(self):
        return (
            self.state.get('state') == State.CORPSE.value or
            self.state.get('parent') == State.CORPSE.value or
            self.state.get('posture') == State.CORPSE.value
        )
   
    @staticmethod
    def get_state_idx(class_string):
        return MAP_CLASS_STR_TO_INT[class_string]
   
    @staticmethod
    def get_state_string(class_idx):
        return MAP_CLASS_INT_TO_STR[class_idx]
   
    @staticmethod
    def get_all_states():
        return MAP_CLASS_INT_TO_STR


    @staticmethod
    def get_humantype_idx(class_string):
        return MAP_CLASS_STR_TO_INT_HT[class_string]
   
    @staticmethod
    def get_humantype_string(class_idx):
        return MAP_CLASS_INT_TO_STR_HT[class_idx]
   
    @staticmethod
    def get_all_humantypes():
        return MAP_CLASS_INT_TO_STR_HT
