from fastapi import APIRouter, Depends
from firebase_admin import auth as firebase_auth

from app.core.security import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/verify")
def verify_token(user: dict = Depends(get_current_user)):
    return {"status": "success", "uid": user["uid"]}


@router.get("/me")
def get_me(user: dict = Depends(get_current_user)):
    return user


@router.get("/check-email")
def check_email(email: str):
    """Email đã có tài khoản đăng nhập chưa — app gọi TRƯỚC khi tự nhờ
    Firebase gửi mail đặt lại mật khẩu (luồng quên mật khẩu), để báo rõ nếu
    email chưa từng đăng ký thay vì im lặng như Firebase mặc định làm (chống
    dò email trên dịch vụ công khai). Chấp nhận đánh đổi lộ "email này có tồn
    tại hay không" vì đây là app nội bộ công ty, không phải dịch vụ đại
    chúng — vẫn có rate limit mặc định toàn cục chặn dò hàng loạt. Không yêu
    cầu đăng nhập (gọi trước khi đăng nhập được)."""
    try:
        firebase_auth.get_user_by_email(email)
        return {"exists": True}
    except firebase_auth.UserNotFoundError:
        return {"exists": False}
    except ValueError:
        # Email không hợp lệ về mặt cú pháp (firebase_auth tự validate).
        return {"exists": False}
