from threading import *
from socket import *

# New connection to the swarm.
# - Client will recieve file and chunk info from tracker
# - Client will tell tracker:
# 	- Which port it will listen on to recieve incoming connections
# 	- It's current chunk mask (denoting which chunks it has)
def new_connection():
	pass

# Update the mask of the client
# - Client tells tracker which chunks it has downloaded
def update_mask():
	pass

# Client requests an updated list of all other clients in the swarm and their chunk masks
def request_client_list():
	pass

# Client requests a connection to another client
# ** ONE SOCKET PER CHUNK **
# Protocol:
# 	- Requesting client establishes connection with another client that has the desired chunk(s)
# 	- Requesting client will send single integer in an ASCII string that is new line terminated.
# 		- Integer represents the chunk id (0-based)
# 	- Client with the chunk will send back a byte array containing the number of bytes in the chunk
# 		- No new line termination
# 	- Recieving client will hash the recieved data to derive its checksum and confirm the derived checksum matches the checksum matches the checksum the tracker provided
def client_to_client():
	pass

