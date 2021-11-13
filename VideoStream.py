class VideoStream:
	def __init__(self, filename):
		self.filename = filename
		try:
			self.file = open(filename, 'rb')
		except:
			raise IOError
		
		self.frames = self.getAllFrames()
		self.frameNum = 0
		
	def nextFrame(self):
		"""Get next frame."""
		if (self.frameNum < self.getNumOfFrames()):
			self.frameNum += 1
			return self.frames[self.frameNum - 1]
		
	def frameNbr(self):
		"""Get frame number."""
		return self.frameNum

	def getNumOfFrames(self):
		# Get number of frames for video
		return len(self.frames)

	def goTo(self, nframe):
		dest = self.frameNum + nframe
		if dest > 0 or dest < self.getNumOfFrames():
			self.frameNum = dest
		return self.frameNum

	def getAllFrames(self):
		allframes = []
		while True:
			data = self.file.read(5)
			if data:
				framelen = int(data)
				data = self.file.read(framelen)
				allframes.append(data)
			else:
				self.file.seek(0)
				break
		
		return allframes
	
	