from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import select

from sqlalchemy import Column, Date, Integer, String, Float, ForeignKey, DateTime,UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
Base=declarative_base()


# this will store the static info about the company
class Company(Base):
    __tablename__="companies"
    company_id=Column(Integer,primary_key=True,autoincrement=True)
    ticker=Column(String,unique=True,nullable=False,index=True)
    sector = Column(String) # e.g., "IT Services"
    industry = Column(String) # e.g., "Software"
    shares_outstanding=Column(Float,nullable=True)
    current_price=Column(Float,nullable=True)
    last_updated = Column(DateTime, default=datetime.now(), onupdate=datetime.utcnow, nullable=False)

    #relationships:
    # this allow us to get the data from another table in pythonic way like company.statements
    statements=relationship("FinancialStatement",back_populates="company")

# it stores the actual variable data or numbers
class FinancialStatement(Base):
    __tablename__ = 'financial_statements'


    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "date",
            "statement_type",
            "metric_name",
            name="uq_financial_statement_observation",
        ),
    )




    statement_id=Column(Integer,primary_key=True,autoincrement=True)
    company_id=Column(Integer,ForeignKey('companies.company_id'))
    date=Column(Date,nullable=False,index=True)
    statement_type=Column(String,nullable=False)
    metric_name=Column(String,nullable=False)
    value=Column(Float,nullable=False)

    company=relationship("Company", back_populates="statements")

    @hybrid_property
    def company_ticker(self):
        """Return the ticker symbol of the related company.

        This hybrid property allows ORM queries such as
        ``filter_by(company_ticker='BADCO')`` to work by generating a subquery
        that selects the ticker from the ``companies`` table based on the
        ``company_id`` foreign key.
        """
        return self.company.ticker if self.company else None

    @company_ticker.expression
    def company_ticker(cls):
        return (
            select(Company.ticker)
            .where(Company.company_id == cls.company_id)
            .scalar_subquery()
        )

