#   Copyright (c) 2022-present, Adil Alper DALKIRAN
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#   ==============================================================================

import string
from datetime import datetime, timedelta
import time
from enum import Enum
from queue import Queue

from redis import asyncio as aioredis

from .endless_timer_task import EndlessTimerTask

from .service_descriptor import ServiceDescriptor
from .rpc_call_request import RPCCallRequest
import asyncio
import async_timeout

from .rpc_call_response import RPCCallResponse
from .utils import randStringRunes

class InventaRole(Enum):
    Orchestrator = 1
    Service = 2

class Inventa:
    def __init__(self, hostname: string, port: int, password: string, service_type: string, servicee_id: string, inventa_role: InventaRole, rpc_command_fn_registry):
        self.redis_url = f"redis://{hostname}:{port}"
        self.Client = aioredis.from_url(self.redis_url, password=password, socket_connect_timeout=10, redis_connect_func=self.onRedisConnect)
        self.SelfDescriptor = ServiceDescriptor(service_type, servicee_id)
        self.InventaRole = inventa_role
        self.RPCCommandFnRegistry = rpc_command_fn_registry
        self.OrchestratorDescriptor = None
        self.IsOrchestratorActive = False
        self.IsRegistered = False

        self.rpcInternalCommandFnRegistry = {
            "register":           self.rpcInternalCommandRegister,
            "orchestrator-alive": self.rpcInternalCommandOrchestratorAlive,
        }
        self.registeredServices = {}

        self.rpcRawQueue = asyncio.Queue()
        self.rpcRequestQueue = asyncio.Queue()
        self.rpcResponseQueue = asyncio.Queue()
        self._SetActiveTimer = None
        self._CheckRegisteredServices = None

        self.OnServiceRegistering = None
        self.OnServiceUnregistering = None

    def Start(self):
        loop = asyncio.get_event_loop()
        pingError = loop.run_until_complete(self.pingRedis())
        if pingError:
            raise Exception(f"Cannot connect to redis: {self.redis_url}, error: {pingError}")
        self.run(loop)


    async def onRedisConnect(self, conn):
        await conn.on_connect()
        if not await conn.can_read_destructive():
            return
        if self.IsRegistered:
            await self.pingRedis()
            await self.setSelfActive()
            await self.checkRegisteredServices()

    async def pingRedis(self) -> Exception:
        last_err = None
        for i in range(1, 10):
            try:
                if await self.Client.ping():
                    return None
            except Exception as e:
                last_err = e
                await asyncio.sleep(1)
        return last_err


    def run(self, event_loop: asyncio.AbstractEventLoop):
        event_loop.create_task(self.runRawQueueProcessor())
        event_loop.create_task(self.runRequestQueueProcessor())

        event_loop.create_task(self.runSubscribeInternal(self.SelfDescriptor.GetPubSubChannelName(), self.rpcRawQueue))
        self._SetActiveTimer = EndlessTimerTask(3, self.setSelfActive)
        event_loop.create_task(self._SetActiveTimer.start())
        self._CheckRegisteredServices = EndlessTimerTask(4, self.checkRegisteredServices)
        event_loop.create_task(self._CheckRegisteredServices.start())
        
    async def CallSync(self, serviceChannel: string, method: string, args: list, timeout: int) -> list:
        req = self.newRPCCallRequest(method, args)
        await self.Client.publish("ch:" + serviceChannel, req.Encode())

        timeout_time = datetime.utcnow() + timedelta(milliseconds=timeout)
        while datetime.utcnow() < timeout_time:
            try:
                async with async_timeout.timeout(timeout/1000):
                    resp = await self.rpcResponseQueue.get()
                    if resp and resp.CallId == req.CallId:
                        if resp.Data[0] == "error":
                            if len(resp.Data) > 1:
                                raise Exception(resp.Data[1])
                            raise Exception("undescribed error")
                        await asyncio.sleep(.01)
                        return resp.Data
                    else:
                        await self.rpcResponseQueue.put(resp)
                        await asyncio.sleep(.01)
                    self.rpcResponseQueue.task_done()
            except asyncio.TimeoutError:
                pass
        raise Exception("timeout")

    async def runRawQueueProcessor(self):
        while True:
            rawMsg = await self.rpcRawQueue.get()
            rawMsgParts = rawMsg.split(b"|")
            rawMsgType = rawMsgParts[0].decode("UTF-8")
            if rawMsgType == "req":
                req = RPCCallRequest("", 0, "", "")
                req.Decode(rawMsg[len(rawMsgType)+1:])
                await self.rpcRequestQueue.put(req)
            elif rawMsgType == "resp":
                resp = RPCCallResponse("", 0, "")
                resp.Decode(rawMsg[len(rawMsgType)+1:])
                await self.rpcResponseQueue.put(resp)
            self.rpcRawQueue.task_done()
            await asyncio.sleep(.01)

    async def runRequestQueueProcessor(self):
        while True:
            req = await self.rpcRequestQueue.get()
            rpcCommandFn = None
            if req.Method in self.rpcInternalCommandFnRegistry:
                rpcCommandFn = self.rpcInternalCommandFnRegistry[req.Method]
            elif req.Method in self.RPCCommandFnRegistry:
                rpcCommandFn = self.RPCCommandFnRegistry[req.Method]
            
            cmdResult = None
            if rpcCommandFn is None:
                print(f"Unknown command type: {req.Method}\n")
                cmdResult = req.ErrorResponse(Exception(f"unknown command type: {req.Method}"))
            else:
                cmdResult = rpcCommandFn(req)
                if not isinstance(cmdResult, list):
                    print(f"Error: command \"{req.Method}\" should return a list, it returned: {cmdResult}\n")
                    cmdResult = req.ErrorResponse(Exception(f"command \"{req.Method}\" should return a list, it returned: {cmdResult}"))
            resp = self.newRPCCallResponse(req, cmdResult)
            await self.Client.publish("ch:" + req.FromService.Encode(), resp.Encode())
            self.rpcRequestQueue.task_done()
            await asyncio.sleep(.01)


    async def runSubscribeInternal(self, pubSubChannelName: string, messageQueue: Queue):
        async def handle_msg(message):
            if message["type"] == "message":
                await messageQueue.put(message["data"])
        
        async def reader(channel: aioredis.client.PubSub):
            while True:
                try:
                    async with async_timeout.timeout(11):
                        message = await channel.get_message(ignore_subscribe_messages=True, timeout=10)
                        if message is not None:
                            asyncio.ensure_future(handle_msg(message))
                        await asyncio.sleep(.01)
                except asyncio.TimeoutError:
                    pass
                except aioredis.ConnectionError:
                    # See: https://lightrun.com/answers/redis-redis-py-asyncio-pubsub-does-not-automatically-reconnect
                    errorPrinted = False
                    while not channel.connection.is_connected:
                        try:
                            if not errorPrinted:
                                print(f"Redis connection reset. Resubscribing to channels {list(channel.channels.keys())}")
                            await channel.connect()
                            print(f"Redis connection was established again. Resubscribed to channels {list(channel.channels.keys())}")
                        except Exception as e:
                            if not errorPrinted:
                                print(f"Error: {e}")
                                errorPrinted = True
                            await asyncio.sleep(.1)



        # See: https://aioredis.readthedocs.io/en/latest/examples/#pubsub
        pubsub = self.Client.pubsub()
        async with pubsub as p:
            await p.subscribe(pubSubChannelName)
            await reader(p)  # wait for reader to complete
            await p.unsubscribe(pubSubChannelName)

        # closing all open connections
        await pubsub.close()

    async def IsServiceActive(self, serviceFullId: string) -> bool:
        return await self.Client.get(serviceFullId) is not None
    
    async def TryRegisterToOrchestrator(self, orchestratorFullId: string, tryCount: int, timeout: int):
        orchestratorDescriptor = ServiceDescriptor.ParseServiceFullId(orchestratorFullId)
        lastErr = None
        if tryCount < 1:
            tryCount = 1
        self.OrchestratorDescriptor = orchestratorDescriptor
        for i in range(1, tryCount):
            print(datetime.utcnow(), f"Trying to register to {orchestratorFullId}...")
            try:
                await self.CallSync(orchestratorFullId, "register", [self.SelfDescriptor.Encode()], timeout)
            except Exception as e:
                lastErr = e
                print(datetime.utcnow(), f"Error while registering: {e}. Remaining try count: {tryCount-i}")
                continue
            self.IsRegistered = True
            self.IsOrchestratorActive = True
            await self.setSelfActive()
            return
        if lastErr is not None:
            raise lastErr


    def newRPCCallRequest(self, method: string, args: list) -> RPCCallRequest:
        return RPCCallRequest(randStringRunes(5) + "-" + str(int(time.time())),
            self.SelfDescriptor,
            method,
            args)

    def newRPCCallResponse(self, req: RPCCallRequest, data: list) -> RPCCallResponse:
        return RPCCallResponse(req.CallId,
            self.SelfDescriptor,
            data)

    async def setSelfActive(self):
        if self.InventaRole != InventaRole.Orchestrator and not self.IsRegistered:
            return
        try:
            await self.pingRedis()
            await self.Client.setex(self.SelfDescriptor.Encode(), timedelta(milliseconds=5000), 1)
        except Exception as e:
            print("cannot set service status on redis: ", e)

    async def checkRegisteredServices(self):
        if self.InventaRole == InventaRole.Orchestrator:
            for serviceDescriptor in self.registeredServices:
                if not await self.IsServiceActive(serviceDescriptor.Encode()):
                    if not self.OnServiceUnregistering:
                        err = f"the orchestrator service \"{self.SelfDescriptor.Encode()}\" has not implemented \"OnServiceUnregistering\" event function"
                        print(f"Error on checkRegisteredServices: {err}")
                        continue
                    else:
                        self.OnServiceUnregistering(serviceDescriptor, True)
                    del self.registeredServices[serviceDescriptor]
        elif self.InventaRole == InventaRole.Service:
            if not self.OrchestratorDescriptor:
                return
            if not await self.IsServiceActive(self.OrchestratorDescriptor.Encode()):
                if self.IsOrchestratorActive:
                    print(f"Error: The orchestrator service {self.OrchestratorDescriptor.Encode()} is not alive anymore.")
                self.IsOrchestratorActive = False
            elif not self.IsOrchestratorActive:
                self.IsOrchestratorActive = True
                print(f"The orchestrator service {self.OrchestratorDescriptor.Encode()} is alive again.")

    def rpcInternalCommandRegister(self, req: RPCCallRequest) -> list:
        serviceDescriptor = ServiceDescriptor.ParseServiceFullId(req.Args.decode())
        if self.SelfDescriptor.Encode() == serviceDescriptor.Encode():
            return [b"ignored-self"]
        if not self.OnServiceRegistering:
            err = f"the orchestrator service \"{self.SelfDescriptor.Encode()}\" has not implemented \"OnServiceRegistering\" event function"
            print(f"Error on rpcInternalCommandRegister: {err}")
            return req.ErrorResponse(err)
        try:
            self.OnServiceRegistering(serviceDescriptor)
        except Exception as e:
            return req.ErrorResponse(e)
        self.registeredServices[serviceDescriptor.Encode()] = True
        return [b"registered"]


    def rpcInternalCommandOrchestratorAlive(self, req: RPCCallRequest) -> list:
        if self.InventaRole != InventaRole.Service:
            return [b"ignored-not-service"]
        orchestratorDescriptor = ServiceDescriptor.ParseServiceFullId(req.Args[0].decode())
        if orchestratorDescriptor.Encode() != self.OrchestratorDescriptor.Encode():
            return [b"ignored-unknown-source"]
        self.IsOrchestratorActive = True
        print(f"The orchestrator service {self.OrchestratorDescriptor.Encode()} is alive again.")
        return [b"ok"]
