from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute.models import DiskCreateOption
import os
import traceback
from typing import List
import sys
import time
import json

from azure.common.client_factory import (
    get_client_from_json_dict,
    get_client_from_cli_profile,
)

from azure.mgmt.compute.models import (
    VirtualMachineExtensionInstanceView,
    VirtualMachineExtension
)

SUBSCRIPTION_ID = os.environ['AZURE_SUBSCRIPTION_ID']
GROUP_NAME = 'mb8azure-sample-group-virtual-machines'
LOCATION = 'centralus'
VM_NAME = 'mb8WindowsVM'
NIC_NAME = 'mb8azure-sample-nic'

VM_EXTENSION_EXECUTION_CODE_FAIL_PREFIX = "ProvisioningState/failed/"
VM_EXTENSION_EXECUTION_CODE_SUCCESS_PREFIX = "ProvisioningState/succeeded"
TIMEOUT_SECONDS = 3600
EXTENSION_NAME = "CSEOK"

def get_credentials():
    subscription_id = os.environ['AZURE_SUBSCRIPTION_ID']
    credentials = ServicePrincipalCredentials(
        client_id=os.environ['AZURE_CLIENT_ID'],
        secret=os.environ['AZURE_CLIENT_SECRET'],
        tenant=os.environ['AZURE_TENANT_ID']
    )
    return credentials, subscription_id


def create_resource_group(resource_group_client):
    resource_group_client.resource_groups.create_or_update(
        GROUP_NAME, {'location': LOCATION})

def create_availability_set(compute_client):
    avset_params = {
        'location': LOCATION,
        'sku': { 'name': 'Aligned' },
        'platform_fault_domain_count': 3
    }
    availability_set_result = compute_client.availability_sets.create_or_update(
        GROUP_NAME,
        'myAVSet',
        avset_params
    )

def create_public_ip_address(network_client):
    public_ip_addess_params = {
        'location': LOCATION,
        'public_ip_allocation_method': 'Dynamic'
    }
    creation_result = network_client.public_ip_addresses.create_or_update(
        GROUP_NAME,
        'mbIPAddress',
        public_ip_addess_params
    )

    return creation_result.result()


def create_vnet(network_client):
    vnet_params = {
        'location': LOCATION,
        'address_space': {
            'address_prefixes': ['10.0.0.0/16']
        }
    }
    creation_result = network_client.virtual_networks.create_or_update(
        GROUP_NAME,
        'myVNet',
        vnet_params
    )
    return creation_result.result()

def create_subnet(network_client):
    subnet_params = {
        'address_prefix': '10.0.0.0/24'
    }
    creation_result = network_client.subnets.create_or_update(
        GROUP_NAME,
        'myVNet',
        'mySubnet',
        subnet_params
    )

    return creation_result.result()

def create_nic(network_client):
    subnet_info = network_client.subnets.get(
        GROUP_NAME,
        'myVNet',
        'mySubnet'
    )
    publicIPAddress = network_client.public_ip_addresses.get(
        GROUP_NAME,
        'mbIPAddress'
    )
    nic_params = {
        'location': LOCATION,
        'ip_configurations': [{
            'name': 'myIPConfig',
            'public_ip_address': publicIPAddress,
            'subnet': {
                'id': subnet_info.id
            }
        }]
    }
    creation_result = network_client.network_interfaces.create_or_update(
        GROUP_NAME,
        NIC_NAME,
        nic_params
    )

    return creation_result.result()

def create_vm(network_client, compute_client):
    nic = network_client.network_interfaces.get(
        GROUP_NAME,
        NIC_NAME
    )
    avset = compute_client.availability_sets.get(
        GROUP_NAME,
        'myAVSet'
    )
    vm_parameters = {
        'location': LOCATION,
        'os_profile': {
            'computer_name': VM_NAME,
            'admin_username': 'azureuser',
            'admin_password': 'Pa$$w0rd123###'
        },
        'hardware_profile': {
            'vm_size': 'Standard_DS1'
        },
        'storage_profile': {
            'image_reference': {
                'publisher': 'MicrosoftWindowsServer',
                'offer': 'WindowsServer',
                'sku': '2012-R2-Datacenter',
                'version': 'latest'
            }
        },
        'network_profile': {
            'network_interfaces': [{
                'id': nic.id
            }]
        },
        'availability_set': {
            'id': avset.id
        }
    }
    creation_result = compute_client.virtual_machines.create_or_update(
        GROUP_NAME,
        VM_NAME,
        vm_parameters
    )

    return creation_result.result()

def get_vm(compute_client):
    vm = compute_client.virtual_machines.get(GROUP_NAME, VM_NAME, expand='instanceView')
    print("hardwareProfile")
    print("   vmSize: ", vm.hardware_profile.vm_size)
    print("\nstorageProfile")
    print("  imageReference")
    print("    publisher: ", vm.storage_profile.image_reference.publisher)
    print("    offer: ", vm.storage_profile.image_reference.offer)
    print("    sku: ", vm.storage_profile.image_reference.sku)
    print("    version: ", vm.storage_profile.image_reference.version)
    print("  osDisk")
    print("    osType: ", vm.storage_profile.os_disk.os_type.value)
    print("    name: ", vm.storage_profile.os_disk.name)
    print("\nosProfile")
    print("  computerName: ", vm.os_profile.computer_name)
    print("  adminUsername: ", vm.os_profile.admin_username)
    print("  provisionVMAgent: {0}".format(vm.os_profile.windows_configuration.provision_vm_agent))
    print("  enableAutomaticUpdates: {0}".format(vm.os_profile.windows_configuration.enable_automatic_updates))
    print("\nnetworkProfile")
    for nic in vm.network_profile.network_interfaces:
        print("  networkInterface id: ", nic.id)
    for disk in vm.instance_view.disks:
        print("  name: ", disk.name)
        print("  statuses")
        for stat in disk.statuses:
            print("    code: ", stat.code)
            print("    displayStatus: ", stat.display_status)
            print("    time: ", stat.time)
    print("\nVM general status")
    print("  provisioningStatus: ", vm.provisioning_state)
    print("  id: ", vm.id)
    print("  name: ", vm.name)
    print("  type: ", vm.type)
    print("  location: ", vm.location)
    print("\nVM instance status")
    for stat in vm.instance_view.statuses:
        print("  code: ", stat.code)
        print("  displayStatus: ", stat.display_status)

def deploy_extension(ComputeManagementClient):
    print("Deploying Custom Extension...\n")


    storage_account_name="mbtests1"
    storage_account_key="NFWmCX2N"

    params_create = {
        'location': LOCATION,
        'publisher': 'Microsoft.Compute',
        'virtual_machine_extension_type': 'CustomScriptExtension',
        'type_handler_version': '1.10',
        'auto_upgrade_minor_version': True,
        'settings': {
            'fileUris': ["https://mbtests1.blob.core.windows.net/quickstartblobs1/RC0.ps1", \
                            "https://mbtests1.blob.core.windows.net/quickstartblobs1/RC2.ps1"],
            'commandToExecute': "powershell -ExecutionPolicy Unrestricted -File RC2.ps1"
        },
        'protected_settings' : {
            'storageAccountName': storage_account_name,
            'storageAccountKey': storage_account_key
        },
        'forceUpdateTag': '10'
    }
    ext_poller = ComputeManagementClient.virtual_machine_extensions.create_or_update( GROUP_NAME, VM_NAME, 'CSEOK', params_create )
    ext = ext_poller.result(timeout=TIMEOUT_SECONDS)
    #check_custom_extension_deployment_status()
    print("Result: ")
    print("Response content", ext_poller._response.content)
    print("Response time elapsed (seconds)", ext_poller._response.elapsed.seconds)
    print("Response status code", ext_poller._response.status_code)
    print("Response text", ext_poller._response.text)
    print("Ext Status", ext.provisioning_state)
    print("Finished Deploying Custom Extension (OK, CloudError, TimeOut).")

def deploynvidia_extension(ComputeManagementClient):
    print("Deploying nvidia Extension...\n")


    params_create = {
        'location': LOCATION,
        'publisher': 'Microsoft.HpcCompute',
        'virtual_machine_extension_type': 'NvidiaGpuDriverWindows',
        'type_handler_version': '1.2',
        'auto_upgrade_minor_version': True,
    }


    ext_poller = ComputeManagementClient.virtual_machine_extensions.create_or_update( GROUP_NAME, VM_NAME, 'nvidiaextension', params_create )
    ext = ext_poller.result(timeout=TIMEOUT_SECONDS)
    #check_custom_extension_deployment_status()
    print("Result: ")
    print("Response content", ext_poller._response.content)
    print("Response time elapsed (seconds)", ext_poller._response.elapsed.seconds)
    print("Response status code", ext_poller._response.status_code)
    print("Response text", ext_poller._response.text)
    print("Ext Status", ext.provisioning_state)
    print("Finished Deploying Custom Extension (OK, CloudError, TimeOut).")



if __name__ == "__main__":
    credentials, subscription_id = get_credentials()

resource_group_client = ResourceManagementClient(
    credentials,
    SUBSCRIPTION_ID
)
network_client = NetworkManagementClient(
    credentials,
    SUBSCRIPTION_ID
)
compute_client = ComputeManagementClient(
    credentials,
    SUBSCRIPTION_ID
)


create_resource_group(resource_group_client)


create_availability_set(compute_client)
print("------------------------------------------------------")


creation_result = create_public_ip_address(network_client)
print("------------------------------------------------------")
print(creation_result)


creation_result = create_vnet(network_client)
print("------------------------------------------------------")
print(creation_result)


creation_result = create_subnet(network_client)
print("------------------------------------------------------")
print(creation_result)


creation_result = create_nic(network_client)
print("------------------------------------------------------")
print(creation_result)


creation_result = create_vm(network_client, compute_client)
print("------------------------------------------------------")
print(creation_result)

#deploy_extension(extension_client)
#deploynvidia_extension(extension_client)
#print("------------------------------------------------------")
#print("Extension Deployed")


#check_custom_extension_deployment_status()

get_vm(compute_client)
print("------------------------------------------------------")

