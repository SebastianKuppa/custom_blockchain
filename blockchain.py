import hashlib
from time import time
import json


class BlockChain:
    def __init__(self):
        self.current_transactions = []
        self.chain = []

    def new_block(self, proof, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        # empty current transactions
        self.current_transactions = []
        self.chain.append(block)
        return block

