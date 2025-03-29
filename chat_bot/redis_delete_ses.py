import redis
import msgpack
import pickle

# Connect to Redis server
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def delete_session(session_key):
    
    
    if r.exists(session_key):
        r.delete(session_key)
        print(f"Session '{session_key}' deleted successfully.")
    else:
        print(f"Session '{session_key}' does not exist.")

import redis

# Connect to Redis server
r = redis.Redis(host='localhost', port=6379, db=0)

# Function to decode bytes safely
def safe_decode(byte_data):
    try:
        return byte_data.decode('utf-8')
    except UnicodeDecodeError:
        return byte_data  # Return raw bytes if decoding fails

def extract_session_id(session_key):
    # Get the value of the session key
    value = r.get(session_key)
    
    if value:
        try:
            # First try to decode using msgpack
            unpacked_data = msgpack.unpackb(value, raw=False)
        except Exception as e:
            print(f"msgpack decoding failed: {e}")
            try:
                # If msgpack fails, try to decode using pickle
                unpacked_data = pickle.loads(value)
            except Exception as e:
                print(f"pickle decoding failed: {e}")
                unpacked_data = None
        
        if unpacked_data:
            print(f"Unpacked Data: {unpacked_data}")
            # Extract the session_id
            session_id = unpacked_data.get('session_id', None)
            return session_id
        else:
            print("Failed to unpack the session data.")
            return None
    else:
        print(f"No value found for key: {session_key}")
        return None
    
def view_all_sessions():
    # Get all session keys
    session_keys = r.keys('session:*')
    
    for key in session_keys:
        key = safe_decode(key)  # Safely decode the key
        key_type = r.type(key).decode('utf-8')  # Get the type of the key

        if key_type == 'string':
            value = r.get(key)
            value = safe_decode(value)  # Safely decode the value
            print(f"Key: {key} - Type: String - Value: {value}\n")
        elif key_type == 'list':
            value = r.lrange(key, 0, -1)  # Get all elements in the list
            print(f"Key: {key} - Type: List - Value: {[safe_decode(v) for v in value]}")
        elif key_type == 'set':
            value = r.smembers(key)  # Get all members of the set
            print(f"Key: {key} - Type: Set - Value: {[safe_decode(v) for v in value]}")
        elif key_type == 'hash':
            value = r.hgetall(key)  # Get all fields and values in the hash
            print(f"Key: {key} - Type: Hash - Value: { {k.decode('utf-8'): safe_decode(v) for k, v in value.items()} }")
        elif key_type == 'zset':
            value = r.zrange(key, 0, -1, withscores=True)  # Get all members of the sorted set with scores
            print(f"Key: {key} - Type: ZSet - Value: {[(safe_decode(v), score) for v, score in value]}")
        else:
            print(f"Key: {key} - Type: {key_type} - Value: Not supported")


if __name__ == "__main__":

    for key in r.scan_iter():

        decoded_key = key.decode('utf-8')
        print(decoded_key)
        delete_session(decoded_key)
        print()

