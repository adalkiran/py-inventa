# **Inventa for Go**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white&style=flat-square)](https://www.linkedin.com/in/alper-dalkiran/)
[![Twitter](https://img.shields.io/badge/Twitter-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white&style=flat-square)](https://twitter.com/aalperdalkiran)
![HitCount](https://hits.dwyl.com/adalkiran/go-inventa.svg?style=flat-square)
![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)

A Python library for microservice registry and executing RPC (Remote Procedure Call) over Redis.

## **WHY THIS PROJECT?**

Service dicovery, regisry and executing remote procedures are some of necessary tools in distributed applications. You must track which services (also how many replica instances of them) are alive. Also your services should communicate between eachother (careography) or via an orchestrator service on top of them.

You can do API/function calls remotely by serving REST APIs, gRPC endpoints, etc... But these choices came with some drawbacks or advantages, you have lots of different architectural options on this topic.

Inventa offers you a lightweight solution for these requirements; if you already have Redis in your project's toolbox, and if all of your services have access to this Redis instance.

Also Inventa doesn't abstract/hide its Redis client object, you can use it's Redis Client object freely which already connected to the server.

## **USAGE SCENARIO**

* You have an application that consists of multiple services, developed with different languages (currently [Go](https://github.com/adalkiran/go-inventa) and [Python](https://github.com/adalkiran/py-inventa) are supported),
* These services exist for different jobs, also they may be replicated into more than one instances, may be run in either different containers or machines,
* There is one registrar/orchestrator service which other services will register themselves and send their heartbeats to it,
* The orchestrator knows which service types and instances are alive now, the orchestrator should select one of instances of specific service, then call a function/procedure of the service, get a response remotely.
* All of your services will use Inventa, the one orchestrator service will instantiate it in **Orchestrator** Inventa role, other services will instantiate it in **Service** Inventa role.
* Both of Service roles and Orchestrator role can call functions that provided by other services, if they know target service's identifier.

## **INSTALLATION**

```sh
pip install inventa
```

## **EXAMPLE**

TODO: Coming soon, in progress...
## **OTHER IMPLEMENTATIONS**

You can find Python implementation of Inventa on [Inventa for Go (go-inventa)](https://github.com/adalkiran/go-inventa).

## **LICENSE**

Inventa for Go is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for the full license text.