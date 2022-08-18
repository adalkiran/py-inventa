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
from .service_descriptor import ServiceDescriptor
from .utils import encodeContentArray, decodeContentArray

class RPCCallRequest:
    def __init__(self, CallId: string, FromService: ServiceDescriptor, Method: string, Args: list):
        self.CallId = CallId
        self.FromService = FromService
        self.Method = Method
        self.Args = Args

    def Encode(self) -> bytes:
        for i, item in enumerate(self.Args):
            if item and not type(item) is bytes:
                self.Args[i] = item.encode()
        return ("req|" + self.CallId + "|" + self.FromService.Encode() + "|" + self.Method + "|").encode() + encodeContentArray(self.Args)
        
    def Decode(self, raw: bytes):
        rawParts = raw.split(b"|")
        self.CallId = rawParts[0].decode()
        self.FromService = ServiceDescriptor.ParseServiceFullId(rawParts[1].decode())
        self.Method = rawParts[2].decode()
        self.Args = decodeContentArray(rawParts[3])

    def ErrorResponse(self, e: Exception) -> list:
        return [b"error", "{0}".format(e).encode()]
