import socket
import sys
import os
import time
import ConfigParser
 
objCP = ConfigParser.ConfigParser()
objCP.read("Server.cfg")
intSEQ = 0
strChk = ""
intPort = objCP.getint("server", "port")
intPktSz = objCP.getint("server", "pktsize")
intWinSz = 1   # Set the initial window size to 1
fltTmOt = float(objCP.getint("server", "timeout"))   # Set the initial value for time out
fltAlp = float(objCP.get("server", "alpha"))
arrWin = []
bCnt = True

objSkt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
strIP = socket.gethostbyname(socket.gethostname())

objSkt.bind((strIP, intPort))
print("Listening at %s:%s" % (strIP, intPort))

strRecv, objAddr = objSkt.recvfrom(1024)
objFile = open(objCP.get("server", "filedest") + strRecv.split(" ")[1], 'rb')

while bCnt:
  while len(arrWin) <= intWinSz:
    objFile.seek(intSEQ)   # Move the file pointer to where the SEQ number points
    strChk = objFile.read(intPktSz)

    if strChk == "":
      bCnt = False
      objSkt.sendto("Completed", objAddr)
    else:
      objSkt.sendto(str(intSEQ) + ";" + strChk, objAddr)   # Assume the SEQ and data are separated with semicolon
      intSEQ += intPktSz
      arrWin.append(intSEQ)   # Stack the expected ACK numbers

  tmStart = time.time()   # Start timer
  while bCnt and len(arrWin) > 0:
  	tmSpl = time.time() - tmStart
  	if tmSpl < intTmOt:
	  	fltTmOt = (1 - fltAlp) * fltTmOt - fltAlp * tmSpl
	    strRecv, objAddr = objSkt.recvfrom(30)
	    arrWin.remove(int(strRecv))

  if len(arrWin) > 0:   # In case some ACK is not received till timeout
    intSEQ = arrWin[0] - intPktSz   # Reset the SEQ to where it failed, which is the smallest SEQ in the sliding window
    intWinSz = 1
  else:
  	intWinSz += 1