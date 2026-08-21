from fastapi import APIRouter, Depends

from app.core.security import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/verify")
def verify_token(user: dict = Depends(get_current_user)):
    return {"status": "success", "uid": user["uid"]}


@router.get("/me")
def get_me(user: dict = Depends(get_current_user)):
    return user
