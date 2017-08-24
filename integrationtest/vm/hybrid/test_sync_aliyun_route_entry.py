'''

New Integration Test for hybrid.

@author: Legion
'''

import zstackwoodpecker.test_util as test_util
import zstackwoodpecker.test_lib as test_lib
import zstackwoodpecker.test_state as test_state
import zstackwoodpecker.operations.hybrid_operations as hyb_ops
import zstackwoodpecker.operations.resource_operations as res_ops
import time
import os

test_obj_dict = test_state.TestStateDict()
ks_inv = None
datacenter_inv = None
route_entry_inv = None

def test():
    global ks_inv
    global datacenter_inv
    global route_entry_inv
    datacenter_type = os.getenv('datacenterType')
    vpc_id = os.getenv('ecs_vpcId')
    vpc_vr_id = os.getenv('vpc_vrId')
    vpn_gateway_id = os.getenv('vpn_gatewayId')
    ks_existed = hyb_ops.query_aliyun_key_secret()
    if not ks_existed:
        ks_inv = hyb_ops.add_aliyun_key_secret('test_hybrid', 'test for hybrid', os.getenv('aliyunKey'), os.getenv('aliyunSecret'))
    # Clear datacenter remained in local
    datacenter_local = hyb_ops.query_datacenter_local()
    if datacenter_local:
        for d in datacenter_local:
            hyb_ops.del_datacenter_in_local(d.uuid)
    datacenter_list = hyb_ops.get_datacenter_from_remote(datacenter_type)
    regions = [ i.regionId for i in datacenter_list]
    for r in regions:
        datacenter_inv = hyb_ops.add_datacenter_from_remote(datacenter_type, r, 'datacenter for test')
        # Add Identity Zone
        iz_list = hyb_ops.get_identity_zone_from_remote(datacenter_type, r)
        vpn_gateway_list = []
        for iz in iz_list:
            if not iz.availableInstanceTypes:
                continue
            iz_inv = hyb_ops.add_identity_zone_from_remote(datacenter_type, datacenter_inv.uuid, iz.zoneId)
            vpn_gateway_list = hyb_ops.sync_vpc_vpn_gateway_from_remote(datacenter_inv.uuid)
            if vpn_gateway_list:
                break
            else:
                hyb_ops.del_identity_zone_in_local(iz_inv.uuid)
        if vpn_gateway_list:
            break
        else:
            hyb_ops.del_datacenter_in_local(datacenter_inv.uuid)
    if not vpn_gateway_list:
        test_util.test_fail("VpnGate for route entry creating was not found in all available dataCenter")
    hyb_ops.sync_ecs_vpc_from_remote(datacenter_inv.uuid)
    vpc_local = hyb_ops.query_ecs_vpc_local()
    # Get Vpc which has available gateway
    for vl in vpc_local:
        if vl.ecsVpcId == vpc_id:
            vpc_inv = vl
    # Get Vpn gateway
    vpc_vpn_gw_local = hyb_ops.query_vpc_vpn_gateway_local()
    for gw in vpc_vpn_gw_local:
        if gw.vpnGatewayId == vpn_gateway_id:
            vpn_gateway = gw
    # Get Aliyun virtual router
    hyb_ops.sync_aliyun_virtual_router_from_remote(vpc_inv.uuid)
    vr_local = hyb_ops.query_aliyun_virtual_router_local()
    for v in vr_local:
        if v.vrId == vpc_vr_id:
            vr = v
    route_entry_inv = hyb_ops.create_aliyun_vpc_virtualrouter_entry_remote('172.18.201.0/24', vr.uuid, vrouter_type='vrouter', next_hop_type='VpnGateway', next_hop_uuid=vpn_gateway.uuid)
    time.sleep(10)
    hyb_ops.sync_router_entry_from_remote(vr.uuid, vrouter_type='vrouter')
    route_entry_local = hyb_ops.query_aliyun_route_entry_local()
    for r in route_entry_local:
        if r.destinationCidrBlock == '172.18.201.0/24':
            route_entry = r
    assert route_entry.status.lower() == 'available'
    test_util.test_pass('Sync Aliyun Route Entry Test Success')

def env_recover():
    global route_entry_inv
    if route_entry_inv:
        time.sleep(20)
        hyb_ops.del_aliyun_route_entry_remote(route_entry_inv.uuid)

    global datacenter_inv
    if datacenter_inv:
        hyb_ops.del_datacenter_in_local(datacenter_inv.uuid)
    global ks_inv
    if ks_inv:
        hyb_ops.del_aliyun_key_secret(ks_inv.uuid)

#Will be called only if exception happens in test().
def error_cleanup():
    global test_obj_dict
    test_lib.lib_error_cleanup(test_obj_dict)
