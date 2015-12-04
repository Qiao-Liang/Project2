import socket
import sys
import os
import time
import ConfigParser

objCP = ConfigParser.ConfigParser()
objCP.read("Server.cfg")
intSEQ = 0
strChk = ""   # For file chunks
intPort = objCP.getint("server", "port")
intPktSz = objCP.getint("server", "pktsize")
intWinSz = objCP.getint("server", "winsize")
intTmOt = objCP.getint("server", "timeout")
arrWin = []
dicDly = {}
bChk = True   # Indicates if file chunk is empty

objSkt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
strIP = socket.gethostbyname(socket.gethostname())

objSkt.bind((strIP, intPort))
print("Listening at %s:%s" % (strIP, intPort))

strRecv, objAddr = objSkt.recvfrom(1024)
objFile = open(objCP.get("server", "filepath") + strRecv.split(" ")[1], 'rb')
objSkt.settimeout(intTmOt)

# Send the packets and receive ACKs
while bChk:
	while len(arrWin) < intWinSz:
		try:
			objFile.seek(intSEQ)   # Move the file pointer to where the SEQ number points
			strChk = objFile.read(intPktSz)

			if strChk == "":
				bChk = False
				objSkt.sendto("Completed", objAddr)
				break
			else:
				objSkt.sendto(str(intSEQ) + ";" + strChk, objAddr)   # Assume the SEQ and data are separated with semicolon
				intSEQ += intPktSz
				arrWin.append(intSEQ)   # Stack the expected ACK numbers
		except socket.timeout:
			print "Timeout when sending data at SEQ %s" % (str(intSEQ))
			pass

	try:
		tmSrt = time.time()
		while bChk and len(arrWin) > 0:
			strRecv, objAddr = objSkt.recvfrom(30)
			dicDly[int(strRecv)] = str(time.time() - tmSrt)   # Record the delay of this packet
			arrWin.remove(int(strRecv))
	except socket.timeout:
		print "timeout when receiving ACK at %s" % (str(intSEQ))
		intSEQ = arrWin[0] - intPktSz   # Reset the SEQ to where it failed, which is the smallest SEQ in the sliding window
		arrWin = []   # Clear the window
		pass
	  
print "File completely sent"

# Write the delay log file
objLog = open(objCP.get("server", "logpath") + objCP.get("server","log"), 'w')

lstKey = dicDly.keys()
lstKey.sort()
for strKey in lstKey:
	objLog.write("%s,%s\n" % (strKey, dicDly[strKey]))

objLog.close()
print "The delay log for each of the packets is created"