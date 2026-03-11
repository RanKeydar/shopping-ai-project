from pydantic import BaseModel, EmailStr, ConfigDict


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    country: str
    city: str
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    country: str
    city: str
    username: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int | None = None