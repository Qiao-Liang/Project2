import socket
import time
import sys
import ConfigParser
import threading

# Define the method to log throughput in a repeatitive manner
# It's invoked by a child thread
def LogThroughput():
	while True:
		arrLog.append(len(dicBuf) * intPktSz)   # Log the bits already in the buffer
		time.sleep(intItvl)   # Execute every x seconds as per the setting in Client.cfg

dicBuf = {}
arrLog = []
intLogTm = 0
intSEQ = 0
strBit = ""
strFile = ""

objCP = ConfigParser.ConfigParser()
objCP.read("Client.cfg")
strSrvIP = objCP.get("server", "IP")
intSrvPort = objCP.getint("server", "port")
intPktSz = objCP.getint("client", "pktsize")
intBufSz = objCP.getint("client", "bufsize")
intItvl = objCP.getint("client", "loginterval")

objSkt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

tmStart = time.time()   # Log the transimission start time
objSkt.sendto("GET " + objCP.get("client","file"), (strSrvIP, intSrvPort))

# Start another process to register the number of packets received per time interval
objThd = threading.Thread(target=LogThroughput)
objThd.setDaemon(True)
objThd.start()

while True:
	strResp = objSkt.recv(1040)
	if strResp == "Completed":
		break
	else:
		intElm = strResp.index(";")   # There can be many semicolon in the response, but only the first one is the eliminator
		strBit = strResp[intElm + 1:]

		intLen = len(strBit)
		intSEQ = int(strResp[:intElm])

		dicBuf[intSEQ] = strBit   # Store the packet in buffer, duplicated SEQ is automatically taken care of since the keys in dictionary are unique

		intACK = intSEQ + intLen
		objSkt.sendto(str(intACK), (strSrvIP, intSrvPort))
		print "Sent the ACK %s" % (str(intACK))

tmEnd = time.time()   # Log the transimission end time
print "Total transmission time is %s" % (str(tmEnd - tmStart))

objFile = open(objCP.get("client", "filedest") + objCP.get("client","file"), 'w')

lstKey = dicBuf.keys()
print "The number of packets is %s" % (str(len(dicBuf)))

lstKey.sort()
for strKey in lstKey:
	objFile.write(dicBuf[strKey])

objFile.close()
print "File transmission completed"

# Write the delay log file
objLog = open(objCP.get("client", "logdest") + objCP.get("client","log"), 'w')

for intIdx in range(len(arrLog)):
	objLog.write("%s\n" % (arrLog[intIdx]))

objLog.close()
print "The throughput log for every %s second(s) is created" % str(intItvl)