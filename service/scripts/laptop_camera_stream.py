"""Phát camera laptop thành 1 luồng qua mạng LAN — giả lập "camera gắn trên xe"
để demo: app điện thoại nhập đường dẫn của luồng này và giám sát buồn ngủ
trên hình từ laptop thay vì camera trước của điện thoại.

    D:\\WEBTAIXE\\venv\\Scripts\\python.exe scripts\\laptop_camera_stream.py
    (tuỳ chọn: --camera 1 --port 8081)

Điện thoại và laptop phải cùng mạng WiFi. Script in ra đường dẫn dạng
http://192.168.x.x:8081 — nhập đường dẫn này vào app (Giám sát › biểu tượng
camera › Camera ngoài). Mở đường dẫn đó trên trình duyệt để xem thử luồng.

Đường dẫn cung cấp:
    /              trang xem thử
    /video         luồng MJPEG (trình duyệt xem trực tiếp)
    /snapshot.jpg  khung hình mới nhất (app lấy ~6 lần/giây để phân tích)
    /clip?seconds=10  video WebM: 5 giây TRƯỚC + 5 giây SAU lúc gọi (app gọi
                   khi báo động, gửi lên server làm clip sự cố)
    /health        tình trạng camera (app dùng để kiểm tra kết nối)

Chỉ dùng cho demo trong mạng nội bộ: không có mật khẩu, không mã hoá.
"""

import argparse
import json
import os
import socket
import tempfile
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import cv2

FPS = 15  # tốc độ đọc camera
BUFFER_SECONDS = 10  # giữ 10 giây gần nhất để cắt clip có cả đoạn trước báo động
JPEG_QUALITY = 80


class CameraWorker:
    """Đọc camera liên tục ở luồng riêng, giữ khung mới nhất + bộ đệm vòng."""

    def __init__(self, index: int, width: int, height: int):
        backend = cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY
        self.cap = cv2.VideoCapture(index, backend)
        if not self.cap.isOpened():
            raise SystemExit(f"Không mở được camera số {index}. Thử --camera 1, hoặc tắt ứng dụng khác đang dùng camera.")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.lock = threading.Lock()
        self.latest = None
        self.latest_jpeg = None
        self.buffer = deque(maxlen=FPS * BUFFER_SECONDS)  # (timestamp, frame)
        self.frames = 0
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        interval = 1.0 / FPS
        while self.running:
            started = time.time()
            ok, frame = self.cap.read()
            if ok:
                ok_jpg, jpg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
                with self.lock:
                    self.latest = frame
                    if ok_jpg:
                        self.latest_jpeg = jpg.tobytes()
                    self.buffer.append((started, frame))
                    self.frames += 1
            time.sleep(max(0.0, interval - (time.time() - started)))

    def jpeg(self):
        with self.lock:
            return self.latest_jpeg

    def clip(self, seconds: float) -> bytes:
        """Ghép `seconds/2` giây đã qua + chờ thêm `seconds/2` giây tới, xuất WebM (VP8)."""
        half = seconds / 2
        called = time.time()
        time.sleep(half)
        with self.lock:
            frames = [f for t, f in self.buffer if called - half <= t <= called + half]
        if not frames:
            raise RuntimeError("Chưa có khung hình nào")
        h, w = frames[0].shape[:2]
        fd, path = tempfile.mkstemp(suffix=".webm")
        os.close(fd)
        try:
            writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"VP80"), FPS, (w, h))
            for f in frames:
                writer.write(f)
            writer.release()
            with open(path, "rb") as fh:
                return fh.read()
        finally:
            os.remove(path)

    def stop(self):
        self.running = False
        time.sleep(0.2)
        self.cap.release()


PAGE = """<!doctype html><html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Camera laptop – luồng demo</title>
<style>body{font-family:system-ui,sans-serif;margin:24px;background:#f8fafc;color:#0f172a}
img{max-width:100%%;border-radius:12px;background:#000}code{background:#e2e8f0;padding:2px 6px;border-radius:4px}</style>
</head><body><h2>Camera laptop đang phát</h2>
<p>Nhập đường dẫn sau vào app điện thoại (Giám sát › Nguồn camera › Camera ngoài):</p>
<p><code>%s</code></p><img src="/video" alt="Luồng camera"></body></html>"""


def make_handler(cam: CameraWorker, public_url: str):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):  # gọn log: chỉ in lỗi
            if args and str(args[1]).startswith(("4", "5")):
                super().log_message(fmt, *args)

        def _send(self, code, body: bytes, ctype: str):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            url = urlparse(self.path)
            if url.path == "/":
                self._send(200, (PAGE % public_url).encode("utf-8"), "text/html; charset=utf-8")
            elif url.path == "/health":
                frame = cam.latest
                h, w = frame.shape[:2] if frame is not None else (0, 0)
                body = {"ok": frame is not None, "width": w, "height": h, "fps": FPS, "frames": cam.frames}
                self._send(200, json.dumps(body).encode(), "application/json")
            elif url.path == "/snapshot.jpg":
                jpg = cam.jpeg()
                if jpg is None:
                    self._send(503, b"camera chua san sang", "text/plain")
                else:
                    self._send(200, jpg, "image/jpeg")
            elif url.path == "/video":
                self.send_response(200)
                self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                try:
                    while True:
                        jpg = cam.jpeg()
                        if jpg:
                            self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\n")
                            self.wfile.write(f"Content-Length: {len(jpg)}\r\n\r\n".encode())
                            self.wfile.write(jpg + b"\r\n")
                        time.sleep(1.0 / FPS)
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    pass
            elif url.path == "/clip":
                try:
                    seconds = float(parse_qs(url.query).get("seconds", ["10"])[0])
                    seconds = min(max(seconds, 2.0), float(BUFFER_SECONDS))
                    self._send(200, cam.clip(seconds), "video/webm")
                except Exception as e:  # noqa: BLE001 — trả lỗi rõ cho app
                    self._send(500, str(e).encode("utf-8"), "text/plain; charset=utf-8")
            else:
                self._send(404, b"not found", "text/plain")

    return Handler


def lan_ip() -> str:
    """IP LAN của laptop (không gửi gói tin nào ra ngoài, chỉ hỏi bảng định tuyến)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def main():
    parser = argparse.ArgumentParser(description="Phát camera laptop cho app giám sát (demo).")
    parser.add_argument("--camera", type=int, default=0, help="số thứ tự camera (mặc định 0)")
    parser.add_argument("--port", type=int, default=8081)
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    args = parser.parse_args()

    cam = CameraWorker(args.camera, args.width, args.height)
    public_url = f"http://{lan_ip()}:{args.port}"
    server = ThreadingHTTPServer(("0.0.0.0", args.port), make_handler(cam, public_url))
    print("Camera laptop đang phát.")
    print(f"  Đường dẫn cho app điện thoại : {public_url}")
    print(f"  Máy ảo Android dùng          : http://10.0.2.2:{args.port}")
    print(f"  Xem thử trên trình duyệt     : http://localhost:{args.port}")
    print("Nhấn Ctrl + C để dừng.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        cam.stop()


if __name__ == "__main__":
    main()
