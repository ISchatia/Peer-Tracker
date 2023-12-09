# TCP Stage 4

from socket import *
import threading
import os, shutil
import random

if os.path.isdir('Tracker'):
    shutil.rmtree('Tracker')
os.mkdir('Tracker')

# ==========

# Tracker opens file as bytes
fileName = 'new-data.txt'
# fileName = 'wireshark-traces-8.zip'
# fileName = 'Research_Talk_CS124.pptx'
# fileName = 'powerpoint.zip'
fileBytes = open(fileName, 'rb').read()

# Determine number of chunks and randomize their order

# chunkSize = 10000
chunkSize = 1024

totalNumberOfChunks = len(fileBytes) // chunkSize + 1
chunkIndices = list(range(totalNumberOfChunks))
random.shuffle(chunkIndices)

lastChunkSize = 0

# Download chunks as files
for i in range(len(chunkIndices)):
    # Get current chunk
    if (i == totalNumberOfChunks - 1):
        currentChunk = fileBytes[i * chunkSize:]
        lastChunkSize = len(currentChunk)
    else:
        currentChunk = fileBytes[i * chunkSize:(i+1) * chunkSize]
        # print(len(currentChunk))
    # Save current chunk
    with open('Tracker/chunk' + str(i), 'wb') as file:
        file.write(currentChunk)
        file.close()

# print(lastChunkSize)

# ==========

# Create TCP socket
trackerPort = 12000
trackerSocket = socket(AF_INET, SOCK_STREAM)
trackerSocket.bind(('', trackerPort))

# Tracker begins listening for incoming TCP requests
trackerSocket.listen(1)
print('The tracker is ready to receive.')

# Send a connecting peer its starting chunks
def sendPeerData(connectionSocket, numberOfPeers, peerCount):

    # Tracker receives 'ready'
    readyMessage = connectionSocket.recv(1024).decode()
    print('2. Tracker receives: ' + readyMessage)
    # Tracker sends 'ready'
    connectionSocket.send(readyMessage.encode())
    print('3. Tracker sends: ' + readyMessage)

    # Tracker receives 'file name'
    fileNameRequest = connectionSocket.recv(1024).decode()
    print('6. Tracker receives: ' + fileNameRequest)
    # Tracker sends 'fileName'
    connectionSocket.send(fileName.encode())
    print('7. Tracker sends: fileName')

    # Tracker receives '# of chunks'
    chunkCountQuery = connectionSocket.recv(1024).decode()
    print('10. Tracker receives: ' + chunkCountQuery)
    # Tracker sends 'totalNumberOfChunks'
    connectionSocket.send(str(totalNumberOfChunks).encode())
    print('11. Tracker sends: totalNumberOfChunks')

    # ===

    connectionSocket.recv(1024).decode()
    connectionSocket.send(str(lastChunkSize).encode())

    # ===

    # Tracker receives 'chunk id list'
    chunkListQuery = connectionSocket.recv(10000).decode()
    print('14. Tracker receives: ' + chunkListQuery)
    # Tracker selects the peers ID list
    idListSize = totalNumberOfChunks // numberOfPeers
    if (peerCount == numberOfPeers - 1):
        chunkIDList = chunkIndices[peerCount * idListSize:]
    else:
        chunkIDList = chunkIndices[peerCount * idListSize:(peerCount+1) * idListSize]
    chunkIDListString = ' '.join([str(i) for i in chunkIDList])
    # Tracker sends 'chunkIDList'
    connectionSocket.send(chunkIDListString.encode())
    print('15. Tracker sends: chunkIDList')

    # Tracker receives 'ready to download'
    downloadRequest = connectionSocket.recv(1024).decode()
    print('18. Tracker receives: ' + downloadRequest)

    # Loop through the peers chunks
    for i in chunkIDList:
        # Tracker sends 'currentChunk'
        if (i == totalNumberOfChunks - 1):
            connectionSocket.send(fileBytes[i * chunkSize:])
        else:
            connectionSocket.send(fileBytes[i * chunkSize:(i+1) * chunkSize])
        # Tracker receives 'next'
        connectionSocket.recv(1024).decode()
    print('19. Tracker sends: chunks')

    # Tracker receives 'close'
    closeMessage = connectionSocket.recv(1024).decode()
    print('22. Tracker receives: ' + closeMessage)
    # Tracker closes connection
    connectionSocket.close()

# ==========

# Number of total peers and current peers connected
numberOfPeers = 4
peerCount = 0
# Loop until all peers have their chunks
while True:
    if (peerCount != numberOfPeers):
        # Tracker waits on accept() for incoming requests, new socket created on return
        connectionSocket, addr = trackerSocket.accept()
        # Create new thread
        peerThread = threading.Thread(target = sendPeerData, args = (connectionSocket, numberOfPeers, peerCount))
        peerThread.start()
        peerCount += 1
    else:
        break
