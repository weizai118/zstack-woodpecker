'''
@author: FangSun
'''

import zstackwoodpecker.test_util as test_util
import zstackwoodpecker.test_lib as test_lib
import zstackwoodpecker.operations.resource_operations as res_ops
import apibinding.inventory as inventory
import zstackwoodpecker.test_state as test_state
import zstackwoodpecker.operations.primarystorage_operations as ps_ops

_config_ = {
        'timeout' : 3000,
        'noparallel' : True
        }

test_stub = test_lib.lib_get_test_stub()
test_obj_dict = test_state.TestStateDict()
VM_COUNT = 1
VOLUME_NUMBER = 10
disabled_ps_list = []

def test():
    local_ps = test_stub.find_ps_local()
    nfs_ps = test_stub.find_ps_nfs()

    test_util.test_dsc("Create {0} vm ".format(VM_COUNT))
    vm = test_stub.create_multi_vms(name_prefix='test-', count=VM_COUNT)[0]
    vm.check()
    test_obj_dict.add_vm(vm)

    test_util.test_dsc("Create {0} volumes in both primary storage ".format(VOLUME_NUMBER))
    volume_in_local = test_stub.create_multi_volume(count=VOLUME_NUMBER, ps=local_ps)
    volume_in_nfs  = test_stub.create_multi_volume(count=VOLUME_NUMBER, ps=nfs_ps)
    for volume in volume_in_local + volume_in_nfs:
        test_obj_dict.add_volume(volume)
        volume.check()

    test_util.test_dsc("Attach all volumes to VM")
    for volume in volume_in_local + volume_in_nfs:
        volume.attach(vm)
        volume.check()

    test_util.test_dsc("disable NFS PS")
    ps_ops.change_primary_storage_state(nfs_ps.uuid, state='disable')
    disabled_ps_list.append(nfs_ps)

    test_util.test_dsc("make sure all VM and Volumes still OK and running")
    vm.check()
    for volume in volume_in_local + volume_in_nfs:
        volume.check()

    test_util.test_dsc("Try to create vm with datavolume")
    new_vm = test_stub.create_multi_vms(name_prefix='test-vm', count=1, data_volume_number=10)[0]
    test_obj_dict.add_vm(new_vm)

    test_util.test_dsc("new Created VM and data volume should be in local ps")

    for volume in new_vm.get_vm().allVolumes:
        assert volume.primaryStorageUuid == local_ps.uuid

    test_util.test_pass('Multi PrimaryStorage Test Pass')


def env_recover():
    test_lib.lib_error_cleanup(test_obj_dict)
    for disabled_ps in disabled_ps_list:
        ps_ops.change_primary_storage_state(disabled_ps.uuid, state='enable')