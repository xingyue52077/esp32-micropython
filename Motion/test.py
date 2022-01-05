#   Author: Olivier Lenoir - <olivier.len02@gmail.com>
#   Created: 2019-12-08 14:26:49
#   Project: Testing 'multiaxis.py'

from utime import ticks_ms, ticks_diff
from multiaxis_RTM import Axis, MultiAxis


x = Axis(dir_pin=5, step_pin=18)

cnc = MultiAxis(x)

t_ms = ticks_ms

print('period:', cnc.period, 'µs')

print(tuple(cnc.cur_pos()))

start = t_ms()
cnc.g01(360)
print(tuple(cnc.cur_pos()))
print(ticks_diff(t_ms(), start), 'ms')


start = t_ms()
cnc.g01(0)
print(tuple(cnc.cur_pos()))
print(ticks_diff(t_ms(), start), 'ms')



