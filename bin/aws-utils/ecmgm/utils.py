import base64
import os
import struct

import boto3
import paramiko
from botocore.exceptions import ClientError
from paramiko.util import deflate_long
from rich.console import Console

console = Console()
ec2 = boto3.resource("ec2")


def start_instance(instance_id):
    try:
        response = ec2.Instance(instance_id).start()
        console.print(f"Started instance {instance_id}")
    except ClientError:
        console.print(f"Couldn't start instance {instance_id}")
        raise
    else:
        return response


def stop_instance(instance_id):
    try:
        response = ec2.Instance(instance_id).stop()
        console.print(f"Stopped instance {instance_id}")
    except ClientError:
        console.print(f"Couldn't stop instance {instance_id}")
        raise
    else:
        return response


def get_console_output(instance_id):
    try:
        output = ec2.Instance(instance_id).console_output()["Output"]
        console.print(f"Got console output for instance {instance_id}")
    except ClientError:
        console.print((f"Couldn't get console output for instance {instance_id}"))
        raise
    else:
        return output


def import_key_pair(key_name: str, private_key_file_path: str) -> ec2.KeyPair:
    key = paramiko.RSAKey.from_private_key_file(private_key_file_path)

    output = b""
    parts = [
        b"ssh-rsa",
        deflate_long(key.public_numbers.e),
        deflate_long(key.public_numbers.n),
    ]

    for part in parts:
        output += struct.pack(">I", len(part)) + part
    public_key = b"ssh-rsa " + base64.b64encode(output) + b"\n"

    key_pair = ec2.import_key_pair(KeyName=key_name, PublicKeyMaterial=public_key)
    return key_pair


def create_key_pair(key_name: str, private_key_file_name: str = None) -> ec2.KeyPair:
    try:
        key_pair = ec2.create_key_pair(KeyName=key_name)
        console.print(f"Created key [bold cyan]{key_pair.name}[/bold cyan].")
        if private_key_file_name is not None:
            with open(private_key_file_name, "w") as pk_file:
                pk_file.write(key_pair.key_material)
            console.print(
                f"Wrote private key to [bold cyan]{private_key_file_name}[/bold cyan]."
            )
    except ClientError:
        console.print(f"Couldn't create key {key_name}.")
        raise
    else:
        return key_pair


def setup_security_group(group_name, group_description, ssh_ingress_ip=None):
    try:
        default_vpc = list(
            ec2.vpcs.filter(Filters=[{"Name": "isDefault", "Values": ["true"]}])
        )[0]
        console.print(f"Got default VPC {default_vpc.id}")
    except ClientError:
        console.print("Couldn't get VPCs.")
        raise
    except IndexError:
        console.print("No default VPC in the list.")
        raise

    try:
        security_group = default_vpc.create_security_group(
            GroupName=group_name, Description=group_description
        )
        console.print(f"Created security group {group_name} in VPC {default_vpc.id}.")
    except ClientError:
        console.print(f"Couldn't create security group {group_name}.")
        raise

    try:
        ip_permissions = [
            {
                # HTTP ingress open to anyone
                "IpProtocol": "tcp",
                "FromPort": 80,
                "ToPort": 80,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            },
            {
                # HTTPS ingress open to anyone
                "IpProtocol": "tcp",
                "FromPort": 443,
                "ToPort": 443,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            },
        ]
        if ssh_ingress_ip is not None:
            ip_permissions.append(
                {
                    # SSH ingress open to only the specified IP address
                    "IpProtocol": "tcp",
                    "FromPort": 22,
                    "ToPort": 22,
                    "IpRanges": [{"CidrIp": f"{ssh_ingress_ip}/32"}],
                }
            )
        security_group.authorize_ingress(IpPermissions=ip_permissions)
        console.print(
            f"Set inbound rules for {security_group.id} to allow all inbound HTTP and HTTPS "
            f"but only {ssh_ingress_ip} for SSH."
        )
    except ClientError:
        console.print(f"Couldnt authorize inbound rules for {group_name}.")
        raise
    else:
        return security_group


def create_instance(
    image_id: str,
    name: str,
    instance_type: str,
    key_name: str,
    security_group_names: list = None,
):
    try:
        instance_params = {
            "ImageId": image_id,
            "InstanceType": instance_type,
            "KeyName": key_name,
            "TagSpecifications": [
                {
                    "ResourceType": "instance",
                    "Tags": [
                        {"Key": "Name", "Value": name},
                    ],
                },
            ],
        }
        if security_group_names is not None:
            instance_params["SecurityGroups"] = security_group_names
        instance = ec2.create_instances(**instance_params, MinCount=1, MaxCount=1)[0]
        console.print(f"Created instance [bold cyan]{instance.id}[/bold cyan].")
    except ClientError:
        console.print(
            f"Couldn't create instance with image {image_id}, instance type {instance_type}, and key {key_name}."
        )
        raise
    else:
        return instance


def delete_key_pair(key_name: str, key_file_name: str) -> None:
    """
    Deletes a key pair and the specified private key file.
    """
    try:
        ec2.KeyPair(key_name).delete()
        os.remove(key_file_name)
        console.print(f"Deleted key {key_name} and private key file {key_file_name}.")
    except ClientError:
        console.print(f"Couldn't delete key {key_name}.")
        raise


def delete_security_group(group_id):
    """
    Deletes a security group.
    """
    try:
        ec2.SecurityGroup(group_id).delete()
        console.print(f"Deleted security group {group_id}.")
    except ClientError:
        console.print(
            f"Couldn't delete security group {group_id}.",
        )
        raise


def terminate_instance(instance_id):
    """
    Terminates an instance. The request returns immediately.
    """
    try:
        instance = ec2.Instance(instance_id)
        instance.terminate()
        console.print(f"Terminating instance {instance_id}.")
        return instance
    except ClientError:
        console.print(f"Couldn't terminate instance {instance_id}.")
        raise
