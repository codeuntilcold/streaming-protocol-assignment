from tkinter import *
import customtkinter
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os
import time

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:

	SETUP_STR = 'SETUP'
	PLAY_STR = 'PLAY'
	PAUSE_STR = 'PAUSE'
	TEARDOWN_STR = 'TEARDOWN'
	DESCRIBE_STR = 'DESCRIBE'
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT
	
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3
	DESCRIBE = 4
	FORWARD = 5
	BACKWARD = 6

	STEP_RANGE = 50

	RTSP_VER = "RTSP/1.0"
	TRANSPORT = "RTP/UDP"
	
	# For statistics
	tbegin = 0
	tend = 0
	texec = 0
	totalData = 0

	version = 'Not stream yet!'

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
		self.rtpSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
		
	# Initiation
	def createWidgets(self):
		"""Build GUI."""
		customtkinter.set_appearance_mode("Dark") # Other: "Light", "System"
		#self.master.configure(background = '#006666')

		# Create Setup button
		#photo = ImageTk.PhotoImage(Image.open('./Setup.png').resize((32,32)))
		self.setup = customtkinter.CTkButton(master=self.master,fg_color=("#8FBDD9"),text="SET UP",corner_radius=16, command=self.setupMovie)
		self.setup.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)#width=20, padx=3, pady=3)
		self.setup.grid(row=1, column=0, padx=2, pady=2)

		# Create Describe button		
		# self.describe = customtkinter.CTkButton(master=self.master,fg_color=("black"),text="DESCRIBE",corner_radius=16, command=self.describeMovie)
		# self.describe.grid(row=1, column=1, padx=2, pady=2)
		
		# Create Play button		
		self.start = customtkinter.CTkButton(master=self.master,fg_color=("#566AA6"),text="PLAY",corner_radius=16, command=self.playMovie)
		self.start.grid(row=1, column=1, padx=2, pady=2)
		
		# Create Pause button			
		self.pause = customtkinter.CTkButton(master=self.master,fg_color=("#495A8C"),text="PAUSE",corner_radius=16, command=self.pauseMovie)
		self.pause.grid(row=1, column=2, padx=2, pady=2)
		
		# Create Teardown button
		self.teardown = customtkinter.CTkButton(master=self.master,fg_color=("#1E2D59"),text="TEARDOWN",corner_radius=16, command=self.exitClient)
		self.teardown.grid(row=1, column=3, padx=2, pady=2)
		
		# Create Backward button
		self.backwardbtn = customtkinter.CTkButton(master=self.master,fg_color=("#8FBDD9"),text="<<",corner_radius=16, command=self.backwardMovie)
		self.backwardbtn.grid(row=2, column=0, padx=2, pady=2)
		
		# Create Forward button
		self.forwardbtn = customtkinter.CTkButton(master=self.master,fg_color=("#566AA6"),text=">>",corner_radius=16, command=self.forwardMovie)
		self.forwardbtn.grid(row=2, column=1, padx=2, pady=2)

		# Create Time button
		self.remtime = customtkinter.CTkButton(master=self.master,fg_color=("#495A8C"),text="...",corner_radius=16)
		self.remtime.grid(row=2, column=2, padx=2, pady=2)

		self.totaltime = customtkinter.CTkButton(master=self.master,fg_color=("#1E2D59"),text="...",corner_radius=16)
		self.totaltime.grid(row=2, column=3, padx=2, pady=2)

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
			photo = ImageTk.PhotoImage(Image.open(imageFile)) 
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
		if tkinter.messagebox.askokcancel("Quit?", "Are you sure you want to quit?"):
			self.exitClient()
		else: # When the user presses cancel, resume playing.
			self.playMovie()

	# RTSP REQUESTS TRIGGER
	def setupMovie(self):
		"""Setup button handler."""
		if self.state == self.INIT:
			self.sendRtspRequest(self.SETUP)

	def describeMovie(self):
		"""Describe button handler."""
		if self.state == self.READY or self.state == self.PLAYING:
			self.sendRtspRequest(self.DESCRIBE)

	def pauseMovie(self):
		"""Pause button handler."""
		if self.state == self.PLAYING:
			self.sendRtspRequest(self.PAUSE)
	
	def playMovie(self):
		"""Play button handler."""
		if self.state == self.READY:
			self.sendRtspRequest(self.PLAY)

	def forwardMovie(self):
		if (self.state == self.READY or self.state == self.PLAYING) and (self.frameNbr + self.STEP_RANGE < self.totalCounter):
			self.sendRtspRequest(self.FORWARD, self.STEP_RANGE)

	def backwardMovie(self):
		if (self.state == self.READY or self.state == self.PLAYING) and (self.frameNbr - self.STEP_RANGE > 0):
			self.sendRtspRequest(self.BACKWARD, -self.STEP_RANGE)

	def exitClient(self):
		"""Teardown button handler."""
		self.sendRtspRequest(self.TEARDOWN)
		self.master.destroy()
		os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)

		# Calculate stats
		# dataRate = float(self.totalData / (self.texec * 1000))
		# print('='*60 + 
		# 	"\nTransmission Rate:    {:.2f}".format(dataRate) + " Kbps\n"
		# 	+ '='*60)
		sys.exit(0)
	
	# SENDING AND RECEIVING FRAMES

	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""

		# Set the timeout value of the socket to 0.5sec
		self.rtpSocket.settimeout(0.5)

		# Create a new datagram socket to receive RTP packets from the server
		try:
			# Bind the socket to the address using the RTP port given by the client user
			self.rtpSocket.bind((self.serverAddr,self.rtpPort))   # in case port is used by other process
			print("Bind RtpPort Success")
		except:
			tkinter.messagebox.showwarning('Connection Failed', 'Connection to rtpServer failed...')

	def listenRtp(self):
		"""Listen for RTP packets."""
		print('[RTP] Listening on port ', self.rtpPort)

		while True:
			try:
				byteStream, _ = self.rtpSocket.recvfrom(20480)

				if byteStream:
					packet = RtpPacket()
					packet.decode(byteStream)
					print("||Received Rtp Packet #" + str(packet.seqNum()) + "|| ")

					try:
						currFrameNbr = packet.seqNum()
						self.version = packet.version()
					except:
						print("seqNum() error")
						print('-'*60)
						traceback.print_exc(file=sys.stdout)
						print('-'*60)

					# if currFrameNbr > self.frameNbr: # Discard the late packet
					self.frameNbr = currFrameNbr
					self.totalData += len(packet.getPayload())
					self.remtime.set_text('Cur: {:.1f}'.format(self.frameNbr * 0.05) + ' s')
					self.updateMovie(self.writeFrame(packet.getPayload()))

			except:
				# Stop listening upon requesting PAUSE or TEARDOWN
				print("Didn`t receive data!")
				if self.playEvent.isSet() or self.frameNbr >= self.totalCounter:
					break

				# Upon receiving ACK for TEARDOWN request,
				# close the RTP socket
				if self.teardownAcked == 1:
					self.rtpSocket.shutdown(socket.SHUT_RDWR)
					self.rtpSocket.close()
					break

	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
		self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.rtspSocket.connect((self.serverAddr, self.serverPort))
		except:
			tkinter.messagebox.showwarning('Connection Failed', 'Connection to \'%s\' failed.' %self.serverAddr)

	# RTSP REQUESTS	

	def sendRtspRequest(self, requestCode, playRange=0):
		"""Send RTSP request to the server."""	
		#-------------
		# TO COMPLETE
		#-------------
		if requestCode == self.SETUP and self.state == self.INIT:
			threading.Thread(target=self.recvRtspReply).start()
                
			# Update RTSP sequence number.
			self.rtspSeq+=1
			
			# Write the RTSP request to be sent.
			request = "%s %s %s" % (self.SETUP_STR,self.fileName,self.RTSP_VER)
			request+="\nCSeq: %d" % self.rtspSeq
			request+="\nTransport: %s; client_port= %d" % (self.TRANSPORT,self.rtpPort)
			
			# Keep track of the sent request.
			self.requestSent = self.SETUP
			
			# Play request
		elif requestCode == self.PLAY and self.state == self.READY:
        
			# Update RTSP sequence number.
			self.rtspSeq+=1
        
			# Write the RTSP request to be sent.
			request = "%s %s %s" % (self.PLAY_STR,self.fileName,self.RTSP_VER)
			request+="\nCSeq: %d" % self.rtspSeq
			request+="\nSession: %d"%self.sessionId
			request+="\nRange: %d"%playRange
                
			
			# Keep track of the sent request.
			self.requestSent = self.PLAY
            
            
            # Pause request
		elif requestCode == self.PAUSE and self.state == self.PLAYING:
        
			# Update RTSP sequence number.
			self.rtspSeq+=1
			
			request = "%s %s %s" % (self.PAUSE_STR,self.fileName,self.RTSP_VER)
			request+="\nCSeq: %d" % self.rtspSeq
			request+="\nSession: %d"%self.sessionId
			
			self.requestSent = self.PAUSE
			
			# Teardown request
		elif requestCode == self.TEARDOWN and not self.state == self.INIT:
        
			# Update RTSP sequence number.
			self.rtspSeq+=1
			
			# Write the RTSP request to be sent.
			request = "%s %s %s" % (self.TEARDOWN_STR, self.fileName, self.RTSP_VER)
			request+="\nCSeq: %d" % self.rtspSeq
			request+="\nSession: %d" % self.sessionId
			
			self.requestSent = self.TEARDOWN
		
			# Describe request
		elif requestCode == self.DESCRIBE and not self.state == self.INIT:
    			
			# Update RTSP sequence number.
			self.rtspSeq+=1
			
			# Write the RTSP request to be sent.
			request = "%s %s %s" % (self.DESCRIBE_STR, self.fileName, self.RTSP_VER)
			request+="\nCSeq: %d" % self.rtspSeq
			request+="\nSession: %d" % self.sessionId
			
			self.requestSent = self.DESCRIBE

		elif requestCode == self.BACKWARD:
			
			# Update RTSP sequence number.
			self.rtspSeq+=1
			
			# Write the RTSP request to be sent.
			request = "%s %s %s" % (self.PLAY_STR, self.fileName, self.RTSP_VER)
			request+="\nCSeq: %d" % self.rtspSeq
			request+="\nSession: %d" % self.sessionId
			request+="\nRange: %d"%playRange
			
			self.requestSent = self.PLAY

		elif requestCode == self.FORWARD:

			# Update RTSP sequence number.
			self.rtspSeq+=1
			
			# Write the RTSP request to be sent.
			request = "%s %s %s" % (self.PLAY_STR, self.fileName, self.RTSP_VER)
			request+="\nCSeq: %d" % self.rtspSeq
			request+="\nSession: %d" % self.sessionId
			request+="\nRange: %d"%playRange
			
			self.requestSent = self.PLAY
		else:
			return
		
		# Send the RTSP request using rtspSocket.
		self.rtspSocket.send(request.encode())
		
		print ('\nData Sent:\n' + request)
	
	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		#TO DO
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
		#TO DO
		print("Parsing Received Rtsp data...")

		"""Parse the RTSP reply from the server."""
		lines = data.decode().split('\n')
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
						self.state = self.READY
						
						# # Open RTP port.
						self.openRtpPort()

					
						self.totalCounter = int(lines[3].split(' ')[1])
						print(self.totalCounter)
						self.totaltime.set_text('Tot: ' + str(self.totalCounter * 0.05) + ' s')
						self.remtime.set_text('Cur: 0 s')

					elif self.requestSent == self.PLAY:
						self.state = self.PLAYING
						threading.Thread(target=self.listenRtp).start()
						self.playEvent = threading.Event()
						self.playEvent.clear()

						# Start tracking time
						self.tstart = time.time()

					elif self.requestSent == self.PAUSE:
						self.state = self.READY
						# The play thread exits. A new thread is created on resume.
						self.playEvent.set()
						
						self.tend = time.time()
						self.texec += self.tend - self.tstart
						# Stop tracking time
						self.tstart = 0	

					elif self.requestSent == self.TEARDOWN:
						self.state = self.INIT
						# Flag the teardownAcked to close the socket.
						self.teardownAcked = 1 

						if self.tstart:
							self.tend = time.time()
							self.texec += self.tend - self.tstart

					elif self.requestSent == self.DESCRIBE:
						print('SESSION DESCRIPTION INFO:')
						print('Streaming kind: RTSP protocol')
						print('Version: ' + str(self.version))

					# elif self.requestSent == self.FORWARD or self.requestSent == self.BACKWARD:


"""
TIẾN - GIAO DIỆN: CREATEWIDGETS, HANDLER, UPDATE MOVIE, WRITEFRAME

DŨNG - SERVER + RTP: listenRtp, sendRtspRequest, openRtpPort

TRÍ  - RTSP REQUEST: SETUP, PLAY, PAUSE, TEARDOWN

TOÀN - RTSP: sendRtspRequest, recvRtspReply, parseRtspReply

DEADLINE: Chủ nhật 10/10, họp lại sau dl để viết báo cáo.
"""

