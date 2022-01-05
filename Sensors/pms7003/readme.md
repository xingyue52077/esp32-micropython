# pms7003驱动，使用方法
```python
from pms7003 import Pms7003

pms = Pms7003(uart=2)
pms_data = pms.read()
```

# 也可以采用被动使用方式
```python
import micropython
from pms7003 import PassivePms7003

pms = PassivePms7003(uart=2)

def do_work(__):
    pms.wakeup()
    
    pms_data = pms.read()
    print(pms_data)
    
    pms.sleep()

# usually performing readings in interrupt handler (e.g. Timer's)
# so use schedule to avoid heap lock limitations:
# https://docs.micropython.org/en/latest/reference/isr_rules.html
callback = lambda __: micropython.schedule(do_work, 0)
```

* 代码来自：https://github.com/pkucmus/micropython-pms7003