#coding:utf-8
'''

New Integration Test for zstack cloudformation.
Cover two scenes : 1.Timeout to create resource stack and rollback.
                   2.Timeout to create resource stack and don't rollback.

@author: chenyuan.xu
'''

import zstackwoodpecker.test_util as test_util
import zstackwoodpecker.operations.resource_stack as resource_stack_ops
import zstackwoodpecker.operations.resource_operations as res_ops

def test():
    test_util.test_dsc("Test Resource template Apis")
    
    cond = res_ops.gen_query_conditions('status', '=', 'Ready')
    cond = res_ops.gen_query_conditions('state', '=', 'Enabled', cond)
    cond = res_ops.gen_query_conditions('system', '=', 'false', cond)
    image_queried = res_ops.query_resource(res_ops.IMAGE, cond)

    cond = res_ops.gen_query_conditions("category", '=', "Public")
    l3_pub_queried = res_ops.query_resource(res_ops.L3_NETWORK, cond)
    
    cond = res_ops.gen_query_conditions("category", '=', "Private")
    cond = res_ops.gen_query_conditions('networkServices.networkServiceType', '=', 'EIP')
    l3_pri_queried = res_ops.query_resource(res_ops.L3_NETWORK, cond)

    cond = res_ops.gen_query_conditions('state', '=', 'Enabled')
    cond = res_ops.gen_query_conditions('type', '=', 'UserVm', cond)
    instance_offering_queried = res_ops.query_resource(res_ops.INSTANCE_OFFERING, cond)  

    templateContent = '''
{
    "ZStackTemplateFormatVersion": "2018-06-18",
    "Description": "Just create a flat network & VM",
    "Parameters": {
        "L3NetworkUuid":{
            "Type": "String",
            "Label": "三层网络"
        },
        "BackupStorageUuid":{
            "Type": "CommaDelimitedList",
            "Label": "镜像服务器"
        }
    },
    "Resources": {
        "VmInstance": {
            "Type": "ZStack::Resource::VmInstance",
            "Properties": {
                "name": "VM-STACK",
                "instanceOfferingUuid": {"Fn::GetAtt":["InstanceOffering","uuid"]},
                "imageUuid":{"Fn::GetAtt":["Image","uuid"]},
                "l3NetworkUuids":[{"Ref":"L3NetworkUuid"}]
            }
        },
        "InstanceOffering": {
            "Type": "ZStack::Resource::InstanceOffering",
            "Properties": {
                "name":"1G-1CPU-STACK",
                "description":"测试创建计算规格",
                "cpuNum": 1,
                "memorySize": 1073741824
            }
        },
        "Image": {
            "Type": "ZStack::Resource::Image",
            "Properties": {
                "name": "IMAGE-STACK",
                "backupStorageUuids": {"Ref":"BackupStorageUuid"},
                "url":"http://172.20.1.22/mirror/diskimages/centos7-test.qcow2",
                "format": "qcow2"
            }
        }
    },
    "Outputs": {
        "VmInstance": {
            "Value": {
                "Ref": "VmInstance"
            }
        }
    }
}
'''
    parameter = '{"PrivateNetworkUuid":"%s","PublicNetworkUuid":"%s","ImageUuid":"%s","InstanceOfferingUuid":"%s"}' % (l3_pri_queried[0].uuid, l3_pub_queried[0].uuid, image_queried[0].uuid, instance_offering_queried[0].uuid)
 
    #1.create resource stack when rollback
    resource_stack_option_rollback = test_util.ResourceStackOption()
    resource_stack_option_rollback.set_name("Create_STACK-Rollback")
    resource_stack_option_rollback.set_rollback("true")
    resource_stack_option_rollback.set_timeout("1")

    resource_stack_option_rollback.set_templateContent(templateContent)
    resource_stack_option_rollback.set_parameters(parameter)
    preview_resource_stack = resource_stack_ops.preview_resource_stack(resource_stack_option_rollback)
    resource_stack_rollback = resource_stack_ops.create_resource_stack(resource_stack_option_rollback)

    #2.get resource from resource stack when rollback
    resource_rollback = resource_stack_ops.get_resource_from_resource_stack(resource_stack_rollback.uuid)
    if len(resource_rollback) != 0:
        test_util.test_fail("There still has resources when rollback")

    cond = res_ops.gen_query_conditions('uuid', '=', resource_stack_rollback.uuid)
    resource_stack_rollback_queried = res_ops.query_resource(res_ops.RESOURCE_STACK, condss
    cond = res_ops.gen_query_conditions('name', '=', 'Create_STACK-Rollback-VM')
    vm_rollback_queried = res_ops.query_resource(res_ops.VM_INSTANCE, cond)

    cond = res_ops.gen_query_conditions('name', '=', 'Create_STACK-Rollback-VIP')
    vip_rollback_queried = res_ops.query_resource(res_ops.VIP, cond)

    cond = res_ops.gen_query_conditions('name', '=', 'Create_STACK-Rollback-EIP')
    eip_rollback_queried = res_ops.query_resource(res_ops.EIP, cond)

    if len(vm_rollback_queried) != 0 or len(vip_rollback_queried) != 0 or len(eip_rollback_queried) != 0:
        test_util.test_fail("Fail to delete resources when rollback")

    #3.create resource stack when not rollback
    resource_stack_option_norollback = test_util.ResourceStackOption()
    resource_stack_option_norollback.set_name("Create_STACK")
    resource_stack_option_norollback.set_rollback("false")
    resource_stack_option_norollback.set_timeout("1")

    resource_stack_option_norollback.set_templateContent(templateContent)
    resource_stack_option_norollback.set_parameters(parameter)
    preview_resource_stack = resource_stack_ops.preview_resource_stack(resource_stack_option_norollback)
    try:
       resource_stack_norollback = resource_stack_ops.create_resource_stack(resource_stack_option_norollback)
    except: 
       pass
    else:
       test_util.test_fail('Resource Stack Rollback Test Success')

    #4.get resource from resource stack when not rollback
    resource_stack_ops.delete_resource_stack(resource_stack_rollback.uuid)

    cond = res_ops.gen_query_conditions('name', '=', 'Create_STACK')
    resource_stack_norollback = res_ops.query_resource(res_ops.RESOURCE_STACK, cond)

    cond = res_ops.gen_query_conditions('uuid', '=', resource_stack_norollback[0].uuid)
    resource_stack_norollback_queried = res_ops.query_resource(res_ops.RESOURCE_STACK, cond)

    cond = res_ops.gen_query_conditions('name', '=', 'Create_STACK-VM')
    vm_norollback_queried = res_ops.query_resource(res_ops.VM_INSTANCE, cond)

    cond = res_ops.gen_query_conditions('name', '=', 'Create_STACK-VIP')
    vip_norollback_queried = res_ops.query_resource(res_ops.VIP, cond)

    cond = res_ops.gen_query_conditions('name', '=', 'Create_STACK-EIP')
    eip_norollback_queried = res_ops.query_resource(res_ops.EIP, cond)

    if len(resource_stack_norollback_queried) == 0 :
        test_util.test_fail("Fail to delete resource stack")

    if resource_stack_norollback_queried[0].status == 'Failed':
        if len(vm_norollback_queried) == 0 or len(vip_norollback_queried) == 0:
            test_util.test_fail("Resources were deleted when not rollback")
    else:
        test_util.test_fail("Resource Stack status is not Failed")

    resource_norollback = resource_stack_ops.get_resource_from_resource_stack(resource_stack_norollback[0].uuid)
    if len(resource_norollback) == 0:
        test_util.test_fail("There has no resources when not rollback")
    
    test_util.test_pass('Resource Stack Rollback Test Success')


#Will be called only if exception happens in test().
def error_cleanup():
    print "Ignore cleanup"




