"""Bài cơ sở tri thức mẫu cho demo (seed_demo.py nạp vào kb_documents + Chroma).

Nội dung viết ở mức hướng dẫn chung, không ghi mức phạt cụ thể (dễ lỗi thời
khi nghị định thay đổi) — trợ lý chỉ nhắc tài xế tra văn bản hiện hành."""

DEMO_KB = [
    {
        "category": "safety",
        "title": "Lái xe đường dài ban đêm",
        "content": """# Lái xe đường dài ban đêm

## Trước chuyến đi
- Ngủ đủ 7–8 tiếng trong 24 giờ trước ca đêm, tránh thức khuya ngay trước khi nhận xe.
- Kiểm tra đèn pha, đèn cốt, đèn sương mù và cần gạt nước.
- Báo điều phối tuyến đường và giờ dự kiến tới nơi.

## Trong khi lái
- Khung giờ 1h–5h sáng là lúc cơ thể buồn ngủ nhất, cần dừng nghỉ chủ động.
- Dùng đèn chiếu gần khi có xe ngược chiều, không nhìn thẳng vào đèn xe đối diện.
- Giữ khoảng cách xa hơn ban ngày vì khó ước lượng tốc độ xe phía trước.

## Khi thấy mệt
- Dừng ở trạm dừng nghỉ hoặc cây xăng sáng đèn, không dừng ở lề đường tối.
- Chợp mắt 15–20 phút có hiệu quả hơn uống thêm cà phê.""",
    },
    {
        "category": "safety",
        "title": "Quy tắc nghỉ giữa ca lái",
        "content": """# Quy tắc nghỉ giữa ca lái

## Thời gian lái theo luật
- Lái xe liên tục không quá 4 giờ, tổng thời gian lái không quá 10 giờ trong một ngày và không quá 48 giờ trong một tuần.
- Sau mỗi 4 giờ lái phải nghỉ ít nhất 15 phút.

## Nghỉ thế nào cho hiệu quả
- Ra khỏi cabin, đi lại và vươn vai vài phút.
- Uống nước, ăn nhẹ; tránh bữa quá no vì dễ gây buồn ngủ.
- Nếu hệ thống cảnh báo buồn ngủ 2 lần trong 1 giờ, dừng nghỉ ngay ở điểm an toàn gần nhất.

## Ghi nhận
- Thời gian nghỉ được ghi nhận qua hành trình trên app, điều phối dựa vào đó để xếp ca.""",
    },
    {
        "category": "safety",
        "title": "Xử lý khi xe nổ lốp trên đường",
        "content": """# Xử lý khi xe nổ lốp trên đường

## Ngay khi nổ lốp
- Giữ chặt vô lăng bằng hai tay, giữ xe đi thẳng.
- Không đạp phanh gấp; nhả chân ga để xe giảm tốc từ từ.
- Bật đèn khẩn cấp, quan sát gương rồi đánh lái nhẹ vào lề.

## Sau khi dừng xe
- Đặt biển cảnh báo phía sau xe, cách ít nhất 50 m (xa hơn trên cao tốc).
- Hành khách xuống xe, đứng ngoài lan can hoặc xa làn đường.
- Trên cao tốc không tự thay lốp; gọi hotline cứu hộ của công ty trong app.

## Báo cáo
- Gửi Báo cáo sự cố trong app kèm ảnh lốp và vị trí để điều phối sắp xếp xe thay thế.""",
    },
    {
        "category": "safety",
        "title": "Lái xe an toàn khi trời mưa lớn",
        "content": """# Lái xe an toàn khi trời mưa lớn

## Giảm nguy cơ trượt nước
- Giảm tốc độ, không phanh gấp hoặc đánh lái đột ngột.
- Lốp mòn dễ trượt nước, báo bảo trì khi gai lốp còn dưới 2 mm.

## Tầm nhìn
- Bật đèn chiếu gần, kể cả ban ngày; không bật đèn khẩn cấp khi xe vẫn chạy.
- Tăng khoảng cách với xe trước lên gấp đôi.

## Ngập nước
- Không đi qua đoạn ngập quá nửa bánh xe.
- Nếu xe chết máy trong vùng ngập, không đề máy lại; báo cứu hộ.""",
    },
    {
        "category": "safety",
        "title": "Sơ cứu cơ bản khi gặp tai nạn",
        "content": """# Sơ cứu cơ bản khi gặp tai nạn

## Bảo đảm an toàn hiện trường
- Bật đèn khẩn cấp, đặt biển cảnh báo, tắt máy các xe liên quan.
- Gọi 115 (cấp cứu) và 113 (công an) — số gọi nhanh có sẵn trong app.

## Với người bị thương
- Không di chuyển nạn nhân nghi chấn thương cột sống, trừ khi có nguy cơ cháy nổ.
- Cầm máu bằng cách ép trực tiếp lên vết thương bằng vải sạch.
- Giữ ấm và trò chuyện để nạn nhân tỉnh táo cho đến khi cấp cứu tới.

## Sau đó
- Chụp ảnh hiện trường, gửi Báo cáo sự cố trong app để công ty hỗ trợ thủ tục.""",
    },
    {
        "category": "safety",
        "title": "Ảnh hưởng của rượu bia và thuốc khi lái xe",
        "content": """# Ảnh hưởng của rượu bia và thuốc khi lái xe

## Rượu bia
- Pháp luật cấm điều khiển phương tiện khi trong máu hoặc hơi thở có nồng độ cồn.
- Cồn làm chậm phản xạ và khiến người lái đánh giá sai khoảng cách.
- Đã uống rượu bia tối hôm trước thì sáng hôm sau vẫn có thể còn nồng độ cồn.

## Thuốc gây buồn ngủ
- Thuốc cảm, thuốc dị ứng, thuốc an thần thường gây buồn ngủ — đọc kỹ hướng dẫn sử dụng.
- Đang dùng thuốc loại này, báo điều phối để đổi ca.

## Chính sách công ty
- Vi phạm nồng độ cồn bị đình chỉ lái ngay, không phụ thuộc điểm vi phạm.""",
    },
    {
        "category": "safety",
        "title": "Tư thế ngồi lái đúng cách",
        "content": """# Tư thế ngồi lái đúng cách

## Ghế và vô lăng
- Lưng tựa sát ghế, khi duỗi tay cổ tay chạm được đỉnh vô lăng.
- Chân đạp hết phanh mà đầu gối vẫn hơi cong.
- Tựa đầu ngang tầm mắt để bảo vệ cổ khi va chạm phía sau.

## Gương
- Chỉnh gương trước khi xe lăn bánh, không chỉnh khi đang chạy.

## Vì sao quan trọng
- Ngồi sai tư thế gây mỏi lưng, mỏi vai — nguyên nhân dẫn tới mất tập trung trong các chuyến dài.
- Tư thế đúng cũng giúp camera giám sát nhận diện khuôn mặt chính xác hơn, tránh cảnh báo nhầm.""",
    },
    {
        "category": "safety",
        "title": "Dấu hiệu mệt mỏi cần dừng xe ngay",
        "content": """# Dấu hiệu mệt mỏi cần dừng xe ngay

## Dấu hiệu sớm
- Ngáp liên tục, mắt cay, chớp mắt chậm.
- Không nhớ vài cây số vừa đi qua.
- Xe lệch làn hoặc chạm vạch rung giảm tốc.

## Việc cần làm
- Dừng ở nơi an toàn gần nhất, không cố đi tiếp "cho kịp giờ".
- Chợp mắt 15–20 phút; mở cửa sổ hay bật nhạc to chỉ có tác dụng vài phút.

## Hệ thống hỗ trợ
- Camera trong cabin phát hiện mắt nhắm lâu và đầu gật để phát cảnh báo.
- Mỗi lần cảnh báo được ghi nhận và tính điểm vi phạm; điểm cao sẽ bị nhắc nhở hoặc tạm đình chỉ.""",
    },
    {
        "category": "traffic_law",
        "title": "Quy tắc sử dụng làn đường trên cao tốc",
        "content": """# Quy tắc sử dụng làn đường trên cao tốc

## Chọn làn
- Xe tải, xe khách lớn đi làn bên phải theo biển báo của từng tuyến.
- Làn trái dùng để vượt; vượt xong phải trở lại làn bên phải.

## Những việc bị cấm
- Dừng, đỗ xe trên làn chạy; chỉ dừng ở làn khẩn cấp khi xe hỏng.
- Lùi xe, quay đầu, đi ngược chiều.
- Chạy chậm hơn tốc độ tối thiểu ghi trên biển báo.

## Ra vào cao tốc
- Tăng tốc trên làn nhập trước khi hòa vào làn chính.
- Lỡ lối ra thì đi tiếp tới lối ra kế tiếp, không lùi lại.""",
    },
    {
        "category": "traffic_law",
        "title": "Giấy tờ bắt buộc mang theo khi lái xe kinh doanh",
        "content": """# Giấy tờ bắt buộc mang theo khi lái xe kinh doanh

## Của người lái
- Giấy phép lái xe đúng hạng (có thể xuất trình bản điện tử trên ứng dụng VNeID).
- Căn cước công dân.

## Của phương tiện
- Giấy chứng nhận đăng ký xe.
- Giấy chứng nhận kiểm định (tem đăng kiểm) còn hạn.
- Giấy chứng nhận bảo hiểm trách nhiệm dân sự bắt buộc còn hạn.

## Lưu ý
- Hạn tem đăng kiểm của từng xe được theo dõi trong mục Đăng kiểm; app nhắc trước khi hết hạn.""",
    },
    {
        "category": "traffic_law",
        "title": "Quy định về thắt dây an toàn",
        "content": """# Quy định về thắt dây an toàn

## Ai phải thắt
- Người lái và hành khách ở mọi vị trí ghế có trang bị dây an toàn.

## Trẻ em
- Trẻ em dưới 10 tuổi và cao dưới 1,35 m không ngồi cùng hàng ghế với người lái (trừ xe chỉ có một hàng ghế) và phải dùng thiết bị an toàn phù hợp.

## Trách nhiệm người lái
- Nhắc hành khách thắt dây trước khi xe chạy.
- Dây bị hỏng, kẹt hoặc không tự rút về: báo bảo trì, không chạy xe khi dây ghế lái hỏng.""",
    },
    {
        "category": "traffic_law",
        "title": "Ưu tiên xe cứu thương và xe chữa cháy",
        "content": """# Ưu tiên xe cứu thương và xe chữa cháy

## Nhận biết
- Xe ưu tiên đang làm nhiệm vụ có còi và đèn ưu tiên.

## Cách nhường đường
- Giảm tốc, đi sát lề phải hoặc dừng lại để xe ưu tiên vượt.
- Không bám theo sau xe ưu tiên để "đi nhờ" qua chỗ ùn tắc.
- Ở ngã tư đang đèn đỏ, không vượt đèn để nhường; chờ hướng dẫn của cảnh sát giao thông nếu có.

## Trên cao tốc
- Chừa trống làn khẩn cấp cho xe cứu hộ, cứu thương.""",
    },
    {
        "category": "vehicle_manual",
        "title": "Kiểm tra xe hằng ngày trước khi nhận ca",
        "content": """# Kiểm tra xe hằng ngày trước khi nhận ca

## Bên ngoài
- Lốp: nhìn độ căng, vết rách, gai lốp; kiểm tra cả lốp dự phòng.
- Đèn: pha, cốt, xi-nhan, đèn phanh, đèn lùi.
- Gương và kính không nứt.

## Khoang máy
- Mức dầu máy, nước làm mát, dầu phanh nằm giữa vạch MIN và MAX.

## Trong cabin
- Không có đèn cảnh báo sáng trên bảng đồng hồ sau khi nổ máy.
- Phanh tay giữ được xe; còi kêu rõ.
- Điện thoại chạy app giám sát đặt cố định, camera nhìn rõ mặt người lái.""",
    },
    {
        "category": "vehicle_manual",
        "title": "Ý nghĩa các đèn cảnh báo trên bảng đồng hồ",
        "content": """# Ý nghĩa các đèn cảnh báo trên bảng đồng hồ

## Đèn đỏ — dừng xe ngay
- Áp suất dầu máy thấp (hình bình dầu).
- Nhiệt độ nước làm mát cao (hình nhiệt kế).
- Hệ thống phanh (chữ BRAKE hoặc dấu chấm than trong vòng tròn).

## Đèn vàng — kiểm tra sớm
- Đèn Check Engine: lỗi động cơ, cần đưa xe vào gara.
- Áp suất lốp thấp.
- ABS: phanh thường vẫn dùng được nhưng không còn chống bó cứng.

## Khi đèn đỏ sáng
- Dừng xe ở nơi an toàn, tắt máy, gửi Báo cáo sự cố kèm ảnh bảng đồng hồ.""",
    },
    {
        "category": "vehicle_manual",
        "title": "Chu kỳ thay dầu và lọc dầu",
        "content": """# Chu kỳ thay dầu và lọc dầu

## Chu kỳ tham khảo
- Dầu máy: mỗi 5.000–10.000 km tùy loại dầu và điều kiện chạy; xe chạy nội thành nhiều nên thay sớm hơn.
- Lọc dầu: thay cùng lúc với dầu máy hoặc cách một lần thay dầu.

## Theo dõi trên hệ thống
- Lịch thay dầu được tạo trong mục Bảo trì, hẹn theo ngày hoặc theo số km.
- Hệ thống nhắc trước khi tới hạn; làm xong, tài xế bấm "Báo đã xong" kèm ảnh hoá đơn.

## Dấu hiệu cần thay sớm
- Dầu đen đặc, mức dầu tụt nhanh, đèn áp suất dầu nhấp nháy.""",
    },
    {
        "category": "vehicle_manual",
        "title": "Bảo dưỡng hệ thống phanh",
        "content": """# Bảo dưỡng hệ thống phanh

## Dấu hiệu má phanh mòn
- Tiếng rít kim loại khi phanh.
- Bàn đạp phanh sâu hơn bình thường, xe bị lệch khi phanh.

## Định kỳ
- Kiểm tra má phanh mỗi 10.000 km.
- Thay dầu phanh khoảng 2 năm một lần vì dầu hút ẩm theo thời gian.

## Xuống dốc dài
- Dùng số thấp và phanh động cơ, tránh rà phanh liên tục gây cháy má phanh.""",
    },
    {
        "category": "vehicle_manual",
        "title": "Chăm sóc ắc quy",
        "content": """# Chăm sóc ắc quy

## Dấu hiệu ắc quy yếu
- Đề máy khó, đèn pha mờ khi nổ máy.
- Cọc bình có lớp bột trắng xanh bám quanh.

## Cách kéo dài tuổi thọ
- Không để đèn, điều hòa chạy khi tắt máy.
- Xe để lâu không chạy, nổ máy ít nhất 15 phút mỗi tuần.
- Ắc quy thường dùng được 2–3 năm, thay sớm hơn nếu xe hay chạy quãng ngắn.

## Kích bình
- Nối dây đỏ vào cực dương hai bình trước, dây đen nối mát sau; tháo theo thứ tự ngược lại.""",
    },
]
