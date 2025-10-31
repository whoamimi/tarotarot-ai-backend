""" taro/api/astrology.py """

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse

from ..schemas.user import User

astrology_router = ApiRouter()

@astrology_router.post(
    '/user_astrology/',
    response_class=JSONResponse,
    response_model_exclude_none=True,
    response_model=User,  # if you want automatic output validation
)
async def user_astrology(
    user: User = Body(
        ...,
        example={
            "id": "12345",
            "username": "whoamimi",
            "first_name": "john",
            "last_name": "snow",
            "birth_date": "20-02-1994",
            "birth_time": "03:15",
            "birth_place": "Australia/Sydney",
            "gender": "male"
        }
    )
):
    """
        Fetches user's astrology readings.
    """
    user.get_astrology()
    return JSONResponse(content=user.model_dump(), status_code=200)
