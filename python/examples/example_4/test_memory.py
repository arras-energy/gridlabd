""" gldcore/link/python/test_memory.py

This module runs the 'test_memory.glm' module to verify that all the event handlers
work and that there are no memory leaks.
"""
import sys
assert(sys.version_info.major>2)
import gldcore

# construct the command line (gldcore hasn't started yet)
gldcore.command('test_memory.glm')

# start gldcore and wait for it to complete
gldcore.start('wait')

# send the final model state to a file
gldcore.save('done.json')


