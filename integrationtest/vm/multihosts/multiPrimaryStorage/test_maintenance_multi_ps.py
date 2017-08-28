'''
@author: FangSun
'''

import zstackwoodpecker.test_util as test_util
import zstackwoodpecker.test_lib as test_lib
import zstackwoodpecker.operations.resource_operations as res_ops
import zstackwoodpecker.test_state as test_state
import zstackwoodpecker.operations.primarystorage_operations as ps_ops
import zstackwoodpecker.operations.vm_operations as vm_ops
import time
import apibinding.inventory as inventory

_config_ = {
        'timeout' : 3000,
        'noparallel' : True
        }

test_stub = test_lib.lib_get_test_stub()
test_obj_dict = test_state.TestStateDict()
VOLUME_NUMBER = 10
maintenance_ps_list = []


@test_stub.skip_if_only_one_ps
def test():
    ps_env = test_stub.PSEnvChecker()

    ps, another_ps = ps_env.get_two_ps()

    vm1, vm2 = test_stub.create_multi_vms(name_prefix='test-', count=2, ps_uuid=ps.uuid)

    for vm in (vm1, vm2):
        test_obj_dict.add_vm(vm)

    if another_ps.type == inventory.LOCAL_STORAGE_TYPE:
        volume_in_another = test_stub.create_multi_volumes(count=VOLUME_NUMBER, ps=another_ps,
                                                          host_uuid=test_lib.lib_get_vm_host(vm2.get_vm()).uuid)
    else:
        volume_in_another = test_stub.create_multi_volumes(count=VOLUME_NUMBER, ps=another_ps)

    for volume in volume_in_another:
        test_obj_dict.add_volume(volume)

    for volume in volume_in_another:
        volume.attach(vm2)

    test_util.test_dsc('set another ps in maintenance mode')
    ps_ops.change_primary_storage_state(state='maintain', primary_storage_uuid=another_ps.uuid)
    maintenance_ps_list.append(another_ps)
    time.sleep(10)
    count = 10
    vm1.update()
    assert vm1.get_vm().state == inventory.RUNNING
    while count:
        vm2.update()
        if vm2.get_vm().state == inventory.STOPPED:
            break
        elif vm2.get_vm().state == inventory.STOPPING:
            time.sleep(10)
            count -= 1
        else:
            test_util.test_fail("VM2 is not in Stopped status!!!")

    vr_vm_list = test_lib.lib_find_vr_by_vm(vm1.get_vm())
    vr_vm = None
    if vr_vm_list:
        vr_vm = vr_vm_list[0]
        if vr_vm.allVolumes[0].primaryStorageUuid == another_ps.uuid:
            assert vr_vm.state == inventory.STOPPED
        else:
            assert vr_vm.state == inventory.RUNNING
            vm1.check()
    else:
        vm1.check()

    with test_stub.expected_failure("Start vm in maintenance ps", Exception):
        vm2.start()

    test_util.test_dsc('enable another ps')
    ps_ops.change_primary_storage_state(state='enable', primary_storage_uuid=another_ps.uuid)
    maintenance_ps_list.remove(another_ps)

    if vr_vm and vr_vm.state == inventory.STOPPED:
        vm_ops.start_vm(vr_vm.uuid)

    time.sleep(10)
    vm2.start()
    vm2.check()

    for volume in volume_in_another:
        volume.detach()
        volume.attach(vm2)

    test_util.test_pass('Multi PrimaryStorage Test Pass')


def env_recover():
    for maintenance_ps in maintenance_ps_list:
        ps_ops.change_primary_storage_state(maintenance_ps.uuid, state='enable')
    test_lib.lib_error_cleanup(test_obj_dict)