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

    def new_transaction(self, sender, recipient, amount):
        self.current_transactions.append({
                'sender': sender,
                'recipient': recipient,
                'amount': amount,
        })
        return self.last_block['index'] + 1

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Creates a SHA256 has for the block
        :param block: input block
        :return: hash
        """
        block_string = json.dumps(block, sort_keys=True).encode()

        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_proof):
        """
        Simple Proof of Work algorithm. Find a number p' where hash(pp') contains 4 leading zeroes, where p
        is the previous p'
        p: previous proof, p' new proof
        :param last_proof:previous proof
        :return: new proof
        """
        proof = 0
        while not self.valid_proof(last_proof, proof):
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Analyzing hash for the first 4 chars contain zero
        :param last_proof: <int>
        :param proof: <int>
        :return: <bool>
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == '0000'
