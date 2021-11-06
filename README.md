### streaming-protocol-assignment
Đây là Github chung cho BTL1 môn Mạng máy tính.

### Hướng dẫn sử dụng
Đầu tiên, khởi động server: python Server.py <server_port>
Trong đó server_port là cổng dành cho server lắng nghe kết nối RTSP từ client. Thường là 554 nhưng nên chọn port lớn hơn 1024.

Tiếp theo, mở 1 terminal khác và khởi động client: python ClientLauncher.py <server_host> <server_port> <RTP_port> <video_file>
VD: python ClientLauncher.py localhost 1025 8000 movie.Mjpeg