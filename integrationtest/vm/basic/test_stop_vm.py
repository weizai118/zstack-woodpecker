'''

New Integration Test for stopping VM operation

@author: Youyk
'''

import zstackwoodpecker.test_util as test_util
import test_stub

vm = None

def test():
    global vm
    vm = test_stub.create_vm()
    vm.check()
    vm.stop()
    vm.check()
    vm.destroy()
    vm.check()
    test_util.test_pass('Stop VM Test Success')

#Will be called only if exception happens in test().
def error_cleanup():
    global vm
    if vm:
        vm.destroy()
