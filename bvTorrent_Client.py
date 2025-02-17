from threading import *
from socket import *
from sys import argv
from pathlib import *

# doing something like "print(updateMask.__doc__)" will print the docstring of the function

# in a try block:
	# recieve filename
	# recieve chunksize
	# recieve numchunks
	# for numchunks send the hashed data (chunksize)
	# send back to the tracker the port it is listening on
def newConnection():
	"""
	New connection to the swarm.
	 - Client will recieve file and chunk info from tracker
	 - Client will tell tracker:
		- Which port it will listen on to recieve incoming connections
		- It's current chunk mask (denoting which chunks it has)
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


def updateMask():
	"""
	Update the mask of the client
	- Client tells tracker which chunks it has downloaded
	"""
	pass


def clientListReq():
	"""Client requests an updated list of all other clients in the swarm and their chunk masks"""
	pass


def getClientlist():
	pass


def Disconnect():
	"""Cleanly disconnect from the swarm"""
	pass


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
