#   Author: Olivier Lenoir - <olivier.len02@gmail.com>
#   Created: 2019-10-29 09:12:13
#   Project: Multi Axis, MicroPython stepper motor
#   Description: This version of MultiAxis use RMT

from machine import Pin
from esp32 import RMT

DRV8825_mp = const(2)


@micropython.viper
def sub(a: int, b: int) -> int:
    return a - b


@micropython.viper
def do_step(s: int, d: int, m: int) -> int:
    sdm = s * d + m // 2
    return sdm // m - (sdm - d) // m


# @micropython.native
class Axis(object):

    id_axis = 0

    def __init__(self, dir_pin, step_pin):
        self.d_pin = Pin(dir_pin, Pin.OUT)
        self.s_pin = RMT(Axis.id_axis, pin=Pin(step_pin), clock_div=80)
        self.wp = self.s_pin.write_pulses
        Axis.id_axis += 1
        self.pos = 0
        # Start period (µs)
        self.start_period = 30000
        # Target period (µs)
        self.period = 10000
        # Acceleration / Deceleration Rate (µs per step)
        self.acceleration_rate = 5000

    def set_dir(self, steps):
        d = self.d_pin()
        if steps < 0 and d:
            self.d_pin(0)
        elif steps > 0 and not d:
            self.d_pin(1)

    def step(self, period=4):
        self.wp((DRV8825_mp, max(DRV8825_mp, min(32767, period - DRV8825_mp))))
        if self.d_pin():
            self.pos += 1
        else:
            self.pos -= 1

    def _step(self, period=4):
        self.wp((DRV8825_mp, max(DRV8825_mp, min(32767, period - DRV8825_mp))))

    def steps(self, steps, period=4, p_size=100):
        self.set_dir(steps)
        d, m = divmod(abs(steps), p_size)
        pulse = (DRV8825_mp, max(DRV8825_mp, min(32767, period - DRV8825_mp)))
        wp = self.wp
        loops = range(d)
        for _ in loops:
            wp(pulse * p_size)
        if m:
            wp(pulse * m)
        self.pos += steps

    def origin(self, period=0):
        self.steps(-self.pos, period)


# @micropython.native
class MultiAxis(object):

    def __init__(self, *axis):
        self.axes = axis
        # Start period (µs)
        self.start_period = 30000
        # Target period (µs)
        self.period = 10000
        # Acceleration / Deceleration Rate (µs per step)
        self.acceleration_rate = 5000

    def cur_pos(self):
        return (a.pos for a in self.axes)

    def dists(self, coords):
        return map(sub, coords, self.cur_pos())

    def set_dirs(self, dists):
        for a, d in zip(self.axes, dists):
            a.set_dir(d)

    def g01(self, *coord):
        # caching
        mx = max
        # calc dist per axis
        dists = list(self.dists(coord))
        # max abs of dists
        m_dist = max(map(abs, dists))
        # set direction
        self.set_dirs(dists)
        # caching Acceleration / Deceleration
        str_p = self.start_period
        trg_p = self.period
        acc_r = self.acceleration_rate
        _acc = 0
        _dec = abs(m_dist) * acc_r - str_p
        # keep axes moving
        main_axes, other_axes, other_dists = [], [], []
        for a, d in zip(self.axes, dists):
            if abs(d) == m_dist:
                main_axes.append(a)
            elif d:
                other_axes.append(a)
                other_dists.append(d)
        # Loop steps
        steps = range(1, m_dist + 1)
        for s in steps:
            _acc += acc_r
            prd = mx(trg_p, str_p - _acc, _acc - _dec)
            for a in main_axes:
                a._step(prd)
            for a, do_s in zip(other_axes, [do_step(s, d, m_dist) for d in other_dists]):
                if do_s:
                    a._step()
        # update position
        for a, d in zip(self.axes, dists):
            a.pos += d
