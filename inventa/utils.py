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
import random

contentReservedCharMap = {
    b"|": b"%pipe%",
    b"!": b"%exc%",
}


def randStringRunes(n: int) -> string:
    letters = string.ascii_lowercase + string.ascii_uppercase
    return "".join(random.choice(letters) for i in range(n))

def encodeContentArray(arr: list) -> bytes:
	for i, s in enumerate(arr):
		for key, val in contentReservedCharMap.items():
			s = s.replace(key, val)
		arr[i] = s
	return b"!".join(arr)

def decodeContentArray(encodedStr: bytes) -> list:
	arr = encodedStr.split(b"!")
	for i, s in enumerate(arr):
		for key, val in contentReservedCharMap.items():
			s = s.replace(val, key)
		arr[i] = s
	return arr