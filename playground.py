from psychopy import sound, prefs, core

prefs.hardware['audioDevice'] = ["PTB"]
sound1 = sound.Sound(value = 440, stereo=True, secs = 1.0)
sound1.play()
core.wait(2.0)