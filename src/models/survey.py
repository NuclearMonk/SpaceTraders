from typing import List
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship


from . import Base


class SurveyDepositModel(Base):
    __tablename__ = 'survey_deposits'
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    survey_signature :  Mapped[str] = mapped_column(
        Text(20), ForeignKey('surveys.signature'))
    survey : Mapped['SurveyModel'] = relationship(back_populates='deposits')
    symbol : Mapped[str]



class SurveyModel(Base):
    __tablename__ = 'surveys'
    signature: Mapped[str] = mapped_column(Text(20), primary_key=True)
    symbol: Mapped[str] = mapped_column(Text(20))
    deposits: Mapped[List[SurveyDepositModel]] = relationship(back_populates='survey')
    expiration = Column(DateTime(timezone=False))
    size: Mapped[str] = mapped_column(Text(20))
