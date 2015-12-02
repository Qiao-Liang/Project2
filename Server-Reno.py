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
bChk = True

objSkt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
strIP = socket.gethostbyname(socket.gethostname())

objSkt.bind((strIP, intPort))
print("Listening at %s:%s" % (strIP, intPort))

strRecv, objAddr = objSkt.recvfrom(1024)
objFile = open(objCP.get("server", "filedest") + strRecv.split(" ")[1], 'rb')

while bChk:
  while len(arrWin) <= intWinSz:
    objFile.seek(intSEQ)   # Move the file pointer to where the SEQ number points
    strChk = objFile.read(intPktSz)

    if strChk == "":
      bChk = False
      objSkt.sendto("Completed", objAddr)
      print "End looping..."
      break
    else:
      objSkt.sendto(str(intSEQ) + ";" + strChk, objAddr)   # Assume the SEQ and data are separated with semicolon
      intSEQ += intPktSz
      arrWin.append(intSEQ)   # Stack the expected ACK numbers
  
  print arrWin
  print "The current size of window is %s" % (str(len(arrWin)))

  try:
    while bChk and len(arrWin) > 0:
      tmStart = time.time()   # Start timer

      objSkt.settimeout(fltTmOt)
      strRecv, objAddr = objSkt.recvfrom(30)

      fltSpl = time.time() - tmStart
      if fltSpl > fltTmOt:
        fltTmOt = (1 - fltAlp) * fltTmOt - fltAlp * fltSpl
        if fltTmOt < 0:
          fltTmOt = fltTmOtSt
      print "The current timeout setting is %s" % (str(fltTmOt))

      arrWin.remove(int(strRecv))
      intWinSz += 1   # Increase the window size by 1 if no packet loss detected
  except socket.timeout:
    intSEQ = arrWin[0] - intPktSz   # Reset the SEQ to where it failed, which is the smallest SEQ in the sliding window
    arrWin = []
    intWinSz = 1 # Reset the window size back to 1
    fltTmOt = fltTmOtSt   # Reset the initial value for time out
    print "timeout when receiving ACK at %s" % (str(intSEQ))
    pass