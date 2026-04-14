from psychopy import prefs
import sys
from condition import Condition
from experiment import Experiment
prefs.hardware['audioDevice'] = ["PTB"]

# add current directory to path
sys.path.append('./src')

test_trial = [Condition.RING, Condition.SECTOR, Condition.SECTOR, Condition.RING]

current_exp = Experiment()
current_exp.run_experiment(test_trial)
