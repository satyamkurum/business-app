from pydantic import BaseModel, Field, BeforeValidator
from typing import Annotated, Literal

# This is our custom type that teaches Pydantic how to handle MongoDB's ObjectId.
# It tells Pydantic: "Before you validate this field, just convert the value to a string."
PyObjectId = Annotated[str, BeforeValidator(str)]

class UserBase(BaseModel):
    """Shared base attributes for a user."""
    firebase_uid: str
    email: str
    name: str | None = None
    role: Literal["owner", "customer"] = "customer"

class User(UserBase):
    """
    Schema for reading a user from the database.
    This model includes the ID and is configured to handle MongoDB's '_id'.
    """
    # We use our custom PyObjectId type for the id field.
    id: PyObjectId = Field(alias="_id")

    class Config:
        # Allows Pydantic to populate the model using field names or aliases.
        populate_by_name = True
        # Allows Pydantic to create a model instance from an ORM object (like the one from Motor).
        from_attributes = True
