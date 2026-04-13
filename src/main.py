from _typeshed import ExcInfo
from psychopy import visual, core
import psychtoolbox as ptb
from psychopy import sound
import sys
from condition import Condition
from experiment import Experiment

# add current directory to path
sys.path.append('./src')

test_trial = [Condition.SECTOR]

current_exp = Experiment()
current_exp.run_experiment(test_trial)
