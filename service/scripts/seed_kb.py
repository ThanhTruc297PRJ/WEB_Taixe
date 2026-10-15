"""Seed KB — nhập hàng loạt tài liệu mẫu vào cơ sở tri thức.

Cách chạy (backend phải đang chạy):
    cd service
    python scripts/seed_kb.py --token <ADMIN_ID_TOKEN>

Lấy token: DevTools → Application → IndexedDB → firebaseLocalStorage → idToken
hoặc dùng: python scripts/seed_kb.py --email admin@... --password ...
"""

import argparse
import json
import sys
import urllib.request

BASE_URL = "http://localhost:8000"

DOCUMENTS = [
    # ─── AN TOÀN LÁI XE ───────────────────────────────────────────────────
    {
        "title": "Xử lý buồn ngủ khi lái xe",
        "category": "safety",
        "content": """## Dấu hiệu buồn ngủ nguy hiểm
- Mắt nặng, chớp mắt liên tục, khó giữ mắt mở
- Đầu gật hoặc gật đầu đột ngột
- Khó nhớ vài km vừa chạy qua
- Lái xe ra khỏi làn đường không kiểm soát
- Bỏ lỡ biển báo hoặc lối ra cao tốc

## Xử lý ngay khi buồn ngủ
- Dừng xe ngay tại nơi an toàn (trạm nghỉ, bãi đỗ xe)
- Ngủ ngắn 15–20 phút — hiệu quả nhất
- Uống cà phê TRƯỚC khi ngủ ngắn (caffeine có tác dụng sau 20 phút)
- Không cố lái tiếp vì nghĩ "sắp tới nơi rồi"
- Gọi người thay thế lái nếu có thể

## Phòng ngừa buồn ngủ khi lái xe đường dài
- Ngủ đủ 7–8 tiếng trước chuyến đi dài
- Tránh lái xe từ 2–5 giờ sáng và 13–15 giờ chiều (đỉnh buồn ngủ)
- Dừng nghỉ mỗi 2 tiếng hoặc sau 200 km
- Không dùng thuốc gây buồn ngủ trước khi lái
- Giữ xe thoáng mát, không để quá ấm

## Những biện pháp KHÔNG hiệu quả
- Bật nhạc to, mở cửa sổ: chỉ tác dụng vài phút
- Uống nhiều nước lạnh: không đủ
- Dựa vào ý chí: buồn ngủ là phản xạ sinh lý, không cưỡng được
""",
    },
    {
        "title": "Sơ cứu khi gặp tai nạn giao thông",
        "category": "safety",
        "content": """## Nguyên tắc chung khi có tai nạn
- Không hoảng loạn — hít thở sâu và hành động bình tĩnh
- Gọi 115 (cấp cứu) ngay lập tức, cung cấp vị trí chính xác
- Không di chuyển nạn nhân trừ khi có nguy cơ cháy nổ hoặc đuối nước
- Bảo vệ hiện trường: bật đèn cảnh báo, đặt tam giác phản quang

## Bước 1 — Đảm bảo an toàn hiện trường
- Tắt máy xe, kéo phanh tay
- Đặt tam giác cảnh báo phía sau 50–100m
- Bật đèn khẩn cấp (hazard)
- Kêu gọi người xung quanh hỗ trợ

## Bước 2 — Kiểm tra nạn nhân
- Kiểm tra nạn nhân có tỉnh táo không (gọi tên, lay nhẹ vai)
- Kiểm tra hơi thở (quan sát ngực phồng/xẹp, áp má gần miệng)
- Kiểm tra mạch cổ tay hoặc cổ
- Nếu bất tỉnh, không thở → lập tức hồi sinh tim phổi (CPR)

## Bước 3 — Hồi sinh tim phổi (CPR) cơ bản
- Đặt nạn nhân nằm ngửa trên mặt phẳng cứng
- Ép tim: 2 tay chồng nhau ép giữa ngực, sâu 5–6 cm, 100–120 lần/phút
- Thổi ngạt: 30 lần ép tim → 2 lần thổi ngạt
- Tiếp tục đến khi xe cấp cứu tới

## Bước 4 — Cầm máu
- Dùng vải sạch hoặc băng gạc ép trực tiếp lên vết thương
- Giữ áp lực liên tục ít nhất 10 phút, không nhấc ra kiểm tra
- Nâng cao chi bị thương nếu có thể
- Không dùng garo trừ khi máu không cầm được

## Bước 5 — Xử lý chấn thương cột sống nghi ngờ
- Không xoay, nghiêng hoặc di chuyển đầu/cổ nạn nhân
- Giữ đầu thẳng hàng với cột sống
- Chờ xe cấp cứu có thiết bị cố định chuyên dụng
""",
    },
    {
        "title": "Lái xe an toàn trong điều kiện thời tiết xấu",
        "category": "safety",
        "content": """## Lái xe khi trời mưa lớn
- Giảm tốc độ 20–30% so với điều kiện bình thường
- Tăng khoảng cách với xe phía trước lên gấp đôi
- Bật đèn pha (không bật đèn sương mù khi trời chỉ mưa)
- Tránh phanh gấp — nhả ga từ từ trước khi vào cua
- Nếu xe bị aquaplaning (trượt nước): nhả ga, giữ thẳng vô lăng, không phanh

## Lái xe khi có sương mù
- Bật đèn sương mù trước và sau
- Tốc độ tối đa 40 km/h khi tầm nhìn dưới 50m
- Không nhìn vào ánh đèn xe ngược chiều
- Đi sát lề phải, theo vạch kẻ đường
- Sử dụng còi khi vào cua mù

## Lái xe ban đêm
- Kiểm tra đèn pha, đèn hậu trước khi xuất phát
- Chuyển sang đèn cốt khi gặp xe ngược chiều (cách 150m)
- Giảm tốc độ 10–20% so với ban ngày
- Chú ý người đi bộ và xe đạp không có đèn
- Không nhìn thẳng vào đèn pha xe ngược chiều

## Xử lý khi nổ lốp khi đang chạy
- Không phanh gấp — giữ vô lăng thật chắc
- Nhả ga từ từ, để xe giảm tốc tự nhiên
- Lái xe ra lề đường, bật đèn khẩn cấp
- Thay lốp dự phòng tại nơi an toàn
""",
    },
    {
        "title": "Phòng ngừa mất tập trung khi lái xe",
        "category": "safety",
        "content": """## Các nguyên nhân mất tập trung phổ biến
- Sử dụng điện thoại (nhắn tin, gọi điện, xem bản đồ)
- Ăn uống khi đang lái
- Nói chuyện với hành khách quá chú tâm
- Điều chỉnh radio, điều hoà, GPS
- Mơ màng, suy nghĩ không liên quan đến lái xe

## Quy định sử dụng điện thoại khi lái xe
- Nghiêm cấm cầm điện thoại khi lái xe (phạt 800.000 – 1.000.000đ)
- Được phép dùng tai nghe không dây HOẶC loa ngoài
- Cài đặt chế độ "Không làm phiền khi lái xe" trên điện thoại
- Dừng xe ở nơi an toàn nếu cần đọc/gửi tin nhắn

## Kỹ thuật duy trì tập trung
- Quét mắt liên tục: gương chiếu hậu mỗi 5–8 giây
- Nhìn xa phía trước 12–15 giây (khoảng 200–300m)
- Kiểm tra điểm mù trước khi chuyển làn
- Nói tên đường/hướng đi để não luôn hoạt động

## Khi phát hiện mình đang mất tập trung
- Nhận ra và nhắc nhở bản thân ngay
- Dừng mọi hoạt động phụ
- Nếu cần thiết, dừng xe an toàn để xử lý
""",
    },
    # ─── LUẬT GIAO THÔNG ──────────────────────────────────────────────────
    {
        "title": "Giới hạn tốc độ và quy định làn đường",
        "category": "traffic_law",
        "content": """## Giới hạn tốc độ theo loại đường
- Đường cao tốc: tối đa 120 km/h (xe tải 100 km/h)
- Quốc lộ ngoài đô thị: tối đa 90 km/h
- Đường đô thị: tối đa 60 km/h
- Khu dân cư, trường học, bệnh viện: tối đa 40 km/h
- Tối thiểu trên cao tốc: 60 km/h

## Mức phạt vi phạm tốc độ (Nghị định 100/2019 sửa đổi)
- Vượt quá 5–10 km/h: phạt 800.000 – 1.000.000đ
- Vượt quá 10–20 km/h: phạt 3.000.000 – 5.000.000đ
- Vượt quá 20–35 km/h: phạt 5.000.000 – 8.000.000đ
- Vượt quá 35 km/h: phạt 10.000.000 – 12.000.000đ + tước bằng 2–4 tháng

## Quy định sử dụng làn đường
- Đi về phía tay phải, nhường làn trái cho xe vượt
- Xe tải nặng, xe khách giường nằm chỉ được đi 2 làn ngoài cùng bên phải
- Không đi vào làn ngược chiều trừ khi vượt xe và đảm bảo an toàn
- Chuyển làn phải bật xi-nhan trước ít nhất 30m

## Quy định về khoảng cách an toàn
- Tốc độ 60 km/h: khoảng cách tối thiểu 35m
- Tốc độ 80 km/h: tối thiểu 55m
- Tốc độ 100 km/h: tối thiểu 70m
- Tốc độ 120 km/h: tối thiểu 100m
""",
    },
    {
        "title": "Quy định về nồng độ cồn và ma túy khi lái xe",
        "category": "traffic_law",
        "content": """## Quy định nồng độ cồn (Luật Phòng chống tác hại rượu bia 2019)
- Nghiêm cấm hoàn toàn lái xe khi có nồng độ cồn trong máu/khí thở
- Mức 0 — không được có bất kỳ nồng độ cồn nào

## Mức phạt vi phạm nồng độ cồn
- Mức 1 (0–0,25 mg/l khí thở): phạt 6.000.000 – 8.000.000đ, tước bằng 10–12 tháng
- Mức 2 (0,25–0,4 mg/l): phạt 16.000.000 – 18.000.000đ, tước bằng 16–18 tháng
- Mức 3 (>0,4 mg/l): phạt 30.000.000 – 40.000.000đ, tước bằng 22–24 tháng
- Tái phạm hoặc gây tai nạn: có thể bị truy cứu hình sự

## Các loại đồ uống có cồn thường gặp
- Bia lon 330ml (5%): khoảng 0,33 đơn vị cồn
- Rượu vang 150ml (12%): khoảng 1,4 đơn vị cồn
- Rượu mạnh 30ml (40%): khoảng 1 đơn vị cồn
- Cơ thể phân giải khoảng 1 đơn vị cồn/giờ

## Quy định về ma túy
- Nghiêm cấm điều khiển phương tiện khi dùng chất ma túy
- Xét nghiệm nước tiểu/máu khi bị kiểm tra
- Vi phạm: phạt tối đa 40 triệu đồng + tước bằng vĩnh viễn + truy tố hình sự

## Lời khuyên thực tế
- Không lái xe sau khi uống dù chỉ 1 lon bia
- Chỉ định sẵn người lái thay hoặc đi taxi khi có kế hoạch uống
- Dùng ứng dụng gọi xe nếu đã uống
""",
    },
    {
        "title": "Quy tắc ưu tiên và nhường đường",
        "category": "traffic_law",
        "content": """## Thứ tự ưu tiên tại giao lộ không có đèn
1. Xe ưu tiên (cấp cứu, cảnh sát, cứu hỏa, quân sự có còi hú)
2. Xe đến từ bên phải (quy tắc bên phải)
3. Xe đang đi trên đường chính (đường ưu tiên có biển báo)
4. Xe rẽ nhường xe đi thẳng

## Ưu tiên xe đặc biệt
- Khi nghe còi hú hoặc thấy đèn ưu tiên: dạt ngay sang lề phải
- Không vượt xe ưu tiên đang chạy nhiệm vụ
- Xe cấp cứu: 115 | Cảnh sát: 113 | Cứu hỏa: 114

## Quy định nhường đường cho người đi bộ
- Người đi bộ được ưu tiên tại vạch sang đường
- Xe phải dừng hoặc giảm tốc khi người đi bộ đang sang
- Phạt 400.000 – 600.000đ nếu không nhường người đi bộ tại vạch

## Quy định vượt xe
- Chỉ vượt khi đường thẳng, tầm nhìn xa, không có biển cấm vượt
- Bật xi-nhan trái, kiểm tra gương và điểm mù
- Vượt xong trở về làn phải, không cắt đầu xe bị vượt
- Không vượt tại ngã tư, cầu hẹp, đoạn cong, đỉnh dốc
""",
    },
    # ─── CẨM NANG XE ──────────────────────────────────────────────────────
    {
        "title": "Kiểm tra xe trước khi xuất phát",
        "category": "vehicle_manual",
        "content": """## Kiểm tra nhanh hàng ngày (5 phút)
- **Lốp xe**: nhìn qua 4 bánh xem có xẹp, nứt, vật lạ không
- **Đèn**: bật đèn pha, đèn hậu, xi-nhan kiểm tra
- **Gương chiếu hậu**: điều chỉnh đúng góc nhìn
- **Nước rửa kính**: kiểm tra bình, bổ sung nếu cần
- **Xăng/điện**: kiểm tra mức nhiên liệu

## Kiểm tra hàng tuần
- **Áp suất lốp**: xe con 30–35 PSI, kiểm tra cả lốp dự phòng
- **Dầu máy**: rút que thăm dầu, mức giữa MIN và MAX, màu vàng nâu là OK
- **Nước làm mát**: kiểm tra bình chứa phụ, mức giữa MIN–MAX
- **Dầu phanh**: bình trong suốt bên cạnh vô lăng, mức không dưới MIN
- **Ắc quy**: kiểm tra đầu cực không bị oxy hóa (bột trắng)

## Dấu hiệu xe cần đưa vào gara ngay
- Đèn cảnh báo động cơ (check engine) bật
- Tiếng kêu lạ khi phanh (két, cọ) hoặc khi vào cua
- Xe bị kéo lệch sang một bên khi chạy thẳng
- Khói từ khoang máy hoặc ống xả màu trắng/đen bất thường
- Vô lăng rung khi đạt tốc độ nhất định

## Kiểm tra định kỳ theo km
- 5.000 km: thay dầu máy và lọc dầu
- 10.000 km: kiểm tra phanh, lọc gió
- 20.000 km: thay bugi, kiểm tra dây curoa
- 40.000 km: thay lọc nhiên liệu
- 60.000 km: kiểm tra hộp số, thay dầu hộp số
""",
    },
    {
        "title": "Xử lý sự cố thường gặp trên đường",
        "category": "vehicle_manual",
        "content": """## Xe bị hết xăng giữa đường
- Đưa xe vào lề phải, bật đèn khẩn cấp
- Đặt tam giác cảnh báo phía sau
- Gọi dịch vụ cứu hộ hoặc mua xăng can nhỏ
- Không đẩy xe trên cao tốc

## Nổ lốp khi đang chạy
- Không phanh gấp, giữ chắc vô lăng
- Nhả ga từ từ, để xe giảm tốc tự nhiên
- Lái xe ra lề đường, bật đèn khẩn cấp
- Thay lốp dự phòng tại nơi an toàn, xa làn xe chạy

## Xe bị quá nhiệt (đồng hồ nhiệt độ đỏ)
- Tắt điều hoà ngay lập tức
- Dừng xe, tắt máy, không mở nắp capo ngay (bỏng hơi nước)
- Chờ 30 phút cho nguội, mở cẩn thận bằng khăn dày
- Không đổ nước lạnh vào khi máy còn nóng
- Gọi cứu hộ nếu không xử lý được

## Xe không nổ máy (ắc quy yếu)
- Dùng dây kích bình từ xe khác (kẹp đỏ-dương, đen-âm)
- Nổ máy xe có bình đầy trước, sau đó nổ xe hết bình
- Chạy xe 20–30 phút để sạc lại ắc quy
- Thay ắc quy mới nếu liên tục xảy ra

## Phanh không ăn / bàn đạp phanh mềm
- Không hoảng loạn, giảm tốc bằng cách nhả ga
- Đạp phanh nhiều lần liên tiếp để tăng áp dầu
- Kéo phanh tay từ từ để hỗ trợ dừng xe
- Chuyển số thấp để tận dụng phanh động cơ
- Tìm nơi thoát khẩn (lề đất, dải phân cách mềm) nếu không dừng được
""",
    },
    {
        "title": "Bảo dưỡng xe định kỳ và tiết kiệm nhiên liệu",
        "category": "vehicle_manual",
        "content": """## Lịch bảo dưỡng định kỳ
- **5.000 km hoặc 3 tháng**: thay dầu máy, kiểm tra phanh, lốp
- **10.000 km hoặc 6 tháng**: thay lọc dầu, lọc gió, kiểm tra ắc quy
- **20.000 km hoặc 1 năm**: thay bugi, kiểm tra hệ thống làm mát
- **40.000 km**: thay lọc nhiên liệu, kiểm tra dây curoa cam
- **60.000 km**: thay dầu hộp số, kiểm tra hệ thống treo

## Kỹ thuật lái xe tiết kiệm nhiên liệu
- Tăng tốc từ từ, tránh đạp ga đột ngột
- Duy trì tốc độ đều (cruise control nếu có)
- Đoán trước tình huống để nhả ga sớm thay vì phanh gấp
- Tắt máy khi dừng quá 1 phút (không phải ở đèn đỏ ngắn)
- Kiểm tra áp suất lốp đúng — lốp xẹp tốn nhiên liệu hơn 3%

## Các thói quen làm hỏng xe nhanh
- Đỗ xe quá lâu khi máy lạnh chưa ấm (nên chờ 30–60 giây)
- Đổ đầy bình xăng quá mức
- Không thay dầu đúng hạn — dầu bẩn mài mòn động cơ
- Đi số thấp ở tốc độ cao — hỏng hộp số
- Phanh tay chưa nhả hết khi lái — mòn má phanh

## Cách đọc đồng hồ cảnh báo xe
- 🔴 Dầu máy: dừng ngay, tắt máy, kiểm tra mức dầu
- 🌡️ Nhiệt độ: quá nhiệt — dừng xe, tắt điều hoà
- 🔋 Ắc quy: không sạc được — kiểm tra máy phát điện
- ⚙️ Check engine: đến gara kiểm tra sớm
- 💡 TPMS (áp suất lốp): bơm lốp ngay khi có thể
""",
    },
    # ─── LUẬT GIAO THÔNG VIỆT NAM MỞ RỘNG ───────────────────────────────
    {
        "title": "Tín hiệu đèn giao thông và biển báo cơ bản",
        "category": "traffic_law",
        "content": """## Ý nghĩa đèn tín hiệu giao thông
- **Đèn xanh**: được đi, nhưng vẫn phải nhường người đi bộ và xe ưu tiên
- **Đèn vàng**: chuẩn bị dừng; chỉ tiếp tục nếu không thể dừng an toàn
- **Đèn đỏ**: dừng lại hoàn toàn trước vạch dừng xe
- **Đèn xanh nhấp nháy**: sắp chuyển vàng, chuẩn bị giảm tốc
- **Đèn vàng nhấp nháy**: cảnh báo nguy hiểm, đi thận trọng

## Đèn mũi tên
- Mũi tên xanh: được đi theo hướng mũi tên chỉ
- Mũi tên đỏ: không được đi theo hướng đó dù đèn chính xanh
- Rẽ phải khi đèn đỏ: chỉ được phép khi có biển cho phép rẽ phải

## Nhóm biển báo theo màu sắc và hình dạng
- **Biển tròn viền đỏ nền trắng**: cấm (cấm đi ngược chiều, cấm vượt...)
- **Biển tròn nền xanh**: lệnh bắt buộc (phải rẽ trái/phải, chỉ đi thẳng...)
- **Biển tam giác viền đỏ**: nguy hiểm, cảnh báo (đường cong, dốc, giao lộ...)
- **Biển chữ nhật xanh lam**: chỉ dẫn (hướng đi, tên đường, khoảng cách...)
- **Biển chữ nhật nền vàng**: công trường thi công, cảnh báo tạm thời

## Một số biển cấm quan trọng
- Biển 102: cấm đi ngược chiều
- Biển 106: cấm vượt xe
- Biển 112: cấm dừng, đỗ xe
- Biển 127: giới hạn tốc độ tối đa
- Biển 130: cấm sử dụng còi

## Vạch kẻ đường
- Vạch liền đơn hoặc đôi: không được vượt, không được đè vạch
- Vạch đứt: được phép vượt khi an toàn
- Vạch dừng xe: dừng trước vạch khi đèn đỏ
- Vạch sang đường (vằn vằn): nhường người đi bộ hoàn toàn
""",
    },
    {
        "title": "Quy định dừng xe và đỗ xe",
        "category": "traffic_law",
        "content": """## Phân biệt dừng xe và đỗ xe
- **Dừng xe**: tạm thời, người lái không rời xe, thời gian ngắn
- **Đỗ xe**: để xe không có người lái hoặc trong thời gian dài

## Nơi bị cấm dừng, đỗ xe
- Trên phần đường xe chạy (trừ khi khẩn cấp)
- Trong hầm đường bộ
- Trên cầu (trừ cầu cho phép đỗ xe)
- Nơi đường bộ giao nhau và trong phạm vi 5m từ điểm giao nhau
- Ngay trước và sau đường ngang qua đường sắt
- Nơi có biển cấm dừng, cấm đỗ
- Gần cửa ra vào của công trình, bệnh viện, trường học
- Trước miệng cống thoát nước, ổ gà, điểm lên xuống xe bus
- Cách hydrant chữa cháy dưới 5m

## Quy định đỗ xe đúng
- Đỗ sát lề đường bên phải, cách lề tối đa 0,25m
- Bật đèn nháy khi dừng đỗ trên đường ban đêm
- Không đỗ che khuất tầm nhìn giao lộ
- Kéo phanh tay, chèn bánh nếu đỗ trên dốc

## Mức phạt vi phạm dừng đỗ xe
- Dừng không đúng nơi quy định: 400.000 – 600.000đ
- Đỗ xe trên cầu: 600.000 – 800.000đ
- Đỗ trong hầm, trên đường cao tốc: 3.000.000 – 5.000.000đ
- Che khuất biển báo, đèn tín hiệu: 1.000.000 – 2.000.000đ
""",
    },
    {
        "title": "Quy định về giấy tờ xe và bằng lái xe",
        "category": "traffic_law",
        "content": """## Giấy tờ bắt buộc khi lái xe
1. **Giấy phép lái xe (GPLX)** còn hiệu lực, đúng hạng
2. **Giấy đăng ký xe** (bản gốc hoặc bản sao công chứng)
3. **Giấy chứng nhận kiểm định an toàn kỹ thuật** còn hạn
4. **Giấy chứng nhận bảo hiểm TNDS** bắt buộc còn hạn

## Các hạng bằng lái xe ô tô
- **Hạng B1**: xe không kinh doanh vận tải dưới 9 chỗ, dưới 3,5 tấn
- **Hạng B2**: xe kinh doanh vận tải dưới 9 chỗ, dưới 3,5 tấn
- **Hạng C**: xe tải từ 3,5 tấn trở lên (không kéo rơ moóc)
- **Hạng D**: xe khách từ 10–30 chỗ
- **Hạng E**: xe khách trên 30 chỗ
- **Hạng FC**: xe tải kéo rơ moóc
- **Hạng FD, FE**: xe khách kéo rơ moóc

## Điều kiện cấp bằng lái xe
- Đủ 18 tuổi (hạng B1, B2), 21 tuổi (hạng C, D), 24 tuổi (hạng E)
- Đủ sức khoẻ theo quy định
- Hoàn thành khoá học lý thuyết và thực hành
- Đạt kỳ thi sát hạch

## Gia hạn và đổi bằng lái
- Bằng B1 cấp lần đầu có hạn 10 năm, gia hạn thêm 10 năm
- Bằng B2, C, D, E: thời hạn 5 năm, gia hạn định kỳ
- Đổi bằng quốc tế: cần có bằng trong nước còn hạn + hồ sơ tại Sở GTVT

## Mức phạt vi phạm giấy tờ
- Không mang GPLX: 200.000 – 400.000đ (cảnh cáo hoặc phạt tiền)
- GPLX hết hạn: 800.000 – 1.200.000đ
- Không có GPLX (chưa thi): 10.000.000 – 12.000.000đ + tạm giữ xe
- Không có đăng ký xe: 400.000 – 600.000đ
- Không có bảo hiểm: 400.000 – 600.000đ
""",
    },
    {
        "title": "Quy định trên đường cao tốc",
        "category": "traffic_law",
        "content": """## Điều kiện phương tiện được vào cao tốc
- Xe cơ giới đủ điều kiện an toàn kỹ thuật
- Xe máy, xe 3 bánh, xe thô sơ KHÔNG được đi cao tốc
- Xe tải chở hàng siêu trường, siêu trọng cần giấy phép đặc biệt

## Tốc độ trên cao tốc
- Tốc độ tối đa: 120 km/h (đoạn cho phép), thông thường 100 km/h
- Tốc độ tối thiểu: 60 km/h
- Xe tải trên 3,5 tấn, xe khách trên 30 chỗ: tối đa 100 km/h
- Khi trời mưa, tầm nhìn kém: giảm 20% tốc độ quy định

## Quy tắc làn đường cao tốc
- Làn ngoài cùng bên trái: dành cho xe vượt, không đi liên tục
- Xe tải nặng, xe khách lớn: chỉ đi 2 làn ngoài cùng bên phải
- Không được đi ngược chiều, quay đầu, lùi xe trên cao tốc
- Không được đỗ xe trên làn chạy (trừ khẩn cấp)

## Khi gặp sự cố trên cao tốc
- Đưa xe vào làn dừng khẩn cấp (lề đường bên phải)
- Bật đèn khẩn cấp ngay lập tức
- Đặt tam giác cảnh báo phía sau ít nhất 150m
- Người và hành khách thoát khỏi xe, đứng sau rào chắn
- Gọi đường dây hỗ trợ cao tốc hoặc 113

## Mức phạt vi phạm đặc thù trên cao tốc
- Đi ngược chiều: 16.000.000 – 18.000.000đ + tước bằng 2–4 tháng
- Quay đầu, lùi xe: 16.000.000 – 18.000.000đ
- Đỗ xe không đúng nơi: 3.000.000 – 5.000.000đ
- Đi vào làn dừng khẩn cấp không có lý do: 1.000.000 – 2.000.000đ
- Đi dưới tốc độ tối thiểu 60 km/h: 800.000 – 1.000.000đ
""",
    },
    {
        "title": "Quy định vượt xe và chuyển làn",
        "category": "traffic_law",
        "content": """## Điều kiện được phép vượt xe
- Đường đủ rộng, tầm nhìn phía trước ít nhất 200m
- Không có biển cấm vượt
- Xe phía trước không có tín hiệu vượt xe khác
- Không có xe ngược chiều trong khoảng cách nguy hiểm
- Vạch kẻ đường là vạch đứt (được phép vượt)

## Nơi bị cấm vượt xe
- Gần đỉnh dốc, khúc cua, nơi tầm nhìn bị che khuất
- Tại giao lộ, ngã tư, vòng xuyến
- Khi qua cầu hẹp, hầm đường bộ
- Khu vực đường sắt giao nhau
- Nơi có biển cấm vượt
- Gần trường học, bệnh viện đang giờ cao điểm

## Thủ tục vượt xe đúng luật
1. Kiểm tra gương chiếu hậu và điểm mù
2. Bật xi-nhan trái báo hiệu
3. Chuyển sang làn trái
4. Tăng tốc vượt qua xe phía trước
5. Bật xi-nhan phải, chuyển về làn phải
6. Tắt xi-nhan sau khi về làn

## Quy định chuyển làn
- Bật xi-nhan ít nhất 30m trước khi chuyển làn
- Kiểm tra gương và quay đầu kiểm tra điểm mù
- Không chuyển nhiều làn cùng lúc
- Không chuyển làn tại giao lộ

## Mức phạt
- Vượt xe nơi có biển cấm: 3.000.000 – 5.000.000đ
- Vượt xe tại đường ngang qua đường sắt: 3.000.000 – 5.000.000đ
- Không bật xi-nhan khi chuyển làn: 400.000 – 600.000đ
- Chuyển làn không đúng quy định: 800.000 – 1.000.000đ
""",
    },
    {
        "title": "Quy định tải trọng xe và vận chuyển hàng hoá",
        "category": "traffic_law",
        "content": """## Tải trọng cho phép
- Xe con (dưới 9 chỗ): chở đúng số người ghi trên đăng ký
- Xe tải: không vượt tải trọng ghi trên đăng ký
- Trục xe đơn: tối đa 10 tấn/trục
- Trục xe đôi: tối đa 18 tấn/trục đôi
- Xe quá khổ, quá tải: phải có giấy phép lưu hành đặc biệt

## Quy định chở hàng
- Hàng hoá phải được chằng buộc chắc chắn, không rơi vãi
- Không chở hàng vượt quá thùng xe về chiều cao/chiều rộng
- Hàng hoá cồng kềnh nhô ra sau: phải có cờ đỏ ban ngày, đèn đỏ ban đêm
- Không chở hàng hoá nguy hiểm mà không có giấy phép

## Hạn chế xe tải theo giờ ở đô thị
- Nội thành TP.HCM, Hà Nội: xe tải trên 2,5 tấn bị hạn chế giờ lưu thông
- Thường cấm 6h–9h và 16h–20h hàng ngày
- Kiểm tra biển báo hoặc quyết định của địa phương

## Mức phạt vi phạm tải trọng
- Vượt tải trọng 10–20%: 3.000.000 – 5.000.000đ
- Vượt tải trọng 20–50%: 7.000.000 – 8.000.000đ
- Vượt tải trọng trên 50%: 14.000.000 – 16.000.000đ + tạm giữ xe
- Hàng rơi vãi xuống đường: 1.000.000 – 2.000.000đ
""",
    },
    {
        "title": "Quy định qua đường sắt và phà, cầu phao",
        "category": "traffic_law",
        "content": """## Quy định qua đường ngang giao nhau với đường sắt
- Phải dừng lại khi đèn đỏ hoặc cần chắn đang đóng/hạ
- Quan sát kỹ 2 phía đường sắt trước khi qua
- Không được dừng đỗ trên đường sắt hoặc trong phạm vi 5m
- Qua đường sắt phải đi nhanh, không dừng giữa đường ray

## Thứ tự ưu tiên tại đường ngang
1. Tàu hoả luôn có quyền ưu tiên tuyệt đối
2. Xe cộ phải nhường hoàn toàn
3. Không vượt qua khi cần chắn đang đóng

## Khi gặp sự cố trên đường sắt
- Tắt máy, đẩy xe ra khỏi đường ray ngay lập tức
- Gọi đường dây khẩn cấp đường sắt: 1800 599 933
- Phất tay ra hiệu cho tàu hoả từ xa nếu có thể

## Quy định qua phà, cầu phao
- Xếp hàng theo thứ tự, không chen lấn
- Tắt máy khi xe trên phà (trừ khi có chỉ dẫn khác)
- Không để xe số tự do trên phà
- Chú ý biển báo tải trọng tối đa của cầu/phà
- Không dừng đỗ giữa cầu phao khi không cần thiết

## Mức phạt
- Không dừng khi đèn đỏ tại đường ngang: 3.000.000 – 5.000.000đ + tước bằng 1–3 tháng
- Vượt qua khi cần chắn đang đóng: 7.000.000 – 8.000.000đ + tước bằng 2–4 tháng
- Dừng đỗ trong phạm vi đường sắt: 1.000.000 – 2.000.000đ
""",
    },
    {
        "title": "Quy định sử dụng đèn xe và còi xe",
        "category": "traffic_law",
        "content": """## Quy định sử dụng đèn pha và đèn cốt
- Ban đêm và khi tầm nhìn dưới 100m: bật đèn pha hoặc đèn cốt
- Trong hầm đường bộ: luôn bật đèn
- Gặp xe ngược chiều trong khoảng cách 150m: chuyển sang đèn cốt
- Khi theo sau xe khác gần: dùng đèn cốt, không pha vào gương xe trước
- Ban ngày trong điều kiện bình thường: không bắt buộc bật đèn pha

## Đèn xi-nhan (đèn báo rẽ)
- Bật xi-nhan trước khi rẽ, chuyển làn ít nhất 30m
- Giữ xi-nhan đến khi hoàn thành thao tác
- Tắt xi-nhan ngay sau khi rẽ xong
- Không bật xi-nhan nhầm hướng

## Đèn khẩn cấp (hazard)
- Dùng khi dừng khẩn cấp trên đường, sự cố xe
- Dùng khi di chuyển chậm bất thường
- Không dùng thay xi-nhan khi rẽ

## Quy định sử dụng còi
- Không bấm còi liên tục, không bấm còi hơi trong đô thị
- Được dùng còi khi cần thiết để cảnh báo nguy hiểm
- Cấm dùng còi từ 22h–5h trong khu dân cư
- Còi hơi chỉ được dùng trên đường ngoài đô thị

## Mức phạt
- Không bật đèn ban đêm: 400.000 – 600.000đ
- Dùng đèn pha chiếu thẳng vào xe ngược chiều: 800.000 – 1.000.000đ
- Bấm còi liên tục trong đô thị: 400.000 – 600.000đ
- Bấm còi hơi trong thành phố: 1.000.000 – 2.000.000đ
""",
    },
    {
        "title": "Quy định về bảo hiểm xe và đăng kiểm",
        "category": "traffic_law",
        "content": """## Bảo hiểm trách nhiệm dân sự (TNDS) bắt buộc
- Tất cả xe cơ giới tham gia giao thông phải có bảo hiểm TNDS
- Mua tại các công ty bảo hiểm được Bộ Tài chính cấp phép
- Thời hạn: 1 năm (có thể mua nhiều năm)
- Mức bồi thường tối đa: 150 triệu đồng/người (thương tật/tử vong)
- Thiệt hại tài sản: tối đa 100 triệu đồng/vụ

## Kiểm định an toàn kỹ thuật (đăng kiểm)
- Xe con mới: kiểm định lần đầu sau 3 năm kể từ ngày sản xuất
- Sau đó: mỗi 2 năm/lần (xe dưới 7 chỗ không kinh doanh)
- Xe kinh doanh vận tải, xe tải: mỗi 6 tháng–1 năm tuỳ loại
- Xe trên 7 năm: kiểm định hàng năm

## Thủ tục đăng kiểm
1. Chuẩn bị: giấy đăng ký xe gốc, bảo hiểm TNDS còn hạn
2. Đến trung tâm đăng kiểm xe (có thể đặt lịch online)
3. Xe được kiểm tra: phanh, đèn, còi, khí thải, kính, gương
4. Đạt: nhận tem kiểm định dán lên kính xe
5. Không đạt: sửa chữa và kiểm định lại trong 30 ngày

## Mức phạt
- Không có bảo hiểm TNDS: 400.000 – 600.000đ
- Quá hạn đăng kiểm: 800.000 – 1.200.000đ
- Quá hạn đăng kiểm trên 6 tháng: 4.000.000 – 6.000.000đ + tạm giữ xe
""",
    },
    {
        "title": "Xử lý vi phạm giao thông và thủ tục nộp phạt",
        "category": "traffic_law",
        "content": """## Quyền và nghĩa vụ khi bị CSGT dừng xe
- Dừng xe ngay khi có hiệu lệnh, đưa xe vào lề phải
- Xuất trình đầy đủ giấy tờ khi được yêu cầu
- Có quyền yêu cầu CSGT xuất trình thẻ công vụ
- Không được tự ý rời đi khi chưa được phép
- Có quyền từ chối ký biên bản nếu không đồng ý (ghi rõ lý do)

## Thủ tục lập biên bản vi phạm
- CSGT lập biên bản vi phạm hành chính
- Tài xế đọc kỹ trước khi ký; ghi "không đồng ý" nếu cần
- Nhận 1 bản biên bản
- Quyết định xử phạt gửi về địa chỉ trong vòng 7 ngày

## Hình thức xử phạt
- **Phạt tiền**: theo mức quy định Nghị định 100/2019 và các sửa đổi
- **Tước GPLX**: có thời hạn (1–6 tháng) hoặc không thời hạn
- **Tạm giữ phương tiện**: tối đa 30 ngày
- **Tịch thu phương tiện**: vi phạm nghiêm trọng, tái phạm nhiều lần

## Cách nộp phạt
1. **Nộp trực tiếp**: tại Kho bạc nhà nước hoặc ngân hàng được uỷ quyền
2. **Nộp online**: qua cổng dịch vụ công quốc gia hoặc app ngân hàng
3. Thời hạn nộp phạt: 10 ngày kể từ ngày nhận quyết định
4. Sau khi nộp: mang biên lai đến cơ quan CSGT để nhận lại giấy tờ/xe

## Khiếu nại quyết định xử phạt
- Khiếu nại lần 1: gửi đến người ra quyết định trong 90 ngày
- Khiếu nại lần 2: gửi đến cấp trên trong 30 ngày kể từ ngày nhận kết quả lần 1
- Hoặc khởi kiện hành chính tại toà án trong 1 năm
""",
    },
    {
        "title": "Quy định giao thông đặc thù ban đêm và thời tiết xấu",
        "category": "traffic_law",
        "content": """## Quy định lái xe ban đêm (18h–6h)
- Bắt buộc bật đèn chiếu sáng phía trước và phía sau
- Giảm tốc độ tối thiểu 10–20% so với ban ngày
- Tăng khoảng cách an toàn tối thiểu 1,5 lần
- Chú ý người đi bộ, xe đạp không có đèn
- Không dùng đèn pha khi đi trong đô thị có đèn đường

## Lái xe khi trời mưa lớn (tầm nhìn dưới 50m)
- Bật đèn sương mù trước và sau (nếu có)
- Tốc độ tối đa 40 km/h, giữ khoảng cách gấp đôi
- Không phanh gấp trên mặt đường ướt
- Nếu không thấy rõ đường: dừng xe ở nơi an toàn, chờ mưa nhỏ hơn

## Lái xe trong sương mù dày đặc
- Giảm tốc độ xuống 20–30 km/h
- Bật đèn sương mù, không bật đèn pha (gây chói ngược)
- Đi sát lề phải, theo vạch kẻ đường
- Bấm còi khi vào đoạn cua, điểm mù
- Nếu tầm nhìn dưới 10m: dừng xe an toàn

## Lái xe trên đường ngập nước
- Chỉ qua khi nước không cao hơn bục phanh (~20–30cm)
- Đi chậm, đều tốc độ, tránh tạo sóng
- Sau khi qua: phanh nhẹ vài lần để làm khô má phanh
- Không tắt máy nếu nước có thể lọt vào ống xả (đặc biệt xe cũ)

## Lái xe trên đường trơn, đóng băng (miền núi)
- Lắp xích tuyết hoặc lốp chuyên dụng nếu có băng
- Giảm tốc độ tối đa 50% so với điều kiện bình thường
- Không phanh gấp, không đánh lái mạnh
- Tăng khoảng cách an toàn gấp 3–4 lần
""",
    },
    {
        "title": "Quy định ưu tiên xe đặc biệt và vận tải công cộng",
        "category": "traffic_law",
        "content": """## Xe được hưởng quyền ưu tiên
1. Xe chữa cháy đang làm nhiệm vụ
2. Xe quân sự, công an đang làm nhiệm vụ khẩn cấp
3. Xe cấp cứu đang thực hiện nhiệm vụ
4. Xe hộ đê, xe cứu nạn thiên tai
5. Đoàn xe có xe hộ tống (dẫn đường)

## Nghĩa vụ của người tham gia giao thông
- Nghe còi hú hoặc thấy đèn ưu tiên nhấp nháy: nhường đường ngay
- Dạt vào lề phải, dừng lại cho xe ưu tiên qua
- Không bám theo xe ưu tiên để tránh đèn đỏ
- Không vượt qua đoàn xe ưu tiên có hộ tống

## Quy định xe buýt và xe khách
- Xe buýt được ưu tiên tại trạm dừng
- Nhường xe buýt khi xe buýt ra khỏi trạm dừng (xe buýt bật xi-nhan)
- Không dừng đỗ trong vùng trạm xe buýt

## Quy định xe tải, xe công trình
- Đèn cảnh báo màu vàng nhấp nháy: xe đang hoạt động đặc biệt
- Giữ khoảng cách xa khi đi sau xe tải lớn (điểm mù lớn)
- Không đi vào điểm mù của xe tải: vị trí ngang hông, phía sau gần

## Mức phạt không nhường xe ưu tiên
- Không nhường đường cho xe ưu tiên có còi hú: 3.000.000 – 5.000.000đ + tước bằng 1–3 tháng
- Bám theo xe ưu tiên qua đèn đỏ: 3.000.000 – 5.000.000đ
""",
    },
    # ─── HƯỚNG DẪN SỬ DỤNG ỨNG DỤNG ─────────────────────────────────────
    {
        "title": "Hướng dẫn đăng ký và đăng nhập tài khoản tài xế",
        "category": "safety",
        "content": """## Đăng ký tài khoản mới
1. Mở ứng dụng Driver Safety Monitor
2. Chọn **"Đăng ký"** trên màn hình chào
3. Nhập đầy đủ: Họ tên, Email, Số điện thoại, Số bằng lái, Mật khẩu
4. Nhấn **"Đăng ký"** — hệ thống gửi email xác thực đến địa chỉ email vừa nhập
5. Mở email, bấm vào link xác thực
6. Quay lại app — trạng thái chuyển sang **"Chờ duyệt"**
7. Chờ quản trị viên duyệt hồ sơ (thường trong 1 ngày làm việc)
8. Khi được duyệt, nhận email thông báo và vào app bình thường

## Đăng nhập
- Nhập email và mật khẩu đã đăng ký
- Nhấn **"Đăng nhập"**
- Nếu quên mật khẩu: chọn **"Quên mật khẩu"** → nhập email → nhận link đặt lại

## Các trạng thái tài khoản
- **Chờ duyệt**: hồ sơ đã gửi, đang chờ admin xem xét
- **Chưa xác thực email**: cần bấm link trong email trước
- **Bị từ chối**: liên hệ công ty để biết lý do
- **Bị khoá**: liên hệ quản lý trực tiếp

## Lưu ý bảo mật
- Không chia sẻ mật khẩu cho người khác
- Đăng xuất khi không sử dụng trên thiết bị chung
- Báo ngay cho công ty nếu mất điện thoại
""",
    },
    {
        "title": "Hướng dẫn gửi báo cáo sự cố và gọi cứu hộ",
        "category": "safety",
        "content": """## Gửi báo cáo sự cố trong ứng dụng
1. Từ màn hình chính, chọn tab **"Báo cáo"** (biểu tượng cờ)
2. Nhập mô tả tình trạng sự cố vào ô văn bản
3. Đính kèm ảnh (tuỳ chọn): chụp ảnh mới hoặc chọn từ thư viện
4. Nhấn **"Gửi Báo Cáo"** — app tự động đính kèm vị trí GPS hiện tại
5. Chờ xác nhận "Đã gửi báo cáo tới công ty"

## Khi nào nên gửi báo cáo
- Xe bị hỏng hóc cần hỗ trợ
- Va chạm hoặc tai nạn giao thông
- Phát hiện tình trạng bất thường trên xe
- Sự cố kỹ thuật cần ghi nhận

## Gọi cứu hộ khẩn cấp (SOS)
Trong màn hình Báo cáo, cuộn xuống phần **"Hỗ trợ khẩn cấp nhanh"**:
- **Cấp cứu 115**: tai nạn có người bị thương
- **Cứu hộ công ty**: số điện thoại cứu hộ của công ty (admin đã cài)
- **CSGT 113**: tai nạn giao thông nghiêm trọng
- **Cứu hỏa 114**: xe bốc cháy

## Lưu ý khi gửi báo cáo
- Đảm bảo có kết nối mạng trước khi gửi
- Ảnh sẽ được nén tự động, không cần lo về dung lượng
- Vị trí GPS được đính kèm tự động nếu đã cấp quyền
- Báo cáo lưu lại vĩnh viễn, admin có thể xem bất cứ lúc nào
""",
    },
    {
        "title": "Hướng dẫn xem nhắc nhở bảo trì và đăng kiểm xe",
        "category": "safety",
        "content": """## Xem lịch bảo trì xe
- Thông báo bảo trì được gửi tự động qua **thông báo đẩy** (push notification)
- Nhắc khi đến hạn bảo trì theo **ngày** hoặc **số km** đã đi
- Ví dụ: "Xe BKS 51A-12345 đến hạn thay dầu (5.000 km)"

## Xem lịch đăng kiểm
- Thông báo đăng kiểm nhắc trước **30 ngày** khi sắp hết hạn
- Nhắc lại vào ngày đến hạn nếu chưa hoàn thành

## Báo hoàn thành bảo trì/đăng kiểm
Khi đã hoàn thành bảo trì hoặc đăng kiểm:
1. Nhận thông báo từ admin giao việc
2. Chụp ảnh biên lai/hoá đơn làm bằng chứng
3. Nhập số km hiện tại và chi phí thực tế
4. Gửi để admin xác nhận

## Nếu không nhận được thông báo
- Kiểm tra quyền thông báo đẩy trong Cài đặt điện thoại
- Kiểm tra kết nối internet
- Liên hệ quản lý để xác nhận thông tin xe đã được nhập đúng

## Lưu ý quan trọng
- Không bỏ qua thông báo bảo trì — ảnh hưởng an toàn lái xe
- Đăng kiểm quá hạn có thể bị xử phạt hành chính
- Báo cáo hoàn thành đúng hạn để tránh nhắc lặp lại
""",
    },
    {
        "title": "Hướng dẫn sử dụng tính năng nhạc và radio trong app",
        "category": "safety",
        "content": """## Nghe nhạc trong ứng dụng
- Tab **"Nhạc"** hiển thị danh sách bài hát do công ty phê duyệt
- Chỉ những bài hát được admin bật mới nghe được
- Bài hát có nội dung không phù hợp sẽ tự động bị ẩn

## Nghe radio
- Tab **"Radio"** hiển thị danh sách kênh radio trực tuyến
- Chọn kênh muốn nghe → nhấn Play
- Radio phát liên tục, không cần thao tác thêm

## Lưu ý an toàn khi nghe nhạc/radio
- Chỉ sử dụng tai nghe một bên khi lái xe
- Âm lượng vừa phải, không quá to để vẫn nghe được còi xe và tín hiệu
- Không thao tác điện thoại để chuyển bài khi đang lái — dừng xe trước
- Tốt nhất: cài bài trước khi xuất phát, để phát tự động

## Nhạc không phát được
- Kiểm tra kết nối mạng (nhạc yêu cầu internet)
- Bài hát có thể đã bị admin tắt — chọn bài khác
- Khởi động lại app nếu vẫn không được
""",
    },
    {
        "title": "Hướng dẫn sử dụng trợ lý AI và hỏi đáp trong app",
        "category": "safety",
        "content": """## Trợ lý AI là gì
- Trợ lý AI giúp tài xế tra cứu thông tin về an toàn lái xe, luật giao thông và bảo trì xe
- Trả lời bằng tiếng Việt, dựa trên cơ sở tri thức của công ty
- Hoạt động 24/7, không cần chờ nhân viên hỗ trợ

## Cách sử dụng trợ lý AI
1. Từ màn hình chính, chọn tab **"Trợ lý"** (biểu tượng robot)
2. Gõ câu hỏi vào ô nhập liệu
3. Nhấn **Gửi** hoặc nhấn Enter
4. Chờ vài giây để trợ lý trả lời

## Các loại câu hỏi trợ lý có thể trả lời
- An toàn lái xe: "Làm gì khi buồn ngủ?", "Xử lý nổ lốp thế nào?"
- Luật giao thông: "Tốc độ tối đa trên cao tốc là bao nhiêu?", "Phạt bao nhiêu khi vượt đèn đỏ?"
- Bảo trì xe: "Bao nhiêu km thì thay dầu?", "Kiểm tra xe trước khi đi như thế nào?"
- Hướng dẫn app: "Cách gửi báo cáo sự cố?", "Làm sao để xem lịch bảo trì?"

## Trợ lý không thể làm
- Chỉ đường hoặc tìm địa điểm (dùng Google Maps)
- Xem thông tin tài khoản cá nhân
- Thay đổi lịch bảo trì hoặc thông tin xe
- Gửi báo cáo thay bạn

## Mẹo đặt câu hỏi hiệu quả
- Hỏi cụ thể: "Cách sơ cứu khi gặp tai nạn" thay vì "tai nạn"
- Dùng tiếng Việt có dấu để trợ lý hiểu chính xác hơn
- Nếu câu trả lời chưa đủ, hỏi thêm chi tiết
""",
    },
    {
        "title": "Hướng dẫn theo dõi hành trình và tính năng giám sát an toàn",
        "category": "safety",
        "content": """## Hệ thống giám sát an toàn hoạt động như thế nào
- App theo dõi trạng thái lái xe trong nền khi tài xế đang trực
- Phát hiện dấu hiệu buồn ngủ qua camera (nếu được bật)
- Ghi nhận sự kiện bất thường và thông báo cho công ty

## Bắt đầu ca lái xe
1. Mở app và đăng nhập
2. App tự động ghi nhận bạn đang online (trạng thái **"Đang lái"**)
3. Khi cần nghỉ: không cần thao tác gì, hệ thống tự nhận diện

## Khi hệ thống phát hiện buồn ngủ
- App rung và phát âm thanh cảnh báo
- Hiển thị thông báo: **"Phát hiện buồn ngủ — Hãy dừng xe nghỉ ngơi"**
- Sự kiện được ghi lại và gửi về công ty kèm đoạn video 10 giây
- Tài xế nên: dừng xe ngay tại nơi an toàn, nghỉ ít nhất 15–20 phút

## Quyền riêng tư và dữ liệu
- Video chỉ được ghi khi phát hiện sự kiện bất thường, không ghi liên tục
- Dữ liệu lưu trên hệ thống công ty, bảo mật
- Tài xế có thể xem lại lịch sử sự kiện của mình

## Cài đặt quyền cần thiết cho app
- **Camera**: cho tính năng phát hiện buồn ngủ
- **Vị trí (GPS)**: cho tính năng đính kèm địa điểm vào báo cáo
- **Thông báo đẩy**: cho nhắc nhở bảo trì và cảnh báo
- **Lưu trữ**: cho phép tải ảnh báo cáo

## Cách cấp quyền
- iOS: Cài đặt → Ứng dụng → Driver Safety Monitor → Quyền
- Android: Cài đặt → Ứng dụng → Driver Safety Monitor → Quyền ứng dụng
""",
    },

    # ─── AN TOÀN LÁI XE BỔ SUNG ──────────────────────────────────────────
    {
        "title": "Lái xe đường dài — quản lý mệt mỏi và sức khoẻ",
        "category": "safety",
        "content": """## Chuẩn bị trước chuyến đi dài
- Ngủ đủ 7–8 tiếng đêm trước chuyến đi
- Không uống rượu bia trong 24 giờ trước
- Ăn nhẹ trước khi xuất phát — không ăn quá no (gây buồn ngủ)
- Kiểm tra xe kỹ: lốp, dầu, nước, phanh, đèn
- Lên kế hoạch dừng nghỉ trước: biết trước vị trí trạm nghỉ

## Lịch nghỉ ngơi khuyến nghị
- Dừng nghỉ mỗi 2 tiếng hoặc sau 200 km
- Mỗi lần nghỉ ít nhất 15–20 phút, ra khỏi xe đi lại
- Chuyến trên 6 tiếng: nghỉ trưa ít nhất 45 phút
- Không lái liên tục quá 4 tiếng

## Dinh dưỡng và nước uống khi lái đường dài
- Uống đủ nước (mất nước gây mệt mỏi và giảm tập trung)
- Ăn nhẹ mỗi 3–4 tiếng: trái cây, hạt, bánh mì — tránh đồ nhiều đường
- Tránh thức ăn nặng, nhiều dầu mỡ giữa chặng
- Caffeine (cà phê, trà) hỗ trợ tỉnh táo nhưng không thay thế được ngủ

## Bài tập giảm mỏi tại trạm nghỉ
- Xoay cổ, xoay vai nhẹ nhàng
- Duỗi chân, đi bộ 5–10 phút
- Ép lưng, xoay hông để giảm đau lưng do ngồi lâu
- Rửa mặt bằng nước lạnh để tỉnh táo

## Dấu hiệu cần dừng nghỉ ngay
- Mắt cay, khó giữ mở
- Không nhớ đoạn đường vừa qua
- Lái xe lạng qua lạng lại không kiểm soát
- Phản xạ chậm hơn bình thường
- Cáu kỉnh, khó chịu không rõ nguyên nhân
""",
    },
    {
        "title": "Kỹ thuật lái xe đường đèo và địa hình miền núi",
        "category": "safety",
        "content": """## Nguyên tắc chung trên đường đèo
- Luôn đi về phía tay phải của đường
- Bấm còi trước khi vào khúc cua mù (khuất tầm nhìn)
- Không dừng xe giữa đèo nếu không khẩn cấp
- Đặc biệt cẩn thận với đường trơn sau mưa hoặc có sương mù

## Kỹ thuật lên dốc
- Chọn số thấp trước khi vào dốc, không tăng số giữa chừng
- Duy trì tốc độ đều, không đạp ga đột ngột
- Nếu xe mất đà: không phanh gấp, chuyển về số thấp hơn
- Không bao giờ lùi xe trên dốc cao

## Kỹ thuật xuống dốc — quan trọng nhất
- Vào số thấp TRƯỚC khi xuống dốc (không vào giữa chừng)
- Để động cơ ghìm tốc độ (engine braking), không đạp phanh liên tục
- Phanh ngắt quãng (nhấn–nhả) thay vì giữ liên tục — tránh quá nhiệt má phanh
- Không ngắt côn (xe số sàn), không về số 0 khi xuống dốc

## Xử lý phanh mất tác dụng trên dốc (brake fade)
- Dấu hiệu: bàn đạp phanh nặng, xe không chậm lại như bình thường
- Xử lý: chuyển ngay về số thấp nhất để ghìm xe
- Tìm lối thoát khẩn (lề đất, taluy dương) để dừng xe
- Sau khi dừng: không tiếp tục cho đến khi phanh nguội (ít nhất 20 phút)

## Tránh xe trên đường hẹp
- Xe đang lên dốc được ưu tiên — xe xuống dốc phải nhường
- Xe nhỏ nhường xe lớn
- Nếu cần lùi: lùi vào chỗ rộng, không lùi dọc theo dốc dài
- Giữ khoảng cách lớn khi đi sau xe tải nặng trên đèo

## Lưu ý đặc biệt
- Kiểm tra phanh kỹ trước khi vào đèo dài
- Dự phòng nước làm mát đầy bình (dễ quá nhiệt trên đèo)
- Không leo đèo lúc sương mù dày, mưa lớn nếu không cần thiết
""",
    },
    {
        "title": "Xử lý hành khách gây rối và lái xe phòng thủ",
        "category": "safety",
        "content": """## Lái xe phòng thủ là gì
Lái xe phòng thủ (defensive driving) là kỹ thuật dự đoán trước nguy hiểm và chủ động tránh tai nạn, kể cả khi lỗi thuộc về người khác.

## Nguyên tắc lái xe phòng thủ
- **Quét mắt liên tục**: nhìn xa phía trước 200–300m, không chỉ nhìn xe ngay trước
- **Dự đoán hành vi**: để ý xe bên cạnh, người đi bộ, trẻ em gần đường
- **Khoảng cách an toàn**: luôn giữ khoảng cách đủ để dừng kịp
- **Tốc độ phù hợp**: không nhất thiết chạy đúng giới hạn nếu điều kiện nguy hiểm hơn
- **Nhường khi nghi ngờ**: nếu không chắc ai ưu tiên — nhường

## Xử lý xe hung hăng, lái ẩu
- Không đáp trả bằng cách tăng tốc, chen lấn, chớp đèn kích động
- Giữ khoảng cách xa hơn bình thường với xe hung hăng
- Cho xe đó vượt qua, không cản đường
- Nếu bị đe doạ: lái xe đến nơi đông người, đồn công an

## Xử lý hành khách gây rối (xe khách, taxi)
- Bình tĩnh, không tranh cãi khi đang lái xe
- Dừng xe ở nơi an toàn trước khi xử lý tình huống
- Không để xung đột ảnh hưởng đến việc lái xe
- Báo ngay cho công ty qua app hoặc điện thoại
- Ghi âm/ghi hình khi có thể (camera hành trình)

## Xử lý khi bị theo dõi hoặc cảm thấy nguy hiểm
- Không đi vào đường vắng, hẻm tối
- Lái xe đến đồn công an, trạm xăng, nơi đông người
- Gọi 113 nếu thực sự bị đe doạ
- Báo vị trí cho công ty qua ứng dụng

## Điểm mù nguy hiểm cần nhớ
- Góc sau xe tải lớn: không đi vào vùng tài xế xe tải không thấy được
- Cửa xe mở đột ngột khi đỗ bên đường: giữ khoảng cách 1m
- Trẻ em chạy ra từ giữa 2 xe đỗ: giảm tốc khi đi qua xe đỗ
""",
    },
    {
        "title": "Phòng tránh tai nạn với người đi bộ và xe máy",
        "category": "safety",
        "content": """## Điểm mù nguy hiểm với xe máy
- Xe máy nhỏ hơn, dễ bị che khuất bởi cột A (trụ kính trước)
- Kiểm tra điểm mù bằng cách quay đầu (không chỉ dùng gương)
- Xe máy thường di chuyển nhanh và len lỏi — cẩn thận khi mở cửa
- Giữ khoảng cách phía trước xe máy ít nhất 3–4 giây

## Các tình huống nguy hiểm với xe máy phổ biến
- Xe máy vượt đèn đỏ hoặc đi ngược chiều
- Xe máy lạng lách giữa các làn
- Xe máy chở hàng cồng kềnh, che khuất tầm nhìn tài xế
- Xe máy đi ban đêm không có đèn hậu

## Tình huống nguy hiểm với người đi bộ
- Trẻ em chạy ra đường bất ngờ — đặc biệt gần trường học, công viên
- Người già qua đường chậm
- Người đi bộ nhìn điện thoại, không chú ý xe
- Người đi bộ mặc màu tối ban đêm

## Vùng cần đặc biệt chú ý
- Gần trường học giờ tan trường (6h30–7h30 và 11h–12h, 16h30–17h30)
- Gần chợ, siêu thị
- Khu dân cư có nhiều trẻ em
- Đoạn đường có nhiều xe máy dừng đỗ hai bên

## Kỹ thuật dự phòng
- Nhìn trước 10–15 giây để phát hiện người đi bộ sớm
- Giảm tốc chủ động khi đến gần vạch sang đường dù không thấy ai
- Không bóp còi vào mặt người đi bộ — có thể gây hoảng loạn
- Nếu người đi bộ đang sang: phanh sớm, nhường hoàn toàn
""",
    },
    {
        "title": "Trang bị an toàn bắt buộc và khuyến nghị trên xe",
        "category": "safety",
        "content": """## Trang bị bắt buộc theo pháp luật
- **Bình cứu hoả**: xe con ít nhất 1 bình 1kg; xe tải, xe khách theo quy định riêng
- **Tam giác cảnh báo phản quang**: ít nhất 1 bộ
- **Dây an toàn**: tất cả ghế có dây an toàn, hành khách phải thắt
- **Gương chiếu hậu**: đủ 3 gương (2 bên + trong), điều chỉnh đúng

## Trang bị khuyến nghị nên có
- **Bộ sơ cứu**: băng gạc, cầm máu, kéo, găng tay y tế
- **Đèn pin**: dùng khi sự cố ban đêm
- **Xăng dự phòng** (can nhỏ 5L): cho xe chạy đường dài
- **Cáp kích bình** (jump cable): 2–3m, loại tốt
- **Bơm lốp mini**: bơm điện cắm cổng sạc xe
- **Chìa khoá dự phòng**: để ở nơi an toàn, không trong xe

## Sử dụng bình cứu hoả đúng cách
- Nhớ vị trí bình trong xe (thường dưới ghế lái hoặc ghế phụ)
- Kéo chốt an toàn, hướng vòi vào gốc lửa
- Bóp cò, quét từ gốc lửa ra ngoài
- Không phun vào mặt người
- Sau khi dùng: nạp lại ngay, không để bình đã dùng tiếp tục trên xe

## Dây an toàn — tại sao quan trọng
- Giảm 45% nguy cơ tử vong trong tai nạn
- Bắt buộc cho tất cả hành khách trên xe
- Trẻ em dưới 4 tuổi: phải dùng ghế trẻ em chuyên dụng
- Phạt không thắt dây: 800.000 – 1.000.000đ/người

## Bảo dưỡng trang bị an toàn định kỳ
- Kiểm tra hạn sử dụng bình cứu hoả hàng năm
- Kiểm tra dây an toàn: không bị cứng, khóa hoạt động tốt
- Vệ sinh gương chiếu hậu mỗi khi rửa xe
- Thay pin đèn flash cảnh báo (nếu dùng loại pin)
""",
    },

    # ─── LUẬT GIAO THÔNG BỔ SUNG ─────────────────────────────────────────
    {
        "title": "Quy tắc giao thông tại vòng xuyến",
        "category": "traffic_law",
        "content": """## Nguyên tắc cơ bản tại vòng xuyến
- Xe **đang lưu thông trong vòng xuyến** được ưu tiên
- Xe **sắp vào vòng xuyến** phải nhường và chờ khoảng trống an toàn
- Đi theo chiều kim đồng hồ (ngược chiều ở Việt Nam — đi bên phải)

## Thủ tục đi qua vòng xuyến đúng
1. Giảm tốc khi tiếp cận vòng xuyến
2. Quan sát xe trong vòng từ bên trái (hướng đang có xe chạy tới)
3. Nhường xe trong vòng xuyến
4. Vào vòng khi có khoảng trống an toàn
5. Bật xi-nhan phải trước khi thoát ra
6. Ra khỏi vòng xuyến theo lối mình muốn

## Chọn làn trong vòng xuyến nhiều làn
- Rẽ phải (lối ra đầu tiên): đi làn ngoài cùng bên phải
- Đi thẳng hoặc rẽ trái (lối ra sau): đi làn trong
- Không đột ngột chuyển làn trong vòng xuyến

## Lỗi phổ biến tại vòng xuyến
- Vào vòng mà không nhường xe trong vòng
- Không bật xi-nhan khi thoát ra
- Dừng trong vòng xuyến gây ùn tắc
- Đi ngược chiều trong vòng xuyến

## Mức phạt
- Không nhường đường trong vòng xuyến: 800.000 – 1.000.000đ
- Đi không đúng phần đường: 800.000 – 1.000.000đ
- Đi ngược chiều: 3.000.000 – 5.000.000đ
""",
    },
    {
        "title": "Quy định khu vực trường học, bệnh viện và khu dân cư",
        "category": "traffic_law",
        "content": """## Khu vực trường học
- Tốc độ tối đa: 40 km/h (có biển báo), 30 km/h trong sân trường
- Đặc biệt cẩn thận giờ tan trường: 6h30–7h30 và 11h–12h và 16h30–17h30
- Cấm dừng đỗ trong phạm vi 5m cổng trường
- Nhường tuyệt đối học sinh đang sang đường
- Không bấm còi trong giờ thi, giờ học (nếu có biển)

## Khu vực bệnh viện
- Tốc độ tối đa: 40 km/h
- Cấm bấm còi to trước cổng bệnh viện
- Nhường xe cấp cứu ra vào bất cứ lúc nào
- Không đỗ xe chắn cổng cấp cứu

## Khu dân cư và đường nội bộ
- Tốc độ tối đa: 40 km/h, trong ngõ hẹp: 20 km/h
- Người đi bộ, trẻ em có thể ra đường bất ngờ
- Không bấm còi inh ỏi trong đêm (sau 22h)
- Đỗ xe không cản lối đi của cư dân

## Gần chợ, trung tâm thương mại
- Chú ý người đột ngột đi ra giữa xe đỗ
- Xe đẩy hàng có thể ra đường không báo hiệu
- Tốc độ thấp, sẵn sàng phanh bất cứ lúc nào

## Quy định giờ cấm xe tải ở đô thị
- TP.HCM: xe tải trên 2,5 tấn cấm nội thành 6h–9h và 16h–20h
- Hà Nội: quy định tương tự, kiểm tra biển báo từng khu vực
- Vi phạm: 1.200.000 – 2.000.000đ
""",
    },
    {
        "title": "Quy định đường một chiều và làn ưu tiên",
        "category": "traffic_law",
        "content": """## Đường một chiều
- Nhận biết: biển báo mũi tên một chiều, vạch kẻ đường song song
- Được phép đi bất kỳ làn nào trên đường một chiều
- Cấm đi ngược chiều trên đường một chiều
- Xe đạp có thể đi ngược chiều trên một số đường một chiều nếu có biển cho phép

## Mức phạt đi ngược chiều đường một chiều
- Xe con: 3.000.000 – 5.000.000đ + tước bằng 1–3 tháng
- Xe tải, xe khách: 5.000.000 – 7.000.000đ + tước bằng 1–3 tháng

## Làn xe buýt ưu tiên (BRT)
- Được đánh dấu bằng vạch màu đỏ hoặc biển chỉ dẫn "Bus only"
- Chỉ xe buýt được đi trong giờ cao điểm (thường 6h–9h và 16h–20h)
- Ngoài giờ cao điểm: xe cá nhân được phép đi làn này (tuỳ quy định từng tuyến)
- Vi phạm: 800.000 – 1.200.000đ

## Làn khẩn cấp trên cao tốc
- Chỉ dùng khi xe bị sự cố, hỏng hóc
- Không đi vào làn khẩn cấp để tránh tắc đường
- Không đỗ xe trên làn khẩn cấp khi không có lý do
- Vi phạm: 1.000.000 – 2.000.000đ

## Đường ưu tiên (đường chính)
- Nhận biết: biển báo "Đường ưu tiên" hoặc biển "Nhường đường"
- Xe trên đường ưu tiên được quyền đi trước tại giao lộ
- Xe từ đường phụ ra phải nhường tuyệt đối
""",
    },
    {
        "title": "Quy định về sử dụng điện thoại và thiết bị điện tử khi lái xe",
        "category": "traffic_law",
        "content": """## Quy định pháp luật hiện hành
- **Cấm hoàn toàn** cầm điện thoại khi lái xe (kể cả dừng đèn đỏ)
- **Được phép**: dùng tai nghe không dây (một bên tai), loa ngoài điện thoại đặt cố định
- **Được phép**: dùng thiết bị GPS gắn cố định trên xe
- Phạt: 800.000 – 1.000.000đ cho xe con

## Thiết bị được phép sử dụng
- Hệ thống thông tin giải trí gắn sẵn trên xe (head unit)
- GPS/màn hình dẫn đường gắn cố định trên giá đỡ
- Tai nghe Bluetooth một bên (không được dùng cả 2 tai)
- Camera hành trình (không được xem khi lái)

## Thiết bị bị cấm sử dụng
- Cầm điện thoại bằng tay (dù chỉ đọc tin nhắn)
- Đặt điện thoại lên đùi, nhìn trong khi lái
- Đội tai nghe 2 bên khi lái xe
- Xem video, phim trên thiết bị cầm tay

## Cài đặt điện thoại khi lái xe
- Bật chế độ **"Không làm phiền khi lái xe"** (Android Auto / Apple CarPlay)
- Cài ứng dụng tự trả lời tin nhắn: "Đang lái xe, sẽ trả lời sau"
- Đặt điện thoại ở chế độ im lặng hoặc chỉ rung
- Nếu cần nghe cuộc gọi: dừng xe ở nơi an toàn

## Hậu quả thực tế của dùng điện thoại khi lái
- Phản xạ chậm gấp 4 lần so với lái bình thường
- Tương đương lái xe khi nồng độ cồn 0,8‰
- 26% các vụ tai nạn liên quan đến điện thoại
- Nhắn tin khi lái tăng nguy cơ tai nạn lên 23 lần
""",
    },

    # ─── CẨM NANG XE BỔ SUNG ─────────────────────────────────────────────
    {
        "title": "Các loại nhiên liệu và cách tra xăng đúng cách",
        "category": "vehicle_manual",
        "content": """## Các loại xăng phổ biến tại Việt Nam
- **RON 95-III (E5)**: xăng pha 5% ethanol, phổ biến nhất, giá thấp hơn
- **RON 95**: xăng không pha cồn, dành cho xe yêu cầu chỉ số octan cao
- **RON 92**: ít phổ biến hơn, một số trạm còn bán
- **Dầu DO 0.05S (Euro 5)**: dành cho xe diesel

## Chọn loại nhiên liệu đúng cho xe
- Xem sổ tay xe hoặc nhãn dán trong nắp bình xăng
- Phần lớn xe đời mới (2015 trở lên): dùng RON 95 hoặc E5 được
- Xe cũ trước 2010: một số không phù hợp E5, kiểm tra nhà sản xuất
- **Không bao giờ** đổ xăng vào xe diesel và ngược lại

## Quy trình tra xăng đúng cách
1. Tắt máy xe trước khi vào trạm
2. Tắt điện thoại hoặc không dùng tại bơm
3. Mở nắp bình xăng
4. Thông báo nhân viên loại xăng và số lít/số tiền
5. Đứng xa nguồn lửa, không hút thuốc
6. Kiểm tra đồng hồ bơm bắt đầu từ 0
7. Nhận hoá đơn và kiểm tra số liệu

## Lưu ý khi đổ xăng
- Không đổ xăng khi máy xe còn nóng ngay (chờ 5 phút)
- Không đổ quá đầy (tràn ra gây cháy, hỏng bộ lọc hơi)
- Lau sạch nếu xăng bắn ra ngoài trước khi khởi động
- Luôn giữ mức xăng trên 1/4 bình — đi gần cạn làm hỏng bơm xăng

## Tiết kiệm nhiên liệu
- Kiểm tra áp suất lốp đúng — lốp xẹp tốn thêm 3–5% xăng
- Tắt máy khi đỗ trên 1 phút
- Tránh tăng tốc và phanh đột ngột
- Tốc độ ổn định 60–80 km/h tiết kiệm nhất trên quốc lộ
""",
    },
    {
        "title": "Bảo quản xe trong điều kiện thời tiết Việt Nam",
        "category": "vehicle_manual",
        "content": """## Bảo quản xe mùa nắng nóng
- Đỗ xe dưới bóng mát hoặc dùng tấm che nắng kính trước
- Nhiệt độ trong xe có thể lên 60–70°C — hạ nhiệt trước khi vào xe
- Kiểm tra áp suất lốp thường xuyên hơn (nắng nóng tăng áp suất)
- Kiểm tra mức nước làm mát thường xuyên hơn
- Không để đồ dễ cháy nổ trong xe (bật lửa, nước hoa)
- Kiểm tra dây curoa thường xuyên hơn (dễ giãn, nứt khi nóng)

## Bảo quản xe mùa mưa
- Kiểm tra gạt mưa — cần thay nếu để vệt hoặc kêu
- Kiểm tra đèn chiếu sáng hoạt động tốt
- Làm sạch rỉ sét sớm nếu phát hiện
- Sau khi lái qua đường ngập: kiểm tra phanh, gầm xe
- Phun chống rỉ gầm xe hàng năm

## Rửa xe đúng cách
- Rửa xe khi máy nguội (tránh nứt vỡ kính, giãn nở đột ngột)
- Dùng xà phòng chuyên dụng cho xe, không dùng nước rửa chén
- Rửa gầm xe loại bỏ bùn đất tích tụ
- Lau khô ngay sau khi rửa, đặc biệt phần kính và gương

## Bảo quản khi không dùng xe lâu ngày (trên 2 tuần)
- Đổ đầy bình xăng (tránh oxy hoá bên trong bình)
- Ngắt cực âm ắc quy nếu không đi trên 1 tháng
- Đặt xe trên bề mặt phẳng, kéo phanh tay vừa phải
- Bơm lốp đúng áp suất trước khi cất xe
- Phủ bạt chống bụi nếu đỗ ngoài trời

## Lưu ý đặc biệt cho xe vùng ven biển
- Muối biển gây rỉ sét nhanh hơn vùng nội địa
- Rửa xe thường xuyên hơn (1–2 lần/tuần)
- Phun chống rỉ gầm 2 lần/năm
- Kiểm tra phần tiếp xúc kim loại dưới gầm hàng tháng
""",
    },
    {
        "title": "Lốp xe — thông số, bảo dưỡng và thay thế",
        "category": "vehicle_manual",
        "content": """## Đọc thông số lốp xe
Thông số trên lốp xe ví dụ: **205/55R16 91V**
- **205**: bề rộng lốp (mm)
- **55**: tỷ lệ chiều cao/chiều rộng (%)
- **R**: lốp radial (loại phổ biến nhất)
- **16**: đường kính vành (inch)
- **91**: chỉ số tải trọng (615 kg/bánh)
- **V**: chỉ số tốc độ tối đa (240 km/h)

## Áp suất lốp tiêu chuẩn
- Xe con thông thường: 30–35 PSI (2,1–2,4 bar)
- Trước và sau có thể khác nhau — xem nhãn dán trên cửa xe phía tài xế
- Kiểm tra khi lốp nguội (trước khi chạy hoặc sau 3 giờ dừng xe)
- Lốp dự phòng nhỏ (spare): thường 60 PSI, tốc độ tối đa 80 km/h

## Dấu hiệu cần thay lốp
- Độ sâu rãnh lốp dưới 1,6mm (kiểm tra bằng đồng xu)
- Có vết nứt, phồng, biến dạng trên thành lốp
- Lốp cũ trên 5–6 năm dù còn hoa (cao su lão hoá)
- Xe rung khi chạy tốc độ cao — lốp mất cân bằng
- Xe bị kéo lệch — áp suất không đều hoặc mòn không đều

## Xoay lốp định kỳ
- Xoay lốp mỗi 10.000–15.000 km để mòn đều
- Lốp trước mòn nhanh hơn lốp sau (do lái và phanh)
- Sơ đồ xoay: lốp sau → trước cùng bên; lốp trước → sau chéo bên

## Thay lốp dự phòng đúng cách
1. Đỗ xe trên mặt phẳng cứng, bật đèn khẩn cấp
2. Kê chèn bánh đối diện trước khi nâng kích
3. Nới lỏng bu-lông trước khi kích (còn chạm đất)
4. Kích đúng điểm kích (xem sách xe)
5. Tháo lốp hỏng, lắp lốp dự phòng
6. Siết bu-lông theo thứ tự chéo (không siết vòng tròn)
7. Hạ kích, siết chặt lại toàn bộ bu-lông
""",
    },
    {
        "title": "Dấu hiệu xe cần bảo dưỡng khẩn và cách xử lý",
        "category": "vehicle_manual",
        "content": """## Dấu hiệu phanh cần kiểm tra ngay
- Tiếng kêu két hoặc rít khi phanh: má phanh mòn, cần thay ngay
- Xe rung hoặc giật khi phanh: đĩa phanh bị biến dạng
- Bàn đạp phanh mềm hoặc phải đạp sâu hơn bình thường: dầu phanh thiếu/rò
- Xe bị kéo lệch khi phanh: má phanh mòn không đều

## Dấu hiệu dầu máy cần chú ý
- Đèn áp suất dầu bật: DỪNG XE NGAY, tắt máy — tiếp tục có thể hỏng động cơ
- Khói trắng từ ống xả: dầu lọt vào buồng đốt — hỏng gioăng, séc măng
- Mùi khét khi xe nóng: dầu rò bị đốt
- Dầu màu đen đặc: quá hạn thay — thay ngay
- Dầu màu nâu sữa (trắng đục): nước lọt vào dầu — nguy hiểm, đưa vào gara

## Dấu hiệu hệ thống làm mát
- Đồng hồ nhiệt độ vào vùng đỏ: DỪNG XE, tắt máy ngay
- Nước làm mát giảm liên tục: rò rỉ hoặc gasket hỏng
- Mùi ngọt trong khoang xe: nước làm mát rò vào trong

## Dấu hiệu hộp số
- Xe chậm bắt tốc, giật khi vào số: dầu hộp số cần thay
- Tiếng ồn khi vào số N: hộp số có vấn đề
- Chuyển số trễ hoặc rung: hộp số tự động cần kiểm tra

## Dấu hiệu hệ thống treo và lái
- Xe bị nảy mạnh qua ổ gà: giảm xóc hỏng
- Tiếng kêu khi qua ổ gà, qua cua: cao su ổ đỡ, đòn gánh
- Vô lăng rung khi chạy 80–120 km/h: cần cân bằng lốp hoặc cân chỉnh góc đặt bánh

## Nguyên tắc chung
- Khi đèn cảnh báo bật: không bỏ qua, kiểm tra trong 24–48 giờ
- Tiếng kêu lạ liên tục: không chờ hư hoàn toàn mới sửa
- Sửa sớm rẻ hơn nhiều so với để hỏng nặng
""",
    },

    # ─── QUY TRÌNH NỘI BỘ CÔNG TY ────────────────────────────────────────
    {
        "title": "Quy trình báo cáo sự cố và xử lý nội bộ",
        "category": "safety",
        "content": """## Khi nào phải báo cáo
- Tai nạn giao thông dù nhỏ (va quẹt, trầy xước)
- Xe bị hỏng hóc không thể tự xử lý
- Phát hiện tình trạng bất thường của xe trước/trong khi lái
- Sự cố với hành khách hoặc hàng hoá
- Bị phạt vi phạm giao thông trong lúc làm việc

## Thứ tự xử lý khi có sự cố
1. **Đảm bảo an toàn**: đưa xe vào lề, bật đèn khẩn cấp
2. **Kiểm tra thương tích**: bản thân và người liên quan
3. **Gọi 115** nếu có người bị thương
4. **Báo công ty ngay**: qua ứng dụng hoặc điện thoại trực tiếp
5. **Không tự ý thương lượng bồi thường** khi chưa có mặt đại diện công ty
6. **Chụp ảnh hiện trường**: xe, vị trí, biển số, thiệt hại
7. **Lấy thông tin đối phương**: tên, điện thoại, biển số, bảo hiểm

## Cách gửi báo cáo qua ứng dụng
- Mở app → tab Báo cáo → mô tả tình trạng → đính kèm ảnh → Gửi
- App tự động đính kèm vị trí GPS và thời gian
- Báo cáo gửi tới công ty ngay lập tức

## Thông tin cần ghi nhận tại hiện trường
- Thời gian và địa điểm chính xác
- Mô tả diễn biến sự cố
- Biển số và thông tin xe liên quan
- Tên, số điện thoại nhân chứng
- Thông tin cảnh sát giao thông nếu có mặt

## Điều tuyệt đối không làm
- Không rời hiện trường khi chưa được phép
- Không nhận lỗi hoặc ký giấy thỏa thuận bồi thường ngay tại chỗ
- Không di chuyển xe khi chưa được CSGT cho phép (trừ trường hợp nguy hiểm)
- Không uống rượu sau tai nạn (cản trở việc đo nồng độ cồn)
""",
    },
    {
        "title": "Quy trình nhận xe và bàn giao ca làm việc",
        "category": "safety",
        "content": """## Kiểm tra xe khi nhận ca
Trước khi xuất phát, tài xế phải kiểm tra và xác nhận:

### Bên ngoài xe
- 4 lốp: áp suất, không nứt, không dị vật
- Đèn pha, đèn hậu, đèn xi-nhan: hoạt động bình thường
- Gương chiếu hậu: không vỡ, điều chỉnh đúng góc
- Kính chắn gió: không nứt ảnh hưởng tầm nhìn
- Thân xe: ghi nhận vết xước/móp hiện có (chụp ảnh)

### Trong xe và khoang máy
- Dầu máy: mức giữa MIN–MAX, màu bình thường
- Nước làm mát: mức đủ
- Dầu phanh: mức đủ
- Bình xăng: mức đủ cho ca
- Điều hoà, gạt mưa: hoạt động tốt
- Bình cứu hoả: còn hạn, chốt an toàn nguyên vẹn
- Tam giác cảnh báo: có đủ trong xe

### Giấy tờ
- Đăng ký xe: có trong xe
- Bảo hiểm TNDS: còn hạn
- Kiểm định (đăng kiểm): còn hạn

## Ghi nhận tình trạng xe
- Ghi số km odometer khi nhận xe
- Chụp ảnh tổng thể xe và các điểm bất thường
- Báo cáo ngay nếu phát hiện vấn đề — không nhận xe hỏng

## Bàn giao xe khi hết ca
- Ghi số km kết thúc
- Vệ sinh sơ bộ trong xe
- Báo cáo mọi sự cố trong ca (dù nhỏ)
- Bàn giao đầy đủ giấy tờ, chìa khoá
- Đỗ xe đúng vị trí quy định

## Trường hợp phát hiện xe có vấn đề
- Báo ngay cho quản lý, không tự ý sửa chữa nếu không được phép
- Không xuất xe khi phát hiện lỗi kỹ thuật nghiêm trọng
- Ghi rõ vấn đề trong báo cáo bàn giao
""",
    },

    # ─── BỔ SUNG 8 CHỦ ĐỀ QUAN TRỌNG ────────────────────────────────────
    {
        "title": "Xe bốc cháy — xử lý khẩn cấp",
        "category": "safety",
        "content": """## Dấu hiệu nhận biết xe sắp hoặc đang cháy
- Mùi khét bất thường từ khoang máy hoặc trong xe
- Khói bốc ra từ mũi xe, gầm xe, hoặc bảng điều khiển
- Đèn cảnh báo nhiệt độ hoặc điện bật liên tục
- Tiếng nổ nhỏ từ khoang động cơ
- Nhiệt độ tay lái, sàn xe tăng bất thường

## Xử lý ngay khi phát hiện cháy
1. **Dừng xe NGAY** tại nơi an toàn, tránh xa xe khác và vật dễ cháy
2. **Tắt máy** — cắt nguồn nhiên liệu
3. **Tất cả mọi người ra khỏi xe ngay lập tức** — không lấy đồ đạc
4. Thoát ra cửa gần nhất, nếu kẹt: đập vỡ kính cạnh cửa
5. **Di chuyển xa ít nhất 100m** — tránh nổ bình xăng
6. **Gọi 114** (cứu hoả) và 115 (nếu có người bị thương)

## Dùng bình cứu hoả (chỉ khi lửa còn nhỏ, chưa vào khoang xe)
- Đứng đầu gió, cách xa 2–3m
- Hướng vòi vào GỐC lửa, không phun vào ngọn
- Quét từ gốc ra ngoài
- Nếu lửa không tắt trong 30 giây: bỏ đi ngay, không tiếp tục

## Tuyệt đối KHÔNG làm
- Không mở nắp capo khi thấy khói (oxy nuôi lửa bùng mạnh hơn)
- Không ở lại trong hoặc gần xe để lấy đồ
- Không dùng nước dập lửa điện hoặc lửa xăng dầu
- Không quay lại xe sau khi đã thoát ra

## Nguyên nhân phổ biến xe bốc cháy
- Chập điện dây điện cũ, hở
- Nhiên liệu rò rỉ gần nguồn nhiệt
- Quá nhiệt động cơ kéo dài
- Tai nạn va chạm mạnh
- Bình cứu hoả hết hạn, không có trong xe
""",
    },
    {
        "title": "Ngủ trong xe có điều hoà — nguy hiểm ngộ độc CO",
        "category": "safety",
        "content": """## Tại sao ngủ trong xe điều hoà nguy hiểm chết người
- Động cơ nổ tạo ra khí carbon monoxide (CO) — không màu, không mùi, không vị
- CO tích tụ trong xe kín gây ngộ độc nhanh, có thể tử vong trong 30–60 phút
- Nạn nhân thường ngủ không tỉnh lại — không có cảm giác cảnh báo
- Đặc biệt nguy hiểm khi đỗ trong ga-ra, hầm, hoặc gió ngược ống xả vào xe

## Triệu chứng ngộ độc CO
- Nhẹ: đau đầu, chóng mặt, buồn nôn, mệt mỏi
- Nặng: lú lẫn, mất phương hướng, ngất
- Nguy kịch: mất ý thức, không thể tự thoát ra

## Tuyệt đối KHÔNG làm
- Không ngủ qua đêm trong xe có máy nổ và điều hoà bật
- Không đỗ xe trong ga-ra kín với máy nổ
- Không nằm ngủ trong xe đang chạy không tắt máy dù chỉ "nghỉ ngắn"

## Cách nghỉ ngơi an toàn trong xe
- Tắt máy, mở cửa sổ hé để không khí lưu thông
- Nếu trời nóng: đỗ dưới bóng mát, dùng tấm che nắng
- Nghỉ tối đa 20–30 phút rồi tiếp tục hoặc vào phòng nghỉ
- Không bao giờ ngủ đêm trong xe có máy nổ

## Xử lý khi phát hiện người ngộ độc CO trong xe
1. Mở cửa xe ngay lập tức
2. Đưa nạn nhân ra ngoài vào nơi thoáng khí
3. Gọi 115 ngay
4. Nếu nạn nhân ngừng thở: thực hiện CPR
5. Không đưa nạn nhân trở lại xe
""",
    },
    {
        "title": "Lái xe khi đang dùng thuốc — những điều cần biết",
        "category": "safety",
        "content": """## Các nhóm thuốc ảnh hưởng đến lái xe

### Thuốc gây buồn ngủ, không được lái xe
- Thuốc kháng histamine (dị ứng, cảm): Chlorpheniramine, Diphenhydramine
- Thuốc an thần, ngủ: Diazepam, Lorazepam, Zolpidem
- Thuốc chống trầm cảm một số loại
- Thuốc say xe (Dimenhydrinate — Dramamine)
- Một số thuốc giảm đau mạnh (codeine, tramadol)

### Thuốc cần thận trọng, không lái khi mới dùng
- Thuốc hạ huyết áp (có thể gây chóng mặt)
- Thuốc tiểu đường (có thể gây hạ đường huyết đột ngột)
- Thuốc chống co giật
- Một số kháng sinh liều cao

### Thuốc ít ảnh hưởng (thường an toàn)
- Paracetamol (liều bình thường)
- Kháng sinh thông thường không gây buồn ngủ
- Thuốc huyết áp quen dùng lâu ngày (đã ổn định)

## Nguyên tắc khi dùng thuốc mới
- Đọc kỹ tờ hướng dẫn — tìm cụm từ "gây buồn ngủ", "không lái xe"
- Dùng thử buổi tối trước để biết phản ứng cơ thể
- Hỏi bác sĩ/dược sĩ nếu không chắc có ảnh hưởng lái xe không
- Không tự ý tăng liều khi đang lái xe

## Các dấu hiệu cần dừng xe ngay
- Mắt nặng, nhìn mờ sau khi uống thuốc
- Phản xạ chậm hơn bình thường
- Chóng mặt, mất thăng bằng
- Khó tập trung, nhầm lẫn

## Hạ đường huyết khi lái xe (tài xế tiểu đường)
- Dấu hiệu: run tay, đổ mồ hôi lạnh, đói cồn cào, mờ mắt
- Xử lý: dừng xe ngay, ăn kẹo/uống nước ngọt
- Chờ 15 phút, kiểm tra lại trước khi tiếp tục lái
- Luôn mang theo đồ ngọt trong xe
""",
    },
    {
        "title": "Qua trạm thu phí — ETC và thu tiền mặt",
        "category": "traffic_law",
        "content": """## Hệ thống thu phí không dừng ETC
- ETC (Electronic Toll Collection) — xe không cần dừng, tự động thu phí
- Cần dán thẻ ETC lên kính chắn gió (do VETC hoặc VDTC cấp)
- Tài khoản ETC cần nạp tiền trước (prepaid)
- Làn ETC có biển "ETC" và đèn xanh — đi với tốc độ tối đa 20 km/h

## Cách sử dụng làn ETC
1. Vào làn có biển "ETC"
2. Giảm tốc độ xuống 20 km/h khi qua cổng
3. Cổng tự mở, phí tự động trừ từ tài khoản
4. Không dừng hẳn trừ khi cổng không mở

## Xử lý khi ETC không nhận
- Dừng xe, nhấn nút gọi nhân viên trên cột
- Không lùi xe — nguy hiểm
- Nhân viên sẽ hỗ trợ thu phí thủ công
- Kiểm tra: thẻ dán đúng vị trí, tài khoản còn tiền

## Nạp tiền tài khoản ETC
- Qua app ngân hàng, ví điện tử (Momo, ZaloPay...)
- Tại cây ATM ngân hàng liên kết
- Tại trạm dịch vụ ETC
- Kiểm tra số dư trước chuyến đi dài

## Làn thu tiền mặt (Mixed/MTC)
- Dừng xe trước vạch, tắt gác chân ga
- Đưa tiền đúng mệnh giá nếu có thể (tiết kiệm thời gian)
- Nhận vé và tiền thừa trước khi đi
- Không tranh cãi về giá vé tại cổng — khiếu nại qua đường dây hỗ trợ

## Mức phạt vi phạm trạm thu phí
- Đi vào làn ETC không có thẻ/hết tiền cố tình: 1.000.000 – 2.000.000đ
- Không chịu nộp phí: 3.000.000 – 5.000.000đ
""",
    },
    {
        "title": "Phòng chống trộm cắp và bảo vệ xe",
        "category": "safety",
        "content": """## Thói quen bảo vệ xe hàng ngày
- Luôn khoá xe và rút chìa khoá khi rời xa, dù chỉ 1 phút
- Không để tài liệu, tiền mặt, điện thoại lộ trong xe
- Đỗ xe ở nơi có đèn sáng, đông người, có camera
- Kéo kính lên, đóng cửa kín trước khi rời xe
- Không để giấy tờ xe gốc trong xe — mang theo người

## Khu vực và thời điểm rủi ro cao
- Bãi đỗ xe tối, vắng người — đặc biệt ban đêm
- Khu vực gần chợ, bến xe, trung tâm thương mại đông đúc
- Để xe trong hẻm vắng qua đêm
- Sự kiện đông người, lễ hội

## Thiết bị bảo vệ xe khuyến nghị
- **Camera hành trình 360°**: ghi lại cả khi xe đỗ (chế độ parking)
- **Khoá vô lăng**: ngăn kẻ trộm lái xe đi ngay cả khi mở được cửa
- **Báo động xe**: phát hiện va chạm, rung động bất thường
- **Định vị GPS**: theo dõi vị trí xe qua điện thoại

## Khi phát hiện xe bị trộm hoặc phá
- Không chạm vào hiện trường
- Gọi 113 ngay
- Cung cấp: biển số xe, màu sắc, thương hiệu, vị trí đỗ lần cuối
- Trình báo công ty bảo hiểm trong 24 giờ
- Cung cấp camera hành trình hoặc camera khu vực nếu có

## Phòng tránh bị "dàn cảnh" trên đường
- Không dừng xe vì người lạ ra hiệu "xe bạn bị hỏng"
- Không mở cửa cho người lạ khi đang dừng đèn đỏ
- Khi bị đụng nhẹ từ phía sau ở nơi vắng: bật đèn khẩn cấp, đến nơi đông người rồi mới dừng
- Không để người lạ vào xe dù lý do có vẻ hợp lý
""",
    },
    {
        "title": "Lái xe qua vùng ngập lụt và mưa lớn",
        "category": "safety",
        "content": """## Đánh giá mức độ ngập trước khi vào
- Mức an toàn: dưới 20–25cm (dưới bục phanh của ô tô thông thường)
- Mức nguy hiểm: trên 30cm — có thể lọt nước vào hệ thống hút khí, hỏng động cơ
- Nước chảy xiết: nguy hiểm dù nước không sâu — có thể đẩy xe trôi
- Quan sát xe khác đi qua trước để đánh giá mức nước

## Kỹ thuật lái qua đường ngập
1. Chuyển về số thấp (số 1 hoặc 2) trước khi vào
2. Đi chậm và đều tốc độ — không tăng giảm tốc đột ngột
3. Giữ tua máy cao (đạp nhẹ ga) để tránh nước lọt vào ống xả
4. Không đi theo sau xe lớn sát — sóng xe lớn tạo ra có thể nhấn chìm xe nhỏ
5. Sau khi ra: nhấn nhẹ phanh vài lần để làm khô má phanh

## Dấu hiệu xe bị lọt nước vào động cơ
- Máy đột ngột tắt giữa vùng ngập
- Tiếng máy bất thường, rung mạnh
- Xử lý: KHÔNG cố đề lại — kéo hoặc đẩy xe ra khỏi nước trước
- Đề lại khi máy đã ngập nước: vỡ thanh truyền, hỏng hoàn toàn động cơ

## Khi xe bị mắc kẹt trong nước
- Không hoảng loạn
- Nếu nước dâng vào xe: mở cửa sổ ngay (trước khi cửa kẹt do áp lực nước)
- Nếu cửa kẹt: dùng vật cứng đập góc kính cạnh cửa
- Thoát ra, bơi hoặc đứng trên nóc xe, kêu cứu

## Những điều tuyệt đối không làm
- Không liều vào vùng nước không biết độ sâu
- Không đi theo đường ngập dù đi tắt được
- Không dừng xe giữa vùng ngập để kiểm tra
- Không mở capô khi đang trong nước
""",
    },
    {
        "title": "Quy định xe điện tại Việt Nam",
        "category": "traffic_law",
        "content": """## Phân loại xe điện theo pháp luật VN
- **Xe đạp điện**: tốc độ tối đa 25 km/h, không cần bằng lái, phải đội mũ bảo hiểm
- **Xe máy điện**: tốc độ trên 25 km/h, cần đăng ký, cần bằng lái hạng A1
- **Ô tô điện**: đầy đủ quy định như xe xăng — bằng lái B1/B2, đăng ký, đăng kiểm, bảo hiểm

## Đăng ký và đăng kiểm xe điện
- Ô tô điện: đăng ký, đăng kiểm như ô tô xăng — các quy trình giống nhau
- Xe máy điện trên 25 km/h: cần đăng ký biển số, bảo hiểm TNDS
- Kiểm định: kiểm tra thêm hệ thống pin, cáp sạc, motor điện

## Sạc xe điện an toàn
- Dùng trạm sạc được chứng nhận, không dùng ổ cắm gia dụng thông thường cho xe ô tô điện
- Không sạc qua đêm trong nhà kín, ga-ra thiếu thông gió
- Không sạc khi pin quá nóng (sau khi chạy dài)
- Kiểm tra cáp sạc thường xuyên — hở, đứt cách điện có thể gây cháy

## Lái xe điện an toàn
- Xe điện tăng tốc nhanh hơn xe xăng — cẩn thận khi ra khỏi điểm dừng
- Xe điện gần như không có tiếng ồn — người đi bộ có thể không nghe thấy
- Phanh tái sinh (regenerative braking): nhả ga xe giảm tốc nhanh — cần làm quen
- Giữ mức pin trên 20% — không để cạn pin hoàn toàn làm hại pin

## Xử lý sự cố pin xe điện
- Pin phồng/rò rỉ mùi khét: tắt xe, ra khỏi xe ngay, gọi cứu hộ
- Không tự tháo pin — nguy cơ điện giật và cháy nổ
- Xe điện bị cháy: khó dập hơn xe xăng — gọi 114, không dùng bình cứu hoả thông thường
- Không đỗ xe điện đang cháy gần công trình, xe khác
""",
    },
    {
        "title": "Quản lý căng thẳng và sức khoẻ tâm lý khi lái xe",
        "category": "safety",
        "content": """## Ảnh hưởng của stress đến lái xe
- Tăng nguy cơ phản ứng hung hăng với xe khác
- Giảm tập trung, bỏ sót tình huống nguy hiểm
- Tăng tốc độ không kiểm soát
- Quyết định sai trong tình huống khẩn cấp
- Mệt mỏi nhanh hơn — dễ buồn ngủ

## Dấu hiệu đang lái xe trong trạng thái stress cao
- Bóp còi liên tục, cáu với xe khác
- Đi quá sát xe phía trước
- Thay đổi tốc độ liên tục không lý do
- Cảm thấy tim đập nhanh, tay siết chặt vô lăng
- Nói to hoặc chửi thề trong xe

## Kỹ thuật giảm stress ngay trên xe
- Hít thở sâu: hít vào 4 giây, giữ 4 giây, thở ra 6 giây
- Hạ thấp vai, thả lỏng tay nắm vô lăng
- Bật nhạc nhẹ, hoặc podcast thay vì để im lặng
- Nhắc bản thân: "Đến chậm 5 phút còn hơn không đến"
- Dừng xe nghỉ nếu cảm thấy không kiểm soát được cảm xúc

## Xử lý khi bị xe khác khiêu khích
- Không đáp trả bằng hành động hung hăng
- Không nhìn chằm chằm vào tài xế kia
- Để xe đó vượt qua hoặc tách làn ra
- Nếu bị đe doạ: lái đến nơi đông người, đồn công an
- Không bao giờ ra khỏi xe tranh cãi trên đường

## Xây dựng thói quen lái xe khoẻ mạnh
- Xuất phát sớm hơn cần thiết — không để áp lực trễ giờ
- Nghe nhạc hoặc podcast yêu thích giúp thư giãn
- Không lái xe ngay sau khi cãi nhau, nhận tin buồn
- Nghỉ ngơi đủ giấc — mệt mỏi và stress liên quan chặt chẽ
- Tập thể dục thường xuyên — giảm stress nền tổng thể
""",
    },
]


FIREBASE_WEB_API_KEY = "AIzaSyDHSLms73ellnGeNlb2M2VpvupYzNWGIC0"


def get_token_by_password(email: str, password: str) -> str:
    """Đăng nhập qua Firebase REST API, trả về idToken."""
    url = (
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
        f"?key={FIREBASE_WEB_API_KEY}"
    )
    data = json.dumps({
        "email": email,
        "password": password,
        "returnSecureToken": True,
    }).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            return result["idToken"]
    except urllib.error.HTTPError as e:
        body = json.loads(e.read())
        msg = body.get("error", {}).get("message", str(e))
        raise SystemExit(f"Đăng nhập thất bại: {msg}")


def add_document(token: str, doc: dict) -> dict:
    data = json.dumps(doc).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/kb/documents",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def main():
    global BASE_URL
    parser = argparse.ArgumentParser(description="Seed KB documents")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--token", help="Firebase Admin ID token (hết hạn sau 1h)")
    group.add_argument("--email", help="Email admin (tự lấy token)")
    parser.add_argument("--password", help="Mật khẩu admin (dùng cùng --email)")
    parser.add_argument("--base-url", default=BASE_URL, help="Backend URL")
    args = parser.parse_args()

    BASE_URL = args.base_url.rstrip("/")

    if args.email:
        if not args.password:
            parser.error("--email yêu cầu --password")
        print(f"Đang đăng nhập với {args.email} ...")
        token = get_token_by_password(args.email, args.password)
        print("Đăng nhập thành công.\n")
    else:
        token = args.token

    print(f"Sẽ thêm {len(DOCUMENTS)} tài liệu vào {BASE_URL}/kb/documents\n")

    ok = 0
    for i, doc in enumerate(DOCUMENTS, 1):
        try:
            result = add_document(token, doc)
            chunks = result.get("chunks", "?")
            print(f"  [{i:2d}/{len(DOCUMENTS)}] ✔ {doc['title']!r} ({chunks} chunks)")
            ok += 1
        except Exception as e:
            print(f"  [{i:2d}/{len(DOCUMENTS)}] ✘ {doc['title']!r} — {e}")

    print(f"\nHoàn tất: {ok}/{len(DOCUMENTS)} tài liệu đã thêm.")
    if ok < len(DOCUMENTS):
        sys.exit(1)


if __name__ == "__main__":
    main()
