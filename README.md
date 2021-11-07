## streaming-protocol-assignment

❌ TUYỆT ĐỐI KHÔNG MERGE VÀO NHÁNH CHÍNH

Đây là nhánh chức năng của phần mở rộng. Ở nhánh này phát triển thêm tính năng kết nối trình chơi video tới trình duyệt thông qua Flask.

### Nguyên lý hoạt động

Ứng dụng Flask sẽ khởi động một Client và cho nó kết nối với server. 
Mỗi lần bấm nút, Flask sẽ gọi hàm tương ứng bên client.
Khi stream video, hàm `listenRtp` trong client sẽ `yield` khung hình nhận được và Flask sẽ nhận nhiệm vụ stream từng khung hình tới trình duyệt.

### Cách sử dụng
- Khởi tạo server
```
python Server.py <server-port>
```
- Khởi tạo Flask client
```
python App.py localhost <server-port> <client-port> movie.Mjpeg
```
- Truy cập vào địa chỉ `localhost:5000` trên trình duyệt.

❌ Lưu ý: Một khi TEARDOWN rồi thì phải khởi động lại app.