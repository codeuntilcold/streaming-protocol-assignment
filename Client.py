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

	""" DŨNG NOTE: 
		UDP: 	client: sendto -> recvfrom
				server: bind -> recvfrom -> sendto
		TCP: 	client: connect -> send -> recv
				server: bind -> listen -> accept -> recv -> send
	"""

	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""

		# Create a new datagram socket to receive RTP packets from the server
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.rtpSocket.bind(('', self.rtpPort))

		# Set the timeout value of the socket to 0.5sec
		self.rtpSocket.settimeout(0.5)

	def listenRtp(self):
		"""Listen for RTP packets."""
		print('[RTP] Listening on port ' + self.rtpPort)

		# Receive a RtpPacket from this line of code in ServerWorker
		byteStream, address = self.rtpSocket.recvfrom(1024)
		
		packet = RtpPacket()
		packet.decode(byteStream)
		imageFile = packet.getPayload()

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
	
	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		#TODO
	
	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		#TODO

"""
TIẾN - GIAO DIỆN: CREATEWIDGETS, HANDLER, UPDATE MOVIE, WRITEFRAME

DŨNG - SERVER + RTP: listenRtp, connectToServer, openRtpPort

TRÍ  - RTSP REQUEST: SETUP, PLAY, PAUSE, TEARDOWN

TOÀN - RTSP: sendRtspRequest, recvRtspReply, parseRtspReply

DEADLINE: Chủ nhật 10/10, họp lại sau dl để viết báo cáo.
"""



