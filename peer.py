# TCP Stage 4

from socket import *
import threading
import os, shutil

def clearFolders(fileName):
    if os.path.isdir(fileName):
        shutil.rmtree(fileName)
    os.mkdir(fileName)

chunkSize = 1024

# ==========

# python .\peer.py

peer1IP = 'localhost'
peer2IP = 'localhost'
peer3IP = 'localhost'
peer4IP = 'localhost'

print('Choose a peer number: 1, 2, 3, 4')
choice = input()

def peerSelection(choice):
    if (choice == '1'):
        downloadName = peer4IP
        downloadPort = 12004
        uploadName = peer1IP
        uploadPort = 12001
    elif (choice == '2'):
        downloadName = peer1IP
        downloadPort = 12001
        uploadName = peer2IP
        uploadPort = 12002
    elif (choice == '3'):
        downloadName = peer2IP
        downloadPort = 12002
        uploadName = peer3IP
        uploadPort = 12003
    elif (choice == '4'):
        downloadName = peer3IP
        downloadPort = 12003
        uploadName = peer4IP
        uploadPort = 12004
    return [downloadName, downloadPort, uploadName, uploadPort]

peerNumber = 'Peer' + choice
clearFolders(peerNumber)
print(peerNumber)
peerData = peerSelection(choice)
downloadName = peerData[0]
downloadPort = peerData[1]
uploadName = peerData[2]
uploadPort = peerData[3]

# ==========

# Create TCP Socket
trackerName = 'localhost'
trackerPort = 12000
peerSocket = socket(AF_INET, SOCK_STREAM)
peerSocket.connect((trackerName, trackerPort))

# Peer sends 'ready'
peerSocket.send('ready'.encode())
print('1. Peer sends: ready')
# Peer receives 'ready'
readyMessage = peerSocket.recv(1024).decode()
print('4. Tracker receives: ' + readyMessage)

# Peer sends 'file name'
peerSocket.send('file name'.encode())
print('5. Peer sends: file name')
# Peer receives 'fileName'
fileName = peerSocket.recv(1024).decode()
print('8. Peer receives: ' + fileName)

# Peer sends '# of chunks'
peerSocket.send('# of chunks'.encode())
print('9. Peer sends: # of chunks')
# Peer receives 'totalNumberOfChunks'
totalNumberOfChunks = peerSocket.recv(1024).decode()
print('12. Peer receives: totalNumberOfChunks')

# ===

peerSocket.send('last chunk size'.encode())
lastChunkSize = peerSocket.recv(1024).decode()
print(lastChunkSize)

# ===

# Peer sends 'chunk id list'
peerSocket.send('chunk id list'.encode())
print('13. Peer sends: chunk id list')
# Peer receives 'chunkIDList'
chunkIDList = peerSocket.recv(1024).decode().split()
print('16. Peer receives: chunkIDList')

# Peer sends 'ready to download'
peerSocket.send('ready to download'.encode())
print('17. Peer sends: ready to download')

# Loop through number of chunks
for i in chunkIDList:

    # ===

    # Peer receives 'currentChunk'
    if (i == int(totalNumberOfChunks) - 1):
        currentChunk = peerSocket.recv(lastChunkSize, MSG_WAITALL)
    else:
        currentChunk = peerSocket.recv(chunkSize, MSG_WAITALL)

    # ===

    # Peer saves 'currentChunk'
    with open(peerNumber + '/chunk' + str(i), 'wb') as file:
        file.write(currentChunk)
        file.close()
    # Peer sends 'next'
    peerSocket.send('next'.encode())
print('20. Peer receives: chunks')

# Peer sends 'close'
peerSocket.send('close'.encode())
print('21. Peer sends: close')
# Peer closes connection
peerSocket.close()

# ==========

# Download (Client-Like)
def download():
    
    # Create TCP socket
    downloadSocket = socket(AF_INET, SOCK_STREAM)
    while True:
        try:
            downloadSocket.connect((downloadName, downloadPort))
        except:
            print('Upload neighbor not open.')
        else:
            break
    
    # Loop forever
    while True:
        # Download sends 'ready'
        downloadSocket.send('ready'.encode())
        print('1. Download sends: ready')
        # Download receives 'ready'
        readyMessage = downloadSocket.recv(1024).decode()
        print('4. Download receives: ' + readyMessage)

        # Download sends 'chunk id list'
        downloadSocket.send('chunk id list'.encode())
        print('5. Download sends: chunk id list')
        # Dowbnload receives 'peerChunkIDList
        peerChunkIDList = downloadSocket.recv(1024).decode().split()
        print('8. Download receives: peerChunkIDList')

        # Loop through peer chunks
        for chunkID in peerChunkIDList:
            # Check if we don't already have that chunk
            if chunkID not in chunkIDList:
                # Download sends 'chunkID'
                downloadSocket.send(chunkID.encode())
                print(peerNumber + ' sends: ' + chunkID)

                # ===

                # Download receives 'chunkBytes'
                if (chunkID == int(totalNumberOfChunks) - 1):
                    chunkBytes = downloadSocket.recv(lastChunkSize, MSG_WAITALL)
                else:
                    chunkBytes = downloadSocket.recv(chunkSize, MSG_WAITALL)

                # ===

                print(peerNumber + ' receives: ' + chunkID + ' chunkBytes')
                # Write chunk to file
                with open(peerNumber + '/chunk' + chunkID, 'wb') as file:
                    file.write(chunkBytes)
                    file.close()
                # Add chunkID to the chunkIDList
                chunkIDList.append(chunkID)
                print(str(len(chunkIDList)) + ' / ' + str(totalNumberOfChunks))

        # Send 'done' to indicate the end of this cycle
        downloadSocket.send('done'.encode())

        # When all chunks are downloaded, combine them and break
        if (len(chunkIDList) == int(totalNumberOfChunks)):    
            # # Peer combines chunks
            with open(peerNumber + '/' + peerNumber + '_' + fileName, 'ab') as file:
                for i in range(int(totalNumberOfChunks)):
                    chunkBytes = open(peerNumber + '/chunk' + str(i), 'rb').read()
                    file.write(chunkBytes)
            file.close()
            break

# ==========

# Upload (Server-Like)
def upload():
    
    # Create TCP Socket
    uploadSocket = socket(AF_INET, SOCK_STREAM)
    uploadSocket.bind(('', uploadPort))

    # Upload begins listening for incoming TCP requests
    uploadSocket.listen(1)
    print('Upload is ready to receive')

    # Upload waits on accept() for incoming requests, new socket created on return
    connectionSocket, addr = uploadSocket.accept()

    # Loop forever
    while True:

        # Upload receives 'ready'
        try:
            readyMessage = connectionSocket.recv(1024).decode()
        except:
            print('Connection was aborted.')
            break

        print('2. Upload receives: ' + readyMessage)
        # Upload sends 'ready'
        connectionSocket.send(readyMessage.encode())
        print('3. Upload sends: ' + readyMessage)

        # Upload receives 'chunk id list'
        chunkListQuery = connectionSocket.recv(1024).decode()
        print('6. Upload receives: ' + chunkListQuery)
        # Upload sends 'peerChunkIDList'
        connectionSocket.send(' '.join(chunkIDList).encode())
        print('7. Upload sends: peerChunkIDList')

        # Wait for requests from download peer
        while True:
            # Upload receives 'request'
            try:
                request = connectionSocket.recv(1024).decode()
            except:
                print('Connection was aborted.')
                break
            print(peerNumber + ' receives: ' + request)
            if (request == 'done'):
                break
            else:
                # Load corresponding chunk
                chunkBytes = open(peerNumber + '/chunk' + str(request), 'rb').read()
                print(len(chunkBytes))
                # Upload sends 'chunkBytes'
                connectionSocket.send(chunkBytes)
                print(peerNumber + ' sends: ' + request + ' chunkBytes')

# ==========

# Create one thread for upload
uPeer = threading.Thread(target = upload, name = 'uPeer')
uPeer.start()

# Create one thread for download
dPeer = threading.Thread(target = download, name = 'dPeer')
dPeer.start()
