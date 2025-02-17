from threading import *
from socket import *
from sys import argv
from pathlib import *

# New connection to the swarm.
# - Client will recieve file and chunk info from tracker
# - Client will tell tracker:
# 	- Which port it will listen on to recieve incoming connections
# 	- It's current chunk mask (denoting which chunks it has)
def newConnection():
# in a try block:
	# recieve filename
	# recieve chunksize
	# recieve numchunks
	# for numchunks send the hashed data (chunksize)
	# send back to the tracker the port it is listening on
	pass


if len(argv) == 2 and argv[1] == "-s":
	# This is a seeder client
	# - Seeder will only need to connect to the tracker and take connections from other clients
	# seeder files are stored in "seederFiles" directory
	newConnection()	
elif len(argv) != 1:
	print("Usage: python3 bvTorrent_Client.py")
	exit()


# Update the mask of the client
# - Client tells tracker which chunks it has downloaded
def updateMask():
	pass

# Client requests an updated list of all other clients in the swarm and their chunk masks
def clientListReq():
	pass

def getClientlist():
	pass

# Cleanly disconnect from the swarm
def Disconnect():
	pass


# Client requests a connection to another client
# ** ONE SOCKET PER CHUNK e.g. REQUEST SINGLE CHUNK, CLOSE CONNECTION, OPEN NEW CONNECTION, REQUEST SINGLE CHUNK, etc.**
# Protocol:
# 	- Requesting client establishes connection with another client that has the desired chunk(s)
# 	- Requesting client will send single integer in an ASCII string that is new line terminated.
# 		- Integer represents the chunk id (0-based)
# 	- Client with the chunk will send back a byte array containing the number of bytes in the chunk
# 		- No new line termination
# 	- Recieving client will hash the recieved data to derive its checksum and confirm the derived checksum matches the checksum matches the checksum the tracker provided
def client_to_client():
	pass

