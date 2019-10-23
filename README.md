# ComputerNetAss1
Database:
Lưu:
-account{username,password}, phân biệt nhau bằng username (không có 2 usernam==nhau)
online_peer{username,ip,port}. Khi login thì add vào online_peer, logout( hoặc không kết nối đến nữa) thì lấy ra khỏi online_peer =>Có thể check những ai đang onl dựa vào online_peer
-Handle login,logout,create tài khoản, checkonline,.... 
Các peer khi gửi message lên server sẽ có dạng (type(login,logout,join(muốn tạo tk) hay checkonl(xem thử có ai đang onl), tên đăng nhập và mật khẩu( trường hợp checkonl thì tên đăng
nhập là tên tài khoản muốn check).
Khi một peer gửi một message lên server thì tạo một thread để handle cái message đó, có các trường hợp sau:
Nếu là gửi để đăng kí tk: check xem có username trùng chưa, có thì gửi message thông báo là bị trùng rồi, không thì tạo tk add vô database (lúc này thì thread bị lock tránh trường hợp nhiều thằng cùng vô đăng kí)
Nếu là login : sau khi check bình thường nếu login thành công thì mở lock( bây giờ thì không vấn đề gì), sau đó add vào online_peers, sau đó cũng tạo thêm một serverThread, nhiệm vụ là lắng nghe liên tục xem peer này có còn đang hoạt động không, không thì serverThread sẽ tụ động kick peer này ra (xóa khỏi online peer)
Nếu là logout: kick peer này ra (xóa khỏi online peer) đồng thời kết thúc thread.
Nếu là check ai đang onl: tìm trong onlone_peer_list xem có không, có thì đang onl không thì không onl
ServerThread để kiểm tra xem một peer có onl không:
user đang onl thì sẽ có một message "ẩn" gửi mỗi lần 1s đến server, nếu trong 5s không thấy tín hiệu ẩn này gửi tới thì coi như đã off.


