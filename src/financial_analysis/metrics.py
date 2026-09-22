
from src.database.session import SessionLocal
from sqlalchemy.orm import Session
from src.database.models import FinancialStatement
from src.financial_analysis.mapping import METRIC_MAP


def get_metric_value(db:Session,company_id:int,year:int,standard_key:str):

    # now we have to get all the possible names for this metric from the map
    possible_names=METRIC_MAP.get(standard_key,[])
    # loop through all possible names until we found one in db
    for name in possible_names:
        result=db.query(FinancialStatement).filter(
            FinancialStatement.company_id==company_id,
            FinancialStatement.year==year,
            FinancialStatement.metric_name==name
        ).first()
        if result is not None:
            return result.value
    return 0.0




def get_ratios(db:Session,company_id:int,year:int):
    # Step 1: Fetch all required metrics once
    metrics = {
        "Net Income": get_metric_value(db, company_id, year, "net_income"),
        "Total Revenue": get_metric_value(db, company_id, year, "revenue"),
        "Stockholders Equity": get_metric_value(db, company_id, year, "equity"),
        "Total Assets": get_metric_value(db, company_id, year, "total_assets"),
        "Total Debt": get_metric_value(db, company_id, year, "total_debt"),
    }

    # Step 2: Define calculation map
    calculation_map = {
        "Net_Profit_Margin": lambda m: None if m["Total Revenue"] == 0 else m["Net Income"] / m["Total Revenue"],
        "ROE": lambda m: None if m["Stockholders Equity"] == 0 else m["Net Income"] / m["Stockholders Equity"],
        "Debt_to_Equity": lambda m: None if m["Stockholders Equity"] == 0 else m["Total Debt"] / m[
            "Stockholders Equity"],
        "Asset_Turnover": lambda m: None if m["Total Assets"] == 0 else m["Total Revenue"] / m["Total Assets"],
    }

    # step 3 : calcualte ratios
    ratios={name:func(metrics) for name,func in calculation_map.items()}
    return ratios




def calculate_growth(db:Session,company_id:int,metric_key:str,start_year:int,end_year:int):
    val_start=get_metric_value(db,company_id,start_year,metric_key)
    val_end=get_metric_value(db,company_id,end_year,metric_key)

    n=end_year-start_year

    if val_start<=0 or n<=0:
        return None


#   calcualte the CAGR:
    CAGR=(val_end/val_start)**(1/n)-1

    return CAGR




if __name__=="__main__":
    db=SessionLocal()
    try:
        print(get_ratios(db,1,2026))
        print("\n")
        print(calculate_growth(db,1,"revenue",2024,2026))
    except Exception as e:
        print(f"bug founded as : {e}")
    finally:
        db.close()

