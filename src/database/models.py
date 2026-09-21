from sqlalchemy import Column, Integer, String, Float, ForeignKey, nulls_last
from sqlalchemy.orm import declarative_base, relationship

Base=declarative_base()


# this will store the static info about the company
class Company(Base):
    __tablename__="companies"
    company_id=Column(Integer,primary_key=True,autoincrement=True)
    ticker=Column(String,unique=True,nullable=False)
    sector = Column(String) # e.g., "IT Services"
    industry = Column(String) # e.g., "Software"

    #relationships:
    # this allow us to get the data from another table in pythonic way like company.statements
    statements=relationship("FinancialStatement",back_populates="company")

# it stores the actual variable data or numbers
class FinancialStatement(Base):
    __tablename__ = 'financial_statements'
    statement_id=Column(Integer,primary_key=True,autoincrement=True)
    company_id=Column(Integer,ForeignKey('companies.company_id'))
    year=Column(Integer,nullable=False)
    metric_name=Column(String,nullable=False)
    value=Column(Float,nullable=False)

    # relationships:
    company=relationship("Company",back_populates="statements")
