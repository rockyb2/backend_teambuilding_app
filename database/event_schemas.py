from datetime import date as Date, datetime
from decimal import Decimal
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid', str_strip_whitespace=True)


class EventRead(EventSchema):
    id: int
    titre: str
    date: Date | None
    lieu: str | None
    tarif: Decimal | None
    description: str | None


class InscriptionEventCreate(EventSchema):
    evenement: str = Field(min_length=1, max_length=255)
    prenom: str = Field(min_length=1, max_length=120)
    nom: str = Field(min_length=1, max_length=120)
    telephone: str = Field(min_length=1, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    nombre_participants: int = Field(strict=True, ge=1, le=2147483647)
    note: str | None = Field(default=None, max_length=5000)

    @field_validator('email', mode='before')
    @classmethod
    def optional_email(cls, value):
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        if not isinstance(value, str) or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value.strip()):
            raise ValueError('Adresse email invalide')
        return value.strip()

    @field_validator('telephone')
    @classmethod
    def valid_phone(cls, value):
        digits = re.sub(r'\D', '', value)
        if not re.fullmatch(r'[+\d\s().-]+', value) or not 7 <= len(digits) <= 15:
            raise ValueError('Numéro de téléphone invalide')
        return value


class InscriptionEventReceipt(EventSchema):
    id: int


class InscriptionEventRead(InscriptionEventCreate):
    id: int
    date_inscription: datetime