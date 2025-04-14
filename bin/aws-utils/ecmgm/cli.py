import getpass
from typing import Optional

import boto3
import typer
from rich.console import Console, Group
from rich.panel import Panel
from rich.prompt import Confirm
from rich.syntax import Syntax
from rich.table import Table

from ecmgm import __app_name__, __version__, schemas, utils

app = typer.Typer()
console = Console()


@app.command()
def listvm():
    ec2 = boto3.client("ec2")
    response = ec2.describe_instances()
    table = Table(title="Instance list")

    for column in [
        "Tags",
        "ImageId",
        "InstanceId",
        "InstanceType",
        "LaunchTime",
        "Monitoring",
        "PublicDnsName",
    ]:
        table.add_column(column, style="magenta")

    for r in response["Reservations"]:
        for i in r["Instances"]:
            table.add_row(
                i["Tags"][0]["Value"],
                i["ImageId"],
                i["InstanceId"],
                i["InstanceType"],
                str(i["LaunchTime"]),
                str(i["Monitoring"]),
                i["PublicDnsName"],
            )

    console.print(table)


@app.command()
def describe(instance_id: str = typer.Argument(..., help="EC2 Instance Id")):
    ec2 = boto3.client("ec2")
    table = Table(title="Instance details")
    table.add_column("Attribute", style="magenta")
    table.add_column("Value", justify="left", style="cyan")

    response = ec2.describe_instances(
        InstanceIds=[
            instance_id,
        ],
    )

    for k, v in response["Reservations"][0]["Instances"][0].items():
        table.add_row(k, str(v))

    console.print(table)


@app.command()
def teardown(instance_id: str = typer.Argument(..., help="EC2 Instance Id")):
    instance = utils.terminate_instance(instance_id)
    with console.status("[bold green]Waiting for EC2 Instance being terminated..."):
        instance.wait_until_terminated()


@app.command()
def create(
    name: str = typer.Argument(..., help="Virtual machine name"),
    os_image: schemas.OsImage = typer.Argument(..., help="OS image"),
    instance_type: schemas.InstanceTypes = typer.Option(
        schemas.InstanceTypes.small.value, help="Instance types"
    ),
    instance_arch: schemas.InstanceArch = typer.Option(
        schemas.InstanceArch.x86_64.value, help="Instance Arch"
    ),
    osnick: str = typer.Option("", help="Optionally filter images by specified osnick"),
    ssh_key_name: str = typer.Option(
        "", help="You can specify your SSH key name in case its already created in AWS"
    ),
    host_id: str = typer.Option(
        "",
        help="Dedicated host id (in case you are spinning macos instance) if not provided will be created by default",
    ),
):
    if (
        instance_type == schemas.InstanceTypes.macmetal.value
        and instance_arch != schemas.InstanceArch.x86_64_mac.value
    ):
        raise ValueError(
            f"Unsoported instance_arch, mac instance types supports only {schemas.InstanceArch.x86_64_mac.value}"
        )
    if (
        instance_arch == schemas.InstanceArch.x86_64_mac.value
        and instance_type != schemas.InstanceTypes.macmetal.value
    ):
        raise ValueError(
            f"Unsoported instance type, mac instance arch supports only {schemas.InstanceTypes.macmetal.value}"
        )
    ec2 = boto3.client("ec2")
    image_filter_query = schemas.OS_SEARCH_MAPPING[os_image]

    if osnick:
        image_filter_query += f"{osnick}*"

    with console.status(
        f"[bold green]Searching for image. Search params: query: {image_filter_query} arch: {instance_arch} osnick: {osnick}..."
    ):
        images = ec2.describe_images(
            Filters=[
                {
                    "Name": "architecture",
                    "Values": [
                        instance_arch,
                    ],
                },
                {"Name": "root-device-type", "Values": ["ebs"]},
                {"Name": "state", "Values": ["available"]},
                {"Name": "virtualization-type", "Values": ["hvm"]},
                {"Name": "hypervisor", "Values": ["xen"]},
                {"Name": "image-type", "Values": ["machine"]},
                {
                    "Name": "name",
                    "Values": [image_filter_query],
                },
            ],
            Owners=["amazon"],
        )

    sorted_amis = sorted(
        images["Images"], key=lambda x: x["CreationDate"], reverse=True
    )
    target_image = sorted_amis[0]
    panel_group = Group(
        Panel(
            target_image["ImageId"],
            title="ami-id",
        ),
        Panel(target_image["Description"], title="Description"),
        Panel(target_image["ImageLocation"], title="Image"),
    )
    console.print("Image found, details:")
    console.print(Panel(panel_group))

    is_continue = Confirm.ask("Do you want to continue?")
    if not is_continue:
        raise typer.Exit()

    if not ssh_key_name:
        console.print(f"No SSH key was specified, creating new")
        private_key_name = f"{getpass.getuser()}-ec2-{os_image.value}-key"
        private_key_filename = f"{getpass.getuser()}-ec2-{os_image.value}-key-file.pem"
        key_pair = utils.create_key_pair(private_key_name, private_key_filename)
        console.print(f"Created a key pair [bold cyan]{key_pair.key_name}[/bold cyan]")

    if instance_type == schemas.InstanceTypes.macmetal.value and not host_id:
        console.print(
            f"Creating dedicated host for instance type: [bold cyan]{instance_type}[/bold cyan]"
        )
        host_id = utils.allocate_hosts(instance_type)
        console.print(
            f"Dedicated host with id [bold cyan]{host_id}[/bold cyan] created"
        )

    instance = utils.create_instance(
        target_image["ImageId"],
        name,
        instance_type,
        ssh_key_name or key_pair.key_name,
        ["redis-io-group"],  # todo default security group is temporary hardcoded
        host_id,
    )

    with console.status("[bold green]Waiting for EC2 Instance to start..."):
        instance.wait_until_running()
        # updating instance attributes to obtain public ip/dns immediately
        instance.reload()

    private_key_filename = private_key_filename if not ssh_key_name else "your-key.pem"
    panel_group = Group(
        Panel("You can now connect to your ec2 machine :thumbs_up:\n"),
        Panel(
            Syntax(
                f"ssh -i {private_key_filename} {schemas.OS_DEFAULT_USER_MAP[os_image]}@{instance.public_dns_name}",
                "shell",
                theme="monokai",
            ),
            title="Command",
        ),
        Panel(
            Syntax(
                f"# you also might need to make key to be only readable by you\nchmod 400 {private_key_filename}\n"
                f"# You may use that instance id -> [{instance.id} <- in other CLI commands like\n"
                "# Get VM details\n"
                f"ecmgm describe {instance.id}\n"
                "# Terminate VM\n"
                f"ecmgm teardown {instance.id}",
                "shell",
                theme="monokai",
            ),
            title="Tip",
        ),
    )
    console.print(Panel(panel_group))


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the application's version and exit.",
        callback=_version_callback,
        is_eager=True,
    )
) -> None:
    return
