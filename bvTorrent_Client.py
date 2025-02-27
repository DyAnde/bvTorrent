from threading import *
from socket import *
from sys import argv
from pathlib import *
import hashlib

# doing something like "print(updateMask.__doc__)" will print the docstring of the function

repo: Path = Path.cwd() / "repository"

seederFiles: Path = Path.cwd() / "seederFiles"

if not repo.exists():
    print("No repository found. Creating...")
    repo.mkdir()

swarmDict: dict[str, str] = {}  # Key: File name, Value: chunk mask of that file
maxChunkSize: int = -1  # Size of each chunk, default to -1
numChunks: int = -1  # Number of chunks in the file, default to -1
hashedData: list[str] = []  # List of hashed data for each chunk, format: "chunkSize,checksum\n"
chunkMask: str = ""  # String of 0s and 1s where 1 denotes the client has the chunk and 0 denotes the client does not have the chunk

isSeeder: bool = False


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
listener.listen(5)  # 5 is the maximum number of queued connections
listenerPort = listener.getsockname()[1]  # Will use available port provided by OS


def updateMask(trackerSocket: socket, chunkMask: str):
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
def client_to_client(targetIP: str, targetPort: int, chunkID: int) -> bool:
    """
    Client requests a connection to another client
    Protocol:
        - Requesting client establishes connection with another client that has the desired chunk(s)
        - Requesting client will send single integer in an ASCII string that is new line terminated.
            - Integer represents the chunk id (0-based)
        - Client with the chunk will send back a byte array containing the number of bytes in the chunk
            - No new line termination
        - Receiving client will hash the received data to derive its checksum and confirm the derived checksum matches the checksum the tracker provided

    param targetIP: IP of the client we are connecting to
    param targetPort: Port of the client we are connecting to
    param chunkID: Index of the chunk we are requesting

    return: True if the chunk was successfully downloaded, False otherwise
    """
    global chunkMask
    global swarmDict
    try:
        peerSocket = socket(AF_INET, SOCK_STREAM)
        peerSocket.connect((targetIP, targetPort))
        peerSocket.send(f"{chunkID}\n".encode())

        chunkSize: int = int(hashedData[chunkID].split(",")[0])
        chunkData = getFullMsg(peerSocket, chunkSize)

        # Hash the chunk data
        peerCheckSum: str = hashlib.sha224(chunkData).hexdigest()

        # hashedData is the same length as the number of chunks, so their indexes match
        trackerCheckSum: str = hashedData[chunkID].split(",")[1].strip()
        temp_file = [None] * numChunks

        if trackerCheckSum == peerCheckSum:
            # Checksums match, write the chunk to the file and update the chunk mask
            print(f"Checksums match for chunk {chunkID}")

            temp_file[chunkID] = chunkData

            # check to see if ALL chunks are recieved and write them all at the same time
            if all(chunk != None for chunk in temp_file):
                with open(repo / fileName, "ab") as file:
                    for chunk in temp_file:
                        file.write(chunk)

            temp = list(chunkMask)
            temp[chunkID] = "1"
            chunkMask = "".join(temp)

            # Also update the swarmDict
            swarmDict[fileName] = chunkMask
            peerSocket.close()
            return True

        else:
            print(f"Checksums do not match for chunk {chunkID}, not writing to file")
            peerSocket.close()
            return False

    except ConnectionRefusedError:
        print(f"Connection refused from {targetIP}:{targetPort}")
        return False

    except Exception as e:
        print(f"Error fetching chunk {chunkID} from {targetIP}:{targetPort}, with exception: \n{e}")
        return False



def handleClient(clientSocket: socket, clientAddr: tuple, isSeeder: bool = False):
    # Receive the chunkID from the requester, then send that chunk OF THE FILE back
    chunkID: int = int(getLine(clientSocket))
    if not isSeeder:
        with open(repo / fileName, "rb") as file:
            file.seek(chunkID * maxChunkSize)
            chunkData = file.read(maxChunkSize)
    else:
        with open(seederFiles / fileName, "rb") as file:
            file.seek(chunkID * maxChunkSize)
            chunkData = file.read(maxChunkSize)
    clientSocket.send(chunkData)
    # clientSocket.send(chunkMask[chunkID].encode()) this was only sending a single character of the chunkMask, lol
    clientSocket.close()


def acceptIncomingConnections(isSeeder: bool = False):
    while True:
        if not isSeeder:
            Thread(target=handleClient, args=(*listener.accept(),), daemon=True).start()
        else:
            Thread(target=handleClient, args=(*listener.accept(), True), daemon=True).start()


trackerIP = input("Enter the IP of the tracker: ")
trackerPort = int(input("Enter the port of the tracker: "))

try:
    trackerSocket = socket(AF_INET, SOCK_STREAM)
    trackerSocket.connect((trackerIP, trackerPort))
except ConnectionRefusedError:
    print("Connection with tracker refused")
    exit()
fileName: str = getLine(trackerSocket).strip()
maxChunkSize = int(getLine(trackerSocket))
numChunks = int(getLine(trackerSocket))
hashedData = [getLine(trackerSocket) for _ in range(numChunks)]

# Check if we have the file in the repository, and we are not a seeder
if not (repo / fileName).exists() and len(argv) == 1:
    # We don't have the file, create it
    (repo / fileName).touch()
    # We just created the file, so we don't have any chunks
    chunkMask = "0" * numChunks
elif len(argv) == 2 and argv[1] == "-s":
    # we are a seeder, so check the seederFiles directory for the file
    isSeeder = True
    if not (seederFiles / fileName).exists():
        print("Seeder file not found")
        exit()
    # We have the file, so we have all the chunks
    chunkMask = "1" * numChunks
elif len(argv) != 1:
    print("Usage: python3 bvTorrent_Client.py")
    exit()
else:
    # We have the file, check which chunks we have
    with open(repo / fileName, "rb") as file:
        fileData = file.read()
    j = 0
    for i in range(0, len(fileData), maxChunkSize):
        sz = min(maxChunkSize, len(fileData) - i)  # last chunk may be smaller than chunkSize
        checkSum: str = hashlib.sha224(fileData[i:i + sz]).hexdigest()
        trackerCheckSum: str = hashedData[j].split(",")[1].strip()
        print(f"{len(trackerCheckSum)=} {len(checkSum)=}")
        if trackerCheckSum == checkSum:
            chunkMask += "1"
        else:
            chunkMask += "0"
        j += 1

# Send back the listening port (NOT THE PORT THE SOCKET IS CONNECTED TO) and chunk mask as a comma delimited string that is newline terminated
# 	- New client example: 12345,000000000000000000000
# 	- Seeder client example: 12345,111111111111111111111
swarmDict[fileName] = chunkMask
trackerSocket.send(f"{listenerPort},{chunkMask}\n".encode())
# Tracker now goes into a loop that listens for 3 things "UPDATE_MASK\n", "CLIENT_LIST\n", and "DISCONNECT!\n"

# Start threads to listen for incoming connections
if not isSeeder:
    Thread(target=acceptIncomingConnections, daemon=True).start()
else:
    Thread(target=acceptIncomingConnections, args=(True,), daemon=True).start()

done = False
while not done:
    try:
        cmd = input("\nWhat would you like to do?\n(GET_CHUNK, CLIENT_LIST, DISCONNECT): ").strip().upper()
    except KeyboardInterrupt:
        cmd = "DISCONNECT"
    if cmd == "CLIENT_LIST":
        clients = clientListReq(trackerSocket)
        print("Clients in swarm:")
        for client in clients:
            clientPort: int = int(client.split(":")[1].split(",")[0])  # Yes, this is ugly, but it's the only way to get the port without REGEX
            if clientPort == listenerPort:
                print(f"\t- (you) {client}")
            else:
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
                    clientPort: int = int(client.split(":")[1].split(",")[0])  # Yes, this is ugly, but it's the only way to get the port without REGEX
                    if clientPort == listenerPort:
                        print(f"\t- (you) {client}")
                    else:
                        print(f"\t- {client}")
            continue
        retVal = client_to_client(peerIP, peerPort, chunkID)
        # The only time our chunkMask should change, while connected to the tracker, is when we successfully downloaded something so we can update it here
        if retVal:
            updateMask(trackerSocket, chunkMask)
    else:
        print("Invalid command")
