import socket
import sys
import os
import time
import math
import ConfigParser
 
objCP = ConfigParser.ConfigParser()
objCP.read("Server.cfg")
intSEQ = 0
strChk = ""
intPort = objCP.getint("server", "port")
intPktSz = objCP.getint("server", "pktsize")
intWinSz = objCP.getint("server", "initwinsize")
intMax = objCP.getint("server", "maxwinsize")
intIcr = 1
fltTmOtSt = float(objCP.getint("server", "timeout"))   # Get the default time out
fltTmOt = fltTmOtSt   # Set the initial value for time out
fltAlp = float(objCP.get("server", "alpha"))
arrWin = []
dicDly = {}   # The dictionary to log packet delays
arrLoss = []   # The array to log the window size when each packet loss is detected
arrSlp = []   # The array to track the slope of the change (slope = delta(winsize)/(packet SEQ))
fltAvg = 0   # The average slope calculated
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

  tmSrt = time.time()  # Start timer
  objSkt.settimeout(fltTmOt)
  try:
    tmPkt = time.time()
    while bChk and len(arrWin) > 0: 
      strRecv, objAddr = objSkt.recvfrom(30)
      dicDly[int(strRecv)] = str(time.time() - tmPkt)   # Record the delay of this packet
      
      if int(strRecv) in arrWin:
        arrWin.remove(int(strRecv))
  except socket.timeout:
    print "timeout when receiving ACK at %s" % (str(intSEQ))
    arrLoss.append([intSEQ, intWinSz])
    intLLen = len(arrLoss)
    if intLLen > 1:   # Track the slope of the change
      arrSlp.append((arrLoss[intLLen - 1][1] - arrLoss[intLLen - 2][1]) / (arrLoss[intLLen - 1][0] - arrLoss[intLLen - 2][0]))
      # Calculate average slope
      if len(arrSlp) > 2:
        fltAvg = 0
        for fltSlp in arrSlp:
          fltAvg += fltSlp
        fltAvg = fltAvg / (len(arrSlp) - 1)

    intSEQ = arrWin[0] - intPktSz   # Reset the SEQ to where it failed, which is the smallest SEQ in the sliding window
    arrWin = []
    intMax = intWinSz
    intIcr = 1
    intWinSz = math.floor(intWinSz / 2) # Reset the window size back to 1
    fltTmOt = fltTmOtSt   # Reset the initial value for time out
    pass

  # Update the window size
  if len(arrLoss) < 3:   # Kind of slow start
    if intWinSz * 2 < intMax:
      intWinSz = intWinSz * 2   # Double the window size if it's less than the max window size
    else:
      intWinSz = intWinSz * 1.25
      #intIcr += 1   # The increment of window size increase itself by 1 after each successful ACK
  else:
    print "The current average slope is %s" % (str(fltAvg))
    intWinSz = intWinSz * (1 + fltAvg)
    if intWinSz < intMax / 2:
      intWinSz = intWinSz * 1.2

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