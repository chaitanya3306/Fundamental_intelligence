import os
import pandas as pd
from jinja2.filters import select_or_reject
from sqlalchemy.orm import Session
from src.database.session import SessionLocal
from src.database.models import Company,FinancialStatement


# --config---

# getting base_dir

BASE_DIR=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SILVER_DATA_DIR=os.path.join(BASE_DIR,"data","silver")

def get_or_create_company(db:Session,ticker:str):
    # ensure if company exists in the company table
    company=db.query(Company).filter(Company.ticker==ticker).first()
    if company:
        return company.company_id
    # if not found then create a new:
    print(f"creating new company record for {ticker}.....")
    new_company=Company(ticker=ticker,
                        sector="Unknown",
                        industry="Unknown")
    db.add(new_company)
    db.commit()
    db.refresh(new_company)

    return new_company.company_id
def load_csv_to_db(db:Session,ticker:str,filename:str,company_id:int):
#     this function loads single Silver.csv transforms it from
#     WIDE to LONG and saves to DB

#     first lets do load the df

    filepath=os.path.join(SILVER_DATA_DIR,ticker,filename)
    if not os.path.exists(filepath):
        return

    df=pd.read_csv(filepath,index_col=0)

#   now lets transform it to long
    df_reset=df.reset_index()
    metric_col_name=df_reset.columns[0]
    long_df=df_reset.melt(
        id_vars=[metric_col_name],
        var_name="year",
        value_name="value"
    )
    print(f"inserting {filename} data......")
    for _,row in long_df.iterrows():
#         create the statement
        statement =FinancialStatement(
            company_id=company_id,
            year=int(str(row['year'])[:4]),
            metric_name=row[metric_col_name],
            value=float(row['value'])
        )
        db.add(statement)

def run_loader(ticker_list):
    db=SessionLocal()
    try:
        for tick in ticker_list:
            company_id=get_or_create_company(db,tick)
    #       get tick folder
            ticker_folder=os.path.join(SILVER_DATA_DIR,tick)
            if not os.path.exists(ticker_folder):
                continue
            for file in os.listdir(ticker_folder):
                if file.endswith(".csv"):
                    load_csv_to_db(db,tick,file,company_id)
            db.commit()
    except Exception as e:
        print(f"critical exception occurs while loading : {e} ")
        db.rollback()
    finally:
        db.close()

if __name__=="__main__":
    TARGET_TICKERS= ["TCS.NS", "RELIANCE.NS", "INFY.NS",
                   "HDFCBANK.NS", "ICICIBANK.NS"]


    run_loader(TARGET_TICKERS)






