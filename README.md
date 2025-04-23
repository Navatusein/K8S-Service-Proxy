# K8S-Service-Proxy

## Content

- [Information](#information)
- [Installation](#installation)
- [Command line arguments](#сommand-line-arguments)

<a id="information"></a>

## Information

The utility is designed for ease of development, in cases where you cannot deploy 
the service in a local cluster, but you have a remote development cluster. 
And to test the code, it needs to be deployed to the remote cluster.

### How it works

Lens configures Port Forwarding from the desired service from the remote cluster. Since Lens is configured to listen f
or connections to the port only from `localhost` the `k8s-sp` utility runs `socat` which proxies requests from 
`bridging port` to the port opened by Lens. We need this so that when `host-ip:bridging-port` is accessed, 
requests are redirected to `localhost:service-port`. The next step is for the `k8s-sp` utility to run a pod in the 
local cluster with `socat` which redirects requests from port `80` to the `bridging port`. It also creates a service with 
the name you passed in the startup parameters, so that other local services can access the service name from the remote 
cluster.

<a id="installation"></a>

## Installation

<a id="сommand-line-arguments"></a>

#### Download the utility

```shell
wget https://github.com/Navatusein/K8S-Service-Proxy/releases/latest/download/k8s-sp
```

or

```shell
curl --output k8s-sp https://github.com/Navatusein/K8S-Service-Proxy/releases/latest/download/k8s-sp
```

#### Give the utility the right to execute

```shell
chmod +x k8s-sp 
```

#### Run the utility with the arguments

```shell
./k8s-sp
```

## Command line arguments

```shell
usage: k8s-sp [-h] -n NAME -p PORT -H HOST [-N NAMESPACE] [-w]

options:
  -h, --help                           show this help message and exit
  -n NAME, --name NAME                 Service name
  -p PORT, --port PORT                 Service port from Lens port forwarding
  -H HOST, --host HOST                 Local host ip ect 192.168.1.100
  -N NAMESPACE, --namespace NAMESPACE  Namespace to deploy into
  -w, --wsl                            Launch socat via wt.exe in a new terminal tab
```
