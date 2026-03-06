# EC2 Instance Manager

# Table of contents

<!--ts-->
- [EC2 Instance Manager](#ec2-instance-manager)
- [Table of contents](#table-of-contents)
  - [Python Version](#python-version)
  - [Third Party Libraries and Dependencies](#third-party-libraries-and-dependencies)
  - [Usage](#usage)
  - [Examples](#examples)
<!--te-->

## Python Version
Python 3.9+ are supported and tested


## Third Party Libraries and Dependencies

The following libraries will be installed when you install the client library:
* [typer](https://github.com/tiangolo/typer)
* [boto3](https://github.com/boto/boto3)

## Usage

To start using the library you need to setup a list of ENV variables with your AWS credentials as follows:
```sh
export AWS_DEFAULT_REGION=<...>
export AWS_ACCESS_KEY_ID=<...>
export AWS_SECRET_ACCESS_KEY=<...>
```
Then you can install a library with pip:

```sh
pip install .
```

If you plan to do a local developent you may also want install it in [editable mode](https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/#working-in-development-mode).
```sh
pip install --editable .
```

Afther the library is installed you can simply start it with --help option for retrieveing the further insructions
```sh
ecmgm --help
```

## Examples

Here is the list of example commands:

Create a VM, using existing AWS SSH key
```sh
ecmgm create <vm-name> <image> --osnick <osnick> --ssh-key-name <ssh-keypair-name>
```

Retrieve VM description
```sh
ecmgm describe <ami-id>
```

Teardown VM
```sh
ecmgm teardown <ami-id>  
```