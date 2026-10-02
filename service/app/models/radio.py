from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator

# App Android bản release chỉ cho phép http:// (không mã hoá) tới các domain
# khai báo trong mobile/android/app/src/main/res/xml/network_security_config.xml.
# Kênh http ở domain khác sẽ không phát được trên máy tài xế -> chặn ngay từ lúc nhập.
CLEARTEXT_HOSTS = {"stream.voh.com.vn"}


class RadioStationIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    frequency: Optional[str] = Field(default=None, max_length=40)
    stream_url: str = Field(min_length=1, max_length=500)
    enabled: bool = True
    order: int = Field(default=0, ge=0, le=999)

    @field_validator("name", "stream_url")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Không được để trống")
        return v

    @field_validator("frequency")
    @classmethod
    def _strip_optional(cls, v: Optional[str]) -> Optional[str]:
        return (v or "").strip() or None

    @field_validator("stream_url")
    @classmethod
    def _check_url(cls, v: str) -> str:
        parsed = urlparse(v)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise ValueError("Link phát phải bắt đầu bằng http:// hoặc https://")
        if parsed.scheme == "http" and parsed.hostname not in CLEARTEXT_HOSTS:
            raise ValueError(
                "Link http:// chỉ hỗ trợ stream.voh.com.vn — kênh khác cần dùng https://"
            )
        return v


class RadioToggle(BaseModel):
    enabled: bool
