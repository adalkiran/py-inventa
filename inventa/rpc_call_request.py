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

class RPCCallRequest:
    def __init__(self, CallId: string, FromService: ServiceDescriptor, Method: string, Args: string):
        self.CallId = CallId
        self.FromService = FromService
        self.Method = Method
        self.Args = Args

    def Encode(self) -> string:
        return "req|" + self.CallId + "|" + self.FromService.Encode() + "|" + self.Method + "|" + self.Args
        
    def Decode(self, raw: string):
        rawParts = raw.split("|")
        self.CallId = rawParts[0]
        self.FromService = ServiceDescriptor.ParseServiceFullId(rawParts[1])
        self.Method = rawParts[2]
        self.Args = "|".join(rawParts[3:])

    def ErrorResponse(self, e: Exception) -> string:
        return "error|{0}".format(e)
