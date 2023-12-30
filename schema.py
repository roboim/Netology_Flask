import pydantic


class CreateAdvertisement(pydantic.BaseModel):
    title: str
    description: str
    user: str
