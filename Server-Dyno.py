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
fltTmOtSt = float(objCP.getint("server", "timeout"))   # Get the default time out
fltTmOt = fltTmOtSt   # Set the initial value for time out
fltAlp = float(objCP.get("server", "alpha"))
arrWin = []
dicDly = {}
bChk = True

objSkt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
strIP = socket.gethostbyname(socket.gethostname())

objSkt.bind((strIP, intPort))
print("Listening at %s:%s" % (strIP, intPort))

strRecv, objAddr = objSkt.recvfrom(1024)
objFile = open(objCP.get("server", "filepath") + strRecv.split(" ")[1], 'rb')

while bChk:
  while len(arrWin) <= intWinSz:
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
  
  print "The current window size is %s" % (str(len(arrWin)))
  print arrWin

  tmSrt = time.time()  # Start timer
  objSkt.settimeout(fltTmOt)
  try:
    tmPkt = time.time()
    while bChk and len(arrWin) > 0: 
      strRecv, objAddr = objSkt.recvfrom(30)
      dicDly[int(strRecv)] = str(time.time() - tmPkt)   # Record the delay of this packet
      print strRecv
      arrWin.remove(int(strRecv))
      intWinSz += 1   # Increase the window size by 1 if no packet loss detected
  except socket.timeout:
    print "timeout when receiving ACK at %s" % (str(intSEQ))
    intSEQ = arrWin[0] - intPktSz   # Reset the SEQ to where it failed, which is the smallest SEQ in the sliding window
    arrWin = []
    intWinSz = 1 # Reset the window size back to 1
    fltTmOt = fltTmOtSt   # Reset the initial value for time out
    pass

  fltSpl = time.time() - tmSrt
  fltTmOt = (1 - fltAlp) * fltTmOt + fltAlp * fltSpl
  print "The current timeout setting is %s" % (str(fltTmOt))

print "File completely sent"

# Write the delay log file
objLog = open(objCP.get("server", "filepath") + objCP.get("server","log"), 'w')

lstKey = dicDly.keys()
lstKey.sort()
for strKey in lstKey:
  objLog.write("%s,%s\n" % (strKey, dicDly[strKey]))

objLog.close()
print "The delay log for each of the packets is created"