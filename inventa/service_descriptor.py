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

class ServiceDescriptor:
	def __init__(self, ServiceType: string, ServiceId: string):
		self.ServiceType = ServiceType
		self.ServiceId = ServiceId
	
	def Encode(self) -> string:
		return "svc:" + self.ServiceType + ":" + self.ServiceId

	def Decode(self, serviceFullId: string):
		rawParts = serviceFullId.split(":")
		if len(rawParts) != 3 or rawParts[0] != "svc":
			raise Exception("invalid ServiceDescriptor value: {0}".format(serviceFullId))
		self.ServiceType = rawParts[1]
		self.ServiceId = rawParts[2]
	def GetPubSubChannelName(self) -> string:
		return "ch:" + self.Encode()

	@staticmethod
	def ParseServiceFullId(serviceFullId: string) -> 'ServiceDescriptor':
		result = ServiceDescriptor("", "")
		try:
			result.Decode(serviceFullId)
		except Exception as e:
			raise Exception("error while decoding service name \"{0}\": {1}".format(serviceFullId, e))
		return result
