
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, Integer, Text
from models import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship

from utils.utils import utcnow


class RequestModel(Base):
    __tablename__ = "requests"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(Text)
    method: Mapped[str] = mapped_column(Text)
    body: Mapped[Optional[str]] = mapped_column(Text)
    params: Mapped[Optional[str]] = mapped_column(Text)
    response: Mapped['ResponseModel'] = relationship(back_populates='request')
    timestamp: Mapped[DateTime] = mapped_column(
        DateTime(False), default=utcnow)


class ResponseModel(Base):
    __tablename__ = "responses"
    id: Mapped[int] = mapped_column(
        ForeignKey(RequestModel.id), primary_key=True)
    code: Mapped[int] = mapped_column(Integer)
    body: Mapped[Optional[str]] = mapped_column(Text)
    request: Mapped[RequestModel] = relationship(back_populates='response')
    timestamp: Mapped[DateTime] = mapped_column(
        DateTime(False), default=utcnow)
