from threading import *
from socket import *
from sys import argv, byteorder
from pathlib import *
import hashlib

# doing something like "print(updateMask.__doc__)" will print the docstring of the function

repo: Path = Path.cwd() / "repository"

seederFiles: Path = Path.cwd() / "seederFiles"
# This is where we will store the files we are seeding

if not repo.exists():
	print("No repository found. Creating...")
	repo.mkdir()

swarmDict: dict[str, str] = {} # Key: File name, Value: chunk mask of that file
chunkSize: int = -1 # Size of each chunk, default to -1
numChunks: int = -1 # Number of chunks in the file, default to -1
hashedData: list[str] = [] # List of hashed data for each chunk, format: "chunkSize,checksum\n"

if len(argv) == 2 and argv[1] == "-s":
	# Seeder
	chunkMask: str = "1" * numChunks
elif len(argv) != 1:
	print("Usage: python3 bvTorrent_Client.py")
	exit()
else:
	# Normal client
	chunkMask: str = "0" * numChunks

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

def updateMask(trackerSocket: socket, chunkMask):
	"""
	Update the mask of the client
	- Client tells tracker which chunks it has downloaded

	param trackerSocket: socket object connected to the tracker
	param chunkMask: string of 0s and 1s where 1 denotes the client has the chunk and 0 denotes the client does not have the chunk
	"""
	trackerSocket.send("UPDATE_MASK\n".encode())
	trackerSocket.send(f"{chunkMask}\n".encode())

def clientListReq(trackerSocket: socket):
	"""
	Client requests an updated list of all other clients in the swarm and their chunk masks
	
	param trackerSocket: socket object connected to the tracker
	"""
	trackerSocket.send("CLIENT_LIST\n".encode())
	numClients: int = int(getLine(trackerSocket))
	clients: list[str] = [getLine(trackerSocket) for _ in range(numClients)]
	return clients

def disconnect(trackerSocket: socket):
	"""
	Cleanly disconnect from the swarm
	
	param trackerSocket: socket object connected to the tracker
	"""
	trackerSocket.send("DISCONNECT!\n".encode())
	trackerSocket.close()

# ** ONE SOCKET PER CHUNK e.g. REQUEST SINGLE CHUNK, CLOSE CONNECTION, OPEN NEW CONNECTION, REQUEST SINGLE CHUNK, etc.**
def client_to_client(targetIP: str, targetPort: int, chunkID: int):
	"""
	Client requests a connection to another client
	Protocol:
		- Requesting client establishes connection with another client that has the desired chunk(s)
		- Requesting client will send single integer in an ASCII string that is new line terminated.
			- Integer represents the chunk id (0-based)
		- Client with the chunk will send back a byte array containing the number of bytes in the chunk
			- No new line termination
		- Recieving client will hash the recieved data to derive its checksum and confirm the derived checksum matches the checksum the tracker provided
	
	param targetIP: IP of the client we are connecting to
	param targetPort: Port of the client we are connecting to
	param chunkID: Index of the chunk we are requesting
	"""
	try:
		peerSocket = socket(AF_INET, SOCK_STREAM)
		peerSocket.connect((targetIP, targetPort))
		peerSocket.send(f"{chunkID}\n".encode())
		chunkData = getFullMsg(peerSocket, chunkSize)
		# Hash the chunk data
		# Going off the assumption that the hashedData is the same length as the number of chunks, so their indexes match
		trackerCheckSum: int = int.from_bytes(hashlib.sha224(hashedData[chunkID].split(",")[1]).digest(), byteorder, signed=True)
		peerCheckSum: int = int.from_bytes(hashlib.sha224(chunkData).digest(), byteorder, signed=True)
		if trackerCheckSum == peerCheckSum:
			# checksums match, write the chunk to the file and update the chunk mask
			print(f"checksums match for chunk {chunkID}")
			with open(repo / fileName, "wb") as file:
				file.write(chunkData)
			chunkMask[chunkID] = "1"
		else:
			print(f"Checksums do not match for chunk {chunkID}, not writing to file")
			peerSocket.close()
	except ConnectionRefusedError:
		print(f"Connection refused from {targetIP}:{targetPort}")
		return
	except Exception as e:
		print(f"Error fetching chunk {chunkID} from {targetIP}:{targetPort}, with exception: {e}")
		return

def handleClient(clientSocket: socket, clientAddr: tuple):
	print(f"Connection from {clientAddr}")

	# Receive the chunkID from the requester, then send that chunk back
	chunkID: int = int(getLine(clientSocket))
	clientSocket.send(chunkMask[chunkID].encode())
	clientSocket.close()

def acceptIncomingConnections():
	while True:
		Thread(target=handleClient, args=(*listener.accept(),), daemon=True).start()

trackerIP = input("Enter the IP of the tracker: ")
trackerPort = int(input("Enter the port of the tracker: "))

try:
	trackerSocket = socket(AF_INET, SOCK_STREAM)
	trackerSocket.connect((trackerIP, trackerPort))
except ConnectionRefusedError:
	print("Connection with tracker refused")
	exit()
fileName: str = getLine(trackerSocket)
chunkSize = int(getLine(trackerSocket))
numChunks = int(getLine(trackerSocket))
hashedData = [getLine(trackerSocket) for _ in range(numChunks)]
# Check if we have any chunks of the file
for file in repo.iterdir():
	# Check if we have the file
	# Send back the listening port (NOT THE PORT THE SOCKET IS CONNECTED TO) and chunk mask as a comma delimited string that is newline terminated
	# 	- New client example: 12345,000000000000000000000
	# 	- Seeder client example: 12345,111111111111111111111
	if file.name == fileName:
		# We have the file, so we are seeder, send back the port and chunk mask
		swarmDict[fileName] = chunkMask
		trackerSocket.send(f"{listenerPort},{chunkMask}\n".encode())
	else:
		# We don't have the file, send back the port and chunk mask
		swarmDict[fileName] = chunkMask
		trackerSocket.send(f"{listenerPort},{chunkMask}\n".encode())
# Tracker now goes into a loop that listens for 3 things "UPDATE_MASK\n", "CLIENT_LIST\n", and "DISCONNECT!\n"

# Start threads to listen for incoming connections
Thread(target=acceptIncomingConnections, daemon=True).start()

done = False
while not done:
	cmd = input("What would you like to do?\n(GET_CHUNK, CLIENT_LIST, DISCONNECT): ").strip().upper()
	if cmd == "CLIENT_LIST":
		clients = clientListReq(trackerSocket)
		print("Clients in swarm:")
		for client in clients:
			print(f"\t- {client}")
	elif cmd == "DISCONNECT":
		disconnect(trackerSocket)
		done = True
	elif cmd == "GET_CHUNK":
		# Get a chunk from another client, using the 'client_to_client' function
		# Ask user to input the IP and port of the client they want to connect to
		try:
			peerIP = input("Enter the IP of the client you want to connect to: ")
			peerPort = int(input("Enter the port of the client you want to connect to: "))
			chunkID = int(input("Enter the chunk ID you want to download: "))
		except KeyboardInterrupt:
			helpMe = input("Do you know of any other users in the swarm? (y/n): ").strip().lower()
			if helpMe == "n":
				clients = clientListReq(trackerSocket)
				print("Clients in swarm:")
				for client in clients:
					print(f"\t- {client}")
			continue
		client_to_client(peerIP, peerPort, chunkID)
		# The only time our chunkMask should change is when we download something so we can update it here
		updateMask(trackerSocket, chunkMask)
	else:
		print("Invalid command")
	# Nice extra spacing for readability
	print()