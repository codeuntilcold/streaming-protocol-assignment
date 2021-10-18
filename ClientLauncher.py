import sys
from tkinter import Tk
from Client import Client

if __name__ == "__main__":
	try:
		serverAddr = sys.argv[1]
		serverPort = sys.argv[2]  # where the server is listening on
		rtpPort = sys.argv[3]     # where the RTP packets are received
		fileName = sys.argv[4]	
	except:
		print("[Usage: ClientLauncher.py Server_name Server_port RTP_port Video_file]\n")	
	
	# create GUI
	root = Tk()
	
	# Create a new client
	app = Client(root, serverAddr, serverPort, rtpPort, fileName)
<<<<<<< HEAD
	app.master.title("RTPClient")   # changetitle	
	root.resizable(0,0)             # create a fixed window, not change size
	root.mainloop()                 # display window on screen
=======
	app.master.title("RTPClient")
	root.mainloop()
>>>>>>> aace24fea9aceed09b8bf37f61193d9fb4cac736
	