from ctypes.util import test
from psychopy import prefs, core, event
import sys
from condition import Condition
from experiment import Experiment
prefs.hardware['audioDevice'] = ["PTB"]
event.globalKeys.add(key='escape', func=core.quit, name='shutdown')

# add current directory to path
sys.path.append('./src')

test_trial = []
test_trial += [Condition.BAR_HORIZONTAL] * 5
#test_trial += [Condition.BAR_VERTICAL] * 5
#test_trial += [Condition.RING] * 5
#test_trial += [Condition.SECTOR] * 5

current_exp = Experiment()
if current_exp.show_dlg():
    print("Dialog OK")
    print(current_exp.data)

current_exp.get_objects()
current_exp.run_experiment(test_trial)
