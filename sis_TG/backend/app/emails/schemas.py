from pydantic import BaseModel, EmailStr


class SendContactEmailRequest(BaseModel):
    restaurant_id: int
    to_email: EmailStr
    subject: str
    body: str


class SendContactEmailResponse(BaseModel):
    success: bool
    message: str
