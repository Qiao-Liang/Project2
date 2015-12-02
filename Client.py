import socket
import time
import sys
import ConfigParser

dicBuf = {}
intSEQ = 0
strBit = ""
strFile = ""

objCP = ConfigParser.ConfigParser()
objCP.read("Client.cfg")
strSrvIP = objCP.get("server", "IP")
intSrvPort = objCP.getint("server", "port")
intPktSz = objCP.getint("client", "pktsize")
intBufSz = objCP.getint("client", "bufsize")

objSkt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

tmElp = time.time()
objSkt.sendto("GET " + objCP.get("client","file"), (strSrvIP, intSrvPort))

while True:
	strResp = objSkt.recv(1040)
	if strResp == "Completed":
		print "End looping..."
		break
	else:
		intElm = strResp.index(";")   # There can be many semicolon in the response, but only the first one is the eliminator
		strBit = strResp[intElm + 1:]

		intLen = len(strBit)
		intSEQ = int(strResp[:intElm])

		print "The lenght of bit received in SEQ %s is %s" % (str(intSEQ), str(intLen))

		dicBuf[intSEQ] = strBit   # Store the packet in buffer, duplicated SEQ is automatically taken care of since the keys in dictionary are unique

		intACK = intSEQ + intLen
		objSkt.sendto(str(intACK), (strSrvIP, intSrvPort))
		print "Sent the ACK %s" % (str(intACK))

objFile = open(objCP.get("client", "filedest") + objCP.get("client","file"), 'w')

lstKey = dicBuf.keys()
print "The number of chunks is %s" % (str(len(dicBuf)))

lstKey.sort()
for strKey in lstKey:
	objFile.write(dicBuf[strKey])

objFile.close()

print time.time() - tmElp