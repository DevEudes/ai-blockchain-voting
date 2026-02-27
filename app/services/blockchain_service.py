from eth_account import Account
import hashlib
import time
import uuid

def generate_wallet_address():
    """
    Generate a new Ethereum wallet address.
    Returns only the public address.
    """
    account = Account.create()
    return account.address

def record_vote_on_blockchain(voter_wallet, candidate_id, election_id):
    raw_data = f"{voter_wallet}-{candidate_id}-{election_id}-{time.time()}-{uuid.uuid4()}"
    tx_hash = hashlib.sha256(raw_data.encode()).hexdigest()
    return tx_hash