import hashlib
from time import time
import json
from urllib.parse import urlparse

import requests
from flask import Flask, jsonify, request
from uuid import uuid4


class BlockChain:
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes = set()

    def valid_chain(self, chain: list) -> bool:
        """
        Determine if a given blockchain is valid
        :param chain: <list> A blockchain
        :return: <bool> True if valid, false if not
        """
        if not chain:
            return False
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'last_block: {last_block}')
            print(f'block: {block}')
            print(f'_'*20)
            if block['previous_hash'] != self.hash(last_block):
                return False
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False
            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        This method resolves conflicts about the current state of the blockchain. It replaces the chain
        with the longest one in the network.
        :return: <bool> True if chain was replaced, False if not
        """
        neighbours = self.nodes
        new_chain = None

        # only looking for chains which are longer than ours
        max_length = len(self.chain)

        # grab and verify the chains from all the nodes in the network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
        # replace our chain if we discovered a new and valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def register_node(self, address):
        """
        Adds new node to the list of nodes
        :param address: <str> node url. Eg. "https://192.168.2.0:80"
        :return: None
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

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


app = Flask(__name__)

# generate unique address for this node
node_identifier = str(uuid4()).replace('-', '')
# init blockchain
blockchain = BlockChain()
blockchain.new_block(proof=1, previous_hash=1)


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'new nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # node identifier receives reward for finding new proof
    # sender address is '0' to show that this coin was mined
    blockchain.new_transaction(
        sender='0',
        recipient=node_identifier,
        amount=1,
    )
    # add new block to chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': 'New Block forged',
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400
    # create new transaction
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])
    response = {'message': f'transaction will be added to block {index}'}

    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
