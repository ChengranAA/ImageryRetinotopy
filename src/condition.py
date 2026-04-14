from enum import Enum
import random

class Condition(Enum):

    SECTOR = 1
    BAR_HORIZONTAL = 2
    BAR_VERTICAL = 3
    RING = 4

    @staticmethod
    def generate_condition_list():
        conditions = [
            Condition.SECTOR,
            #Condition.BAR_HORIZONTAL,
            #Condition.BAR_VERTICAL,
            Condition.RING
        ]
        list_conditions = conditions * 5
        random.shuffle(list_conditions)
        return list_conditions

if __name__ == "__main__":
    list_conditions = Condition.generate_condition_list()
    for condition in list_conditions:
        print(condition.name)