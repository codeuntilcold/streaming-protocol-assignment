from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT
	
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3
	
	def __init__(self, master, serveraddr, serverport, rtpport, filename):
		self.master = master
		self.master.protocol("WM_DELETE_WINDOW", self.handler)
		self.createWidgets()
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)
		self.rtpPort = int(rtpport)
		self.fileName = filename
		self.rtspSeq = 0
		self.sessionId = 0
		self.requestSent = -1
		self.teardownAcked = 0
		self.connectToServer()
		self.frameNbr = 0
		
	# Initiation
	# THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI 	
	def createWidgets(self):
		"""Build GUI."""
		# Create Setup button
		self.setup = Button(self.master, width=20, padx=3, pady=3)
		self.setup["text"] = "Setup"
		self.setup["command"] = self.setupMovie
		self.setup.grid(row=1, column=0, padx=2, pady=2)
		
		# Create Play button		
		self.start = Button(self.master, width=20, padx=3, pady=3)
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start.grid(row=1, column=1, padx=2, pady=2)
		
		# Create Pause button			
		self.pause = Button(self.master, width=20, padx=3, pady=3)
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=1, column=2, padx=2, pady=2)
		
		# Create Teardown button
		self.teardown = Button(self.master, width=20, padx=3, pady=3)
		self.teardown["text"] = "Teardown"
		self.teardown["command"] =  self.exitClient
		self.teardown.grid(row=1, column=3, padx=2, pady=2)
		
		# Create a label to display the movie
		self.label = Label(self.master, height=19)
		self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5) 
	
	# VIDEO DISPLAY
	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""

		""" Không bắt lỗi :"""
		# cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
		# file = open(cachename, "wb")
		# file.write(data)
		# file.close()
		
		# return cachename
		""" else : """
		cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT

		try:
			file = open(cachename, "wb")
		except:
			print("file open error")

		try:
			file.write(data)
		except:
			print("file write error")

		file.close()

		return cachename

	
	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
		# ----------------------------------------------------
		""" Nếu không bắt lỗi khi mở ảnh :"""
		# photo = ImageTk.PhotoImage(Image.open(imageFile))
		# self.label.configure(image = photo, height=288) 
		# self.label.image = photo

		""" else :"""
		try:
			photo = ImageTk.PhotoImage(Image.open(imageFile)) #stuck here !!!!!!
		except:
			print("photo error")
			print('-'*60)
			traceback.print_exc(file=sys.stdout)
			print('-'*60)

		self.label.configure(image = photo, height=288)
		self.label.image = photo

	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		self.pauseMovie()
		#if tkMessageBox.askokcancel("Quit?", "Are you sure you want to quit?"):
		if tkinter.messagebox.askokcancel("Quit?", "Are you sure you want to quit?"):
			self.exitClient()
		else: # When the user presses cancel, resume playing.
			#self.playMovie()
			print("Playing Movie")
			threading.Thread(target=self.listenRtp).start()
			#self.playEvent = threading.Event()
			#self.playEvent.clear()
			self.sendRtspRequest(self.PLAY)

	# RTSP REQUESTS TRIGGER
	def setupMovie(self):
		"""Setup button handler."""
		if self.state == self.INIT:
    			self.sendRtspRequest(self.SETUP)

	def pauseMovie(self):
		"""Pause button handler."""
		if self.state == self.PLAYING:
    			self.sendRtspRequest(self.PAUSE)
	
	def playMovie(self):
		"""Play button handler."""
		if self.state == self.READY:
    			# print("Play movie")
				# threading.Thread(target=self.listenRtp).start()
				# self.playEvent = threading.Event()
				# self.playEvent.clear()
				# self.playMovie
				self.sendRtspRequest(self.PLAY)

	def exitClient(self):
		"""Teardown button handler."""
		self.sendRtspRequest(self.TEARDOWN)
		self.master.destroy()
		os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)
		# rate = float(self.counter/self.frameNbr)
		# print
		sys.exit(0)
	
	# SENDING AND RECEIVING FRAMES

	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""

		# Create a new datagram socket to receive RTP packets from the server
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.rtpSocket.bind((self.serverAddr, self.rtpPort))

		# Set the timeout value of the socket to 0.5sec
		self.rtpSocket.settimeout(0.5)

	def listenRtp(self):
		"""Listen for RTP packets."""
		print('[RTP] Listening on port ' + self.rtpPort)

		while True:
			try:
				byteStream, address = self.rtpSocket.recvfrom(1024)
				
				packet = RtpPacket()
				packet.decode(byteStream)

				currentFrameNum = packet.seqNum()
				if currentFrameNum > self.frameNbr:
					self.frameNbr = currentFrameNum
					imageFile = packet.getPayload()
					self.updateMovie(self.writeFrame(imageFile))
			except:
				# Stop listening when receive PAUSE or TEARDOWN
				if self.playEvent.isSet():
					break

				if self.teardownAcked == 1:
					self.rtpSocket.shutdown(socket.SHUT_RDWR)
					self.rtpSocket.close()
					break
					
			### Info for DESCRIBE request
			
			# version = packet.version()
			# sequence = packet.seqNum()
			# ts = packet.timestamp()
			# payloadType = packet.payloadType()

	# RTSP REQUESTS
	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
		self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.rtspSocket.connect((self.serverAddr, self.serverPort))
		print('[RTSP] Connected to ' + self.serverAddr + ' port ' + str(self.serverPort))
	

	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""	
		#-------------
		# TO COMPLETE
		#-------------
		if requestCode == self.SETUP and self.state == self.INIT:
			threading.Thread(target=self.recvRtspReply).start()
			# Update RTSP sequence number.
			# ...
			self.rtspSeq = 1

			# Write the RTSP request to be sent.
			# request = ...
			request = "SETUP " + str(self.fileName) + "\n" + str(self.rtspSeq) + "\n" + " RTSP/1.0 RTP/UDP " + str(self.rtpPort)

			self.rtspSocket.send(request)
			# Keep track of the sent request.
			# self.requestSent = ...
			self.requestSent = self.SETUP

		# Play request
		elif requestCode == self.PLAY and self.state == self.READY:
			# Update RTSP sequence number.
			# ...
			self.rtspSeq = self.rtspSeq + 1
			# Write the RTSP request to be sent.
			# request = ...
			request = "PLAY " + "\n" + str(self.rtspSeq)

			self.rtspSocket.send(request)
			print '-'*60 + "\nPLAY request sent to Server...\n" + '-'*60
			# Keep track of the sent request.
			# self.requestSent = ...
			self.requestSent = self.PLAY

		# Pause request
		elif requestCode == self.PAUSE and self.state == self.PLAYING:
			# Update RTSP sequence number.
			# ...
			self.rtspSeq = self.rtspSeq + 1
			# Write the RTSP request to be sent.
			# request = ...
			request = "PAUSE " + "\n" + str(self.rtspSeq)
			self.rtspSocket.send(request)
			print '-'*60 + "\nPAUSE request sent to Server...\n" + '-'*60
			# Keep track of the sent request.
			# self.requestSent = ...
			self.requestSent = self.PAUSE

		# Resume request


		# Teardown request
		elif requestCode == self.TEARDOWN and not self.state == self.INIT:
			# Update RTSP sequence number.
			# ...
			self.rtspSeq = self.rtspSeq + 1
			# Write the RTSP request to be sent.
			# request = ...
			request = "TEARDOWN " + "\n" + str(self.rtspSeq)
			self.rtspSocket.send(request)
			print '-'*60 + "\nTEARDOWN request sent to Server...\n" + '-'*60
			# Keep track of the sent request.
			# self.requestSent = ...
			self.requestSent = self.TEARDOWN

		else:
			return

		# Send the RTSP request using rtspSocket.
		# ...

#		print '\nData sent:\n' + request
	
	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		#TODO
		while True:
			reply = self.rtspSocket.recv(1024)

			if reply:
				self.parseRtspReply(reply)

			# Close the RTSP socket upon requesting Teardown
			if self.requestSent == self.TEARDOWN:
				self.rtspSocket.shutdown(socket.SHUT_RDWR)
				self.rtspSocket.close()
				break
	
	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		#TODO
		print "Parsing Received Rtsp data..."

		"""Parse the RTSP reply from the server."""
		lines = data.split('\n')
		seqNum = int(lines[1].split(' ')[1])

		# Process only if the server reply's sequence number is the same as the request's
		if seqNum == self.rtspSeq:
			session = int(lines[2].split(' ')[1])
			# New RTSP session ID
			if self.sessionId == 0:
				self.sessionId = session

			# Process only if the session ID is the same
			if self.sessionId == session:
				if int(lines[0].split(' ')[1]) == 200:
					if self.requestSent == self.SETUP:
						#-------------
						# TO COMPLETE
						#-------------
						# Update RTSP state.
						print "Updating RTSP state..."
						# self.state = ...
						self.state = self.READY
						# Open RTP port.
						#self.openRtpPort()
						print "Setting Up RtpPort for Video Stream"
						self.openRtpPort()

					elif self.requestSent == self.PLAY:
						 self.state = self.PLAYING
						 print '-'*60 + "\nClient is PLAYING...\n" + '-'*60
					elif self.requestSent == self.PAUSE:
						 self.state = self.READY

						# The play thread exits. A new thread is created on resume.
						 self.playEvent.set()

					elif self.requestSent == self.TEARDOWN:
						# self.state = ...

						# Flag the teardownAcked to close the socket.
						self.teardownAcked = 1

"""
TIẾN - GIAO DIỆN: CREATEWIDGETS, HANDLER, UPDATE MOVIE, WRITEFRAME

DŨNG - SERVER + RTP: listenRtp, connectToServer, openRtpPort

TRÍ  - RTSP REQUEST: SETUP, PLAY, PAUSE, TEARDOWN

TOÀN - RTSP: sendRtspRequest, recvRtspReply, parseRtspReply

DEADLINE: Chủ nhật 10/10, họp lại sau dl để viết báo cáo.
"""



