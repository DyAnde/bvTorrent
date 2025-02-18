from threading import *
from socket import *
from sys import argv
from pathlib import *

# doing something like "print(updateMask.__doc__)" will print the docstring of the function

repo: Path = Path.cwd() / "repository/"

def getFullMsg(conn: socket, msgLength: int):
	msg = b""
	while len(msg) < msgLength:
		retVal = conn.recv(msgLength - len(msg))
		msg += retVal
		if len(retVal) == 0:
			break
	return msg

def getLine(conn: socket):
	msg = b""
	while True:
		ch = conn.recv(1)
		msg += ch
		if ch == b"\n" or len(ch) == 0:
			break
	return msg.decode()

# Setup listening socket
listener = socket(AF_INET, SOCK_STREAM)
listener.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
listener.bind(("", 0))
listener.listen(5) # 5 is the maximum number of queued connections
listenerPort = listener.getsockname()[1] # Will use available port provided by OS

print(f"Listening on port {listenerPort}")

def updateMask():
	"""
	Update the mask of the client
	- Client tells tracker which chunks it has downloaded
	"""
	pass

def clientListReq():
	"""Client requests an updated list of all other clients in the swarm and their chunk masks"""
	pass

def disconnect():
	"""Cleanly disconnect from the swarm"""
	pass

# in a try block:
	# recieve filename
	# recieve chunksize
	# recieve numchunks
	# for numchunks send the hashed data (chunksize)
	# send back to the tracker the port it is listening on
def newConnection(connInfo: tuple):
	"""
	New connection to the swarm.
	 - Client will recieve file and chunk info from tracker
	 - Client will tell tracker:
		- Which port it will listen on to recieve incoming connections
		- It's current chunk mask (denoting which chunks it has)
	
	param connInfo: tuple of (IP, port) of the tracker
	"""
	try:
		clientSocket = socket(AF_INET, SOCK_STREAM)
		clientSocket.connect(connInfo)
	except ConnectionRefusedError:
		print("Connection refused")
		exit()
	# Recieve file name
	fileName: str = getLine(clientSocket)
	# Recieve chunk size
	chunkSize: int = int(getLine(clientSocket))
	# Recieve number of chunks
	numChunks: int = int(getLine(clientSocket))
	# Recieve the hashed data for each chunk
	hashedData: str = ""
	for i in range(numChunks):
		hashedData += getLine(clientSocket)
	# Put hashedData into a cleaner data structure
	hashedDataList: list = hashedData.split("\n")
	# Check if we have any chunks of the file
	for file in repo.iterdir():
		# Check if we have the file
		# Send back the port (NOT THE PORT THE SOCKET IS CONNECTED TO) and chunk mask as a comma delimited string that is newline terminated
		# 	- New client example: 12345,000000000000000000000
		# 	- Seeder client example: 12345,111111111111111111111
		if file.name == fileName:
			# We have the file, so we are seeder, send back the port and chunk mask
			clientSocket.send(f"{listenerPort},{1*numChunks}\n".encode())
		else:
			# We don't have the file, send back the port and chunk mask
			clientSocket.send(f"{listenerPort},{0*numChunks}\n".encode())
	# Tracker now goes into a loop that listens for 3 things "UPDATE_MASK\n", "CLIENT_LIST\n", and "DISCONNECT!\n"
	


# ** ONE SOCKET PER CHUNK e.g. REQUEST SINGLE CHUNK, CLOSE CONNECTION, OPEN NEW CONNECTION, REQUEST SINGLE CHUNK, etc.**
def client_to_client():
	"""
	Client requests a connection to another client
	Protocol:
		- Requesting client establishes connection with another client that has the desired chunk(s)
		- Requesting client will send single integer in an ASCII string that is new line terminated.
			- Integer represents the chunk id (0-based)
		- Client with the chunk will send back a byte array containing the number of bytes in the chunk
			- No new line termination
		- Recieving client will hash the recieved data to derive its checksum and confirm the derived checksum matches the checksum matches the checksum the tracker provided
	"""
	pass

if len(argv) == 2 and argv[1] == "-s":
	# This is a seeder client
	# - Seeder will only need to connect to the tracker and take connections from other clients
	# seeder files are stored in "seederFiles" directory
	newConnection()	
elif len(argv) != 1:
	print("Usage: python3 bvTorrent_Client.py")
	exit()
