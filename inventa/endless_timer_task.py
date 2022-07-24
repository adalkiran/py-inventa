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

import asyncio

class EndlessTimerTask:
    def __init__(self, delay, fn, *args, **kwargs):
        self.delay = delay
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.exit = False
    
    async def start(self):
        while not self.exit:
            await asyncio.sleep(self.delay)
            if asyncio.iscoroutinefunction(self.fn):
                await self.fn(*self.args, **self.kwargs)
            else:
                self.fn(*self.args, **self.kwargs)
    
    def stop(self):
        self.exit = True
    