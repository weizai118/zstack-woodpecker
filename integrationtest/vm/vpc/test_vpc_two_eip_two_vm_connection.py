'''
@author: FangSun
'''

import zstackwoodpecker.test_util as test_util
import zstackwoodpecker.test_lib as test_lib
import zstackwoodpecker.test_state as test_state
import os
from itertools import izip

VLAN1_NAME, VLAN2_NAME = ['l3VlanNetworkName1', "l3VlanNetwork3"]
VXLAN1_NAME, VXLAN2_NAME = ["l3VxlanNetwork11", "l3VxlanNetwork12"]

CLASSIC_L3 = 'l3NoVlanNetworkName1'

vpc1_l3_list = [VLAN1_NAME, VLAN2_NAME]
vpc2_l3_list = [VXLAN1_NAME, VXLAN2_NAME]

vpc_l3_list = [vpc1_l3_list, vpc2_l3_list]
vpc_name_list = ['vpc1','vpc2']


case_flavor = dict(vm1_vm2_one_vpc_1vlan=   dict(vm1l3=VLAN1_NAME, vm2l3=VLAN1_NAME),
                   vm1_vm2_one_vpc_2vlan=   dict(vm1l3=VLAN1_NAME, vm2l3=VLAN2_NAME),
                   vm1_vm2_two_vpc=         dict(vm1l3=VLAN1_NAME, vm2l3=VXLAN2_NAME),
                   vm1_classic_vm2_vpc  =   dict(vm1l3=CLASSIC_L3, vm2l3=VXLAN2_NAME)
                   )


test_stub = test_lib.lib_get_test_stub()
test_obj_dict = test_state.TestStateDict()
vr_inv_list = []


def test():
    flavor = case_flavor[os.environ.get('CASE_FLAVOR')]
    test_util.test_dsc("create vpc vrouter and attach vpc l3 to vpc")
    for vpc_name in vpc_name_list:
        vr_inv_list.append(test_stub.create_vpc_vrouter(vpc_name))
    for vr_inv, l3_list in izip(vr_inv_list, vpc_l3_list):
        test_stub.attach_all_l3_to_vpc_vr(vr_inv, l3_list)

    test_util.test_dsc("create two vm, vm1 in l3 {}, vm2 in l3 {}".format(flavor['vm1l3'], flavor['vm2l3']))
    vm1 = test_stub.create_vm_with_random_offering(vm_name='vpc_vm_{}'.format(flavor['vm1l3']), l3_name=flavor['vm1l3'])
    test_obj_dict.add_vm(vm1)

    vm2 = test_stub.create_vm_with_random_offering(vm_name='vpc_vm_{}'.format(flavor['vm2l3']), l3_name=flavor['vm2l3'])
    test_obj_dict.add_vm(vm2)

    for vm in (vm1,vm2):
        vm.check()

    vr_pub_nic = test_lib.lib_find_vr_pub_nic(vr_inv_list[0])

    vip_list = []
    for vm in (vm1, vm2):
        test_util.test_dsc("Create vip for vm {}".format(vm.get_vm().name))
        vip = test_stub.create_vip('vip_{}'.format(vm.get_vm().name), vr_pub_nic.l3NetworkUuid)
        test_obj_dict.add_vip(vip)
        vip_list.append(vip)

        test_util.test_dsc("Create eip for vm {}".format(vm.get_vm().name))
        eip = test_stub.create_eip('eip_{}'.format(vm.get_vm().name), vip_uuid=vip.get_vip().uuid)
        vip.attach_eip(eip)
        vip.check()
        eip.attach(vm.get_vm().vmNics[0].uuid, vm)
        vip.check()

    for vm in (vm1, vm2):
        vm.check()

    vm1_inv = vm1.get_vm()
    vm2_inv = vm2.get_vm()
    vip1, vip2 = vip_list

    test_util.test_dsc("test two vm EIP connectivity")
    test_stub.run_command_in_vm(vm1_inv, 'iptables -F')
    test_stub.run_command_in_vm(vm2_inv, 'iptables -F')

    test_lib.lib_check_ping(vm1_inv, vip2.get_vip().ip)
    test_lib.lib_check_ping(vm2_inv, vip1.get_vip().ip)

    test_lib.lib_check_ports_in_a_command(vm1_inv, vip1.get_vip().ip,
                                          vip2.get_vip().ip, ["22"], [], vm2_inv)

    test_lib.lib_check_ports_in_a_command(vm2_inv, vip2.get_vip().ip,
                                          vip1.get_vip().ip, ["22"], [], vm1_inv)

    test_stub.remove_all_vpc_vrouter()


def env_recover():
    test_stub.remove_all_vpc_vrouter()
    test_lib.lib_error_cleanup(test_obj_dict)

