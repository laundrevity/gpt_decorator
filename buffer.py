from typing import List, Dict
import traceback
import tiktoken
import json


class Buffer:
    def __init__(self, max_tokens: int = 8192, min_free_tokens: int = 100):
        self.max_tokens = max_tokens
        self.min_free_tokens = min_free_tokens
        self.enc = tiktoken.get_encoding('cl100k_base')
        self.messages: List[Dict[str, str]] = []

    def get_current_length(self) -> int:
        tot = 0
        for message in self.messages:
            tot += len(self.enc.encode(json.dumps(message)))
        return tot
    
    def append(self, message: Dict[str, str]):
        cur_len = self.get_current_length()
        msg_len = len(self.enc.encode(json.dumps(message)))

        while cur_len + msg_len > self.max_tokens - self.min_free_tokens:
            print(f'{cur_len=}, {msg_len=} too big')
            # pop the oldest message
            try:
                oldest = self.messages.pop(0)
                oldest_len = len(self.enc.encode(json.dumps(oldest)))
                print(f"+ [{oldest_len}]: Forgetting {oldest}...")
                msg_len -= oldest_len
            except Exception as e:
                print(f"Got error {e}")
                traceback.print_exc()
                return

        if len(self.messages) != 0 and message != self.messages[-1]:
            self.messages.append(message)
        elif len(self.messages) == 0:
            self.messages.append(message)
