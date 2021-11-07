import sys, socket

from ServerWorker import ServerWorker

class Server:	
	
	def main(self):
		try:
			SERVER_PORT = int(sys.argv[1])
		except:
			print("[Usage: Server.py Server_port]\n")
		# create a new socket
		# first param is Address Family, socket.AF_INET: IPv4
		# second param is Socket Type, socket.SOCK_STREAM: TCP
		rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		# register name for socket and bind it into socket
		rtspSocket.bind(('', SERVER_PORT))
		# allow maximum 5 connections
		rtspSocket.listen(5)        

		# Receive client info (address,port) through RTSP/TCP session
		while True:
			clientInfo = {}
			#print(1)
			# Client request and server accept, 1 socket is created. Client and server can communicate with each other
			clientInfo['rtspSocket'] = rtspSocket.accept()
			ServerWorker(clientInfo).run()

if __name__ == "__main__":
	(Server()).main()


