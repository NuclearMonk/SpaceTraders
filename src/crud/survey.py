
from sqlalchemy import select
from login import engine
from models.survey import SurveyDepositModel, SurveyModel
from schemas.survey import Survey, SurveyDeposit
from sqlalchemy.orm import Session

from utils.utils import utcnow



def store_survey(survey: Survey) -> Survey:
    with Session(engine) as session:
        new_survey = SurveyModel()
        new_survey.signature = survey.signature
        new_survey.symbol = survey.symbol
        new_survey.expiration = survey.expiration
        new_survey.size = survey.size
        new_survey.deposits = [_store_deposit(sd) for sd in survey.deposits]
        session.add(new_survey)
        session.commit()
        return _survey_to_schema(new_survey)

def get_valid_surveys(symbol: str):
    with Session(engine) as session:
        stmt =select(SurveyModel).where(SurveyModel.symbol == symbol, SurveyModel.expiration < utcnow())
        return [_survey_to_schema(survey) for survey in session.scalars(stmt).all()]

def _survey_to_schema(survey: SurveyModel) -> Survey:
    if not Survey:
        return None
    return Survey(signature=survey.signature,
                  symbol=survey.symbol,
                  deposits=[SurveyDeposit(symbol=sd.symbol) for sd in survey.deposits],
                  expiration=survey.expiration,
                  size=survey.deposits
                  )

def _store_deposit(deposit: SurveyDeposit)->SurveyDepositModel:
    new_deposit = SurveyDepositModel()
    new_deposit.symbol = deposit.symbol
    return new_deposit    



