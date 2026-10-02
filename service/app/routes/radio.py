from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_active_driver, get_current_admin
from app.models.radio import RadioStationIn, RadioToggle
from app.services import radio_service

# Web admin: thêm/sửa/xoá/bật tắt kênh radio.
router = APIRouter(
    prefix="/radio",
    tags=["radio (web admin)"],
    dependencies=[Depends(get_current_admin)],
)

# App tài xế: lấy danh sách kênh đang bật, báo phát.
self_router = APIRouter(prefix="/radio", tags=["radio (app tài xế)"])


# ── App tài xế ───────────────────────────────────────────────────────────
@self_router.get("/stations")
def list_stations(_: dict = Depends(get_current_active_driver)):
    return radio_service.list_enabled()


@self_router.post("/stations/{station_id}/play")
def register_play(station_id: str, _: dict = Depends(get_current_active_driver)):
    if not radio_service.register_play(station_id):
        raise HTTPException(
            status_code=403, detail="Kênh này đã bị quản trị viên tắt"
        )
    return {"status": "ok"}


# ── Web admin ────────────────────────────────────────────────────────────
@router.get("/stations/all")
def list_all_stations():
    return radio_service.list_all()


@router.post("/stations", status_code=201)
def create_station(payload: RadioStationIn):
    return radio_service.create_station(payload.model_dump())


@router.put("/stations/{station_id}")
def update_station(station_id: str, payload: RadioStationIn):
    station = radio_service.update_station(station_id, payload.model_dump())
    if station is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy kênh")
    return station


@router.put("/stations/{station_id}/toggle")
def toggle_station(station_id: str, payload: RadioToggle):
    station = radio_service.update_station(station_id, {"enabled": payload.enabled})
    if station is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy kênh")
    return station


@router.delete("/stations/{station_id}", status_code=204)
def delete_station(station_id: str):
    if not radio_service.delete_station(station_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy kênh")
