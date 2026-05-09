from pydantic import BaseModel, EmailStr


class FeedbackCreate(BaseModel):
    customer_name: str
    email: EmailStr
    product_slug: str
    rating: int
    message: str

