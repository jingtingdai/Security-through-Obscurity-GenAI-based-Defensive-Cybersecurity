from fastapi import FastAPI, UploadFile, HTTPException, status, Depends
from pydantic import BaseModel
from typing import List, Annotated
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
import pandas as pd
from io import StringIO
from obfuscation import obfuscate_date, obfuscate_number, obfuscate_str, deobfuscate_date, deobfuscate_number, deobfuscate_str
from sqlalchemy import func
from fastapi.middleware.cors import CORSMiddleware
import math, random
from auth import get_current_user, router
from dependency import db_dependency
import logging
from datetime import datetime

# Configure logging for security alerts
# Create file handler with immediate flush to ensure Logstash can read new entries
# Use a custom handler that flushes after each write
class FlushingFileHandler(logging.FileHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

file_handler = FlushingFileHandler('frontend_access.log')
file_handler.setLevel(logging.INFO)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        file_handler,
        logging.StreamHandler()
    ]
)
security_logger = logging.getLogger('security')

app = FastAPI()
app.include_router(router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3002", "http://localhost:8080", "http://localhost:8081"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



models.Base.metadata.create_all(bind=engine)

# represent number of rows for 1 true data. e.g if for every 1 true data there will be another 9 fake data, then it will be set 10
dataPerTrue = 10

user_dependency = Annotated[dict, Depends(get_current_user)]

# Optional authentication function
def get_optional_user():
    """Optional user dependency that returns None if not authenticated"""
    from fastapi import Request
    from jose import JWTError, jwt
    from auth import SECRET_KEY, ALGORITHM
    
    async def optional_user_dependency(request: Request):
        try:
            # Try to get the authorization header
            authorization = request.headers.get("Authorization")
            security_logger.info(f"DEBUG: Authorization header = {authorization[:50] if authorization else 'None'}...")
            
            if not authorization or not authorization.startswith("Bearer "):
                security_logger.info("DEBUG: No valid Authorization header found")
                return None
            
            token = authorization.split(" ")[1]
            security_logger.info(f"DEBUG: Token extracted, length = {len(token)}")
            
            # Decode JWT token manually (similar to get_current_user)
            # First try normal decode (for valid tokens)
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            except JWTError as e:
                # If token is expired, try to decode without verification for logging purposes
                security_logger.info(f"DEBUG: JWTError during decode - {str(e)}, attempting unverified decode for logging")
                try:
                    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_signature": False, "verify_exp": False})
                    security_logger.info("DEBUG: Successfully decoded expired token for logging purposes")
                except Exception as decode_error:
                    security_logger.info(f"DEBUG: Failed to decode even without verification - {str(decode_error)}")
                    return None
            
            username: str = payload.get("sub")
            user_id: str = payload.get("id")
            security_logger.info(f"DEBUG: Decoded payload - username={username}, user_id={user_id}")
            
            if username is None or user_id is None:
                security_logger.info("DEBUG: Username or user_id is None in payload")
                return None
            
            result = {"username": username, "id": user_id}
            security_logger.info(f"DEBUG: Returning user object: {result}")
            return result
        except JWTError as e:
            security_logger.info(f"DEBUG: JWTError - {str(e)}")
            return None
        except HTTPException as e:
            security_logger.info(f"DEBUG: HTTPException - {str(e)}")
            return None
        except Exception as e:
            security_logger.info(f"DEBUG: Unexpected exception - {type(e).__name__}: {str(e)}")
            return None
    
    return Depends(optional_user_dependency)


@app.get("/", status_code=status.HTTP_200_OK)
async def user(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")
    return {"User": user}


@app.post("/upload-csv/")
async def upload_csv(file: UploadFile):
    #Check if file is csv
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400,detail="Only csv file allowed")

    raw = await file.read()
    df = pd.read_csv(StringIO(raw.decode("utf-8-sig", errors="replace")), engine="python", on_bad_lines="skip")

    if df.empty:
        raise HTTPException(status_code=400, detail="CSV file is empty or contains no data")

    # read fake data
    data_quantity = dataPerTrue * len(df)
    fake_file_name = f"/Users/jingtingdai/Desktop/Master_Thesis/learning/test/data/synthetic_{data_quantity}_rows.csv"
    fake_df = pd.read_csv(fake_file_name)
    
    
    db: Session = SessionLocal()
    try:
        max_row_number = db.query(func.max(models.Test.row_number)).scalar()
        if max_row_number is None:
            max_row_number = 0
    except:
        max_row_number = 0

    #check data model
    try:
        records = df.to_dict(orient="records")
       
        # Map to ORM objects
        objects = []
        true_row_number = get_row_number(len(records))
        idx  = 0
        for i in range(data_quantity):
            cur_row_number = max_row_number + i+1 
            if cur_row_number not in true_row_number:
                cur_obj = get_model_data(cur_row_number, fake_df.loc[i].to_dict())
            else:
                cur_obj = get_model_data(cur_row_number, records[idx])
                idx += 1
            objects.append(cur_obj)
     

        db.add_all(objects)
        db.commit()
        return {"status": "success", "rows": len(objects)}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}")
    finally:
        db.close()

def check_and_log_row_access(requested_row: int, user: str = "unknown", log_authorized_access: bool = True):
    """
    Check if a row number is authorized and log access attempts.
    Returns True if authorized, False if unauthorized.
    
    Args:
        requested_row: The row number being accessed
        user: The user making the request
        log_authorized_access: If True, also logs when authorized users access fake rows
    
    Returns:
        True if row is in true_row_number, False otherwise
    """
    true_row_number = get_row_number(0)
    is_authorized = requested_row in true_row_number
    
    # Log access attempt with frontend_access tag and row information
    security_logger.info(
        f"FRONTEND_ACCESS - accessed_row:{requested_row} "
        f"authorized_rows:{true_row_number} "
        f"is_authorized:{is_authorized} "
        f"requested_by:{user} timestamp:{datetime.now().isoformat()}"
    )
    
    if not is_authorized:
        # Log unauthorized access (for security monitoring)
        security_logger.warning(
            f"UNAUTHORIZED_ACCESS - row_number:{requested_row} "
            f"authorized_rows:{true_row_number} requested_by:{user} timestamp:{datetime.now().isoformat()}"
        )
        
        # Also log as "FAKE_DATA_ACCESS" for auditing authorized users
        if log_authorized_access:
            security_logger.info(
                f"FAKE_DATA_ACCESS - row_number:{requested_row} "
                f"is_fake_row:true authorized_rows:{true_row_number} "
                f"requested_by:{user} timestamp:{datetime.now().isoformat()}"
            )
        
        return False
    else:
        # Log access to authorized/real data rows
        if log_authorized_access:
            security_logger.info(
                f"REAL_DATA_ACCESS - row_number:{requested_row} "
                f"is_fake_row:false authorized_rows:{true_row_number} "
                f"requested_by:{user} timestamp:{datetime.now().isoformat()}"
            )
        return True

@app.get("/real-data/")
async def read_real(user = get_optional_user()):
    db: Session = SessionLocal()
    
    # Debug logging
    security_logger.info(f"DEBUG: user object = {user}, type = {type(user)}")
    
    username = "unknown"
    if user:
        security_logger.info(f"DEBUG: user dict = {user}, username field = {user.get('username', 'NOT_FOUND')}")
        username = user.get("username", "unknown")
    else:
        security_logger.info("DEBUG: user is None or falsy")

    true_row_number = get_row_number(0)
    
    # Log frontend access with all accessed rows
    security_logger.info(
        f"FRONTEND_ACCESS - accessing_rows:{true_row_number} "
        f"requested_by:{username} timestamp:{datetime.now().isoformat()}"
    )
    
    result = db.query(models.Test).filter(models.Test.row_number.in_(true_row_number)).all()

    real_data = []

    for i in result:
        cur_dict = {}
        cur_dict["Shipment_ID"] = deobfuscate_str(i.Shipment_ID)
        cur_dict["Origin_Warehouse"] = deobfuscate_str(i.Origin_Warehouse)
        cur_dict["Shipment_Date"] = deobfuscate_date(i.Shipment_Date)
        cur_dict["Weight_kg"] = deobfuscate_number(i.Weight_kg)
        cur_dict["Transit_Days"] = deobfuscate_number(i.Transit_Days)
        real_data.append(cur_dict)

    return real_data

@app.get("/query-row/{row_number}")
async def query_specific_row(row_number: int, user = get_optional_user()):
    """
    Query a specific row by row_number. 
    This endpoint logs unauthorized access if the row is not in true_row_number.
    """
    db: Session = SessionLocal()
    
    username = "unknown"
    if user:
        username = user.get("username", "unknown")
    
    # Check if this row access is authorized
    is_authorized = check_and_log_row_access(row_number, username)
    
    result = db.query(models.Test).filter(models.Test.row_number == row_number).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Row not found")
    
    # Only return deobfuscated data if authorized
    if is_authorized:
        cur_dict = {
            "row_number": result.row_number,
            "Shipment_ID": deobfuscate_str(result.Shipment_ID),
            "Origin_Warehouse": deobfuscate_str(result.Origin_Warehouse),
            "Shipment_Date": str(deobfuscate_date(result.Shipment_Date)),
            "Weight_kg": float(deobfuscate_number(result.Weight_kg)),
            "Transit_Days": int(deobfuscate_number(result.Transit_Days))
        }
        return cur_dict
    else:
        # Return obfuscated data or limited info
        raise HTTPException(
            status_code=403, 
            detail="Unauthorized access to this row"
        )


def get_model_data(mapped_row, rec):
    
    sh_id = rec.get("Shipment_ID")
    wh = rec.get("Origin_Warehouse")
    date = rec.get("Shipment_Date")
    weight = rec.get("Weight_kg")
    days = rec.get("Transit_Days")
    mapped_id = obfuscate_str(sh_id)
    mapped_wh = obfuscate_str(wh)
    mapped_date = obfuscate_date(date)
    mapped_weight = obfuscate_number(weight)
    mapped_days = obfuscate_number(days)
    
    cur_obj = models.Test(row_number = mapped_row,
        Shipment_ID=mapped_id,
        Origin_Warehouse=mapped_wh,
        Shipment_Date=mapped_date,
        Weight_kg=mapped_weight,
        Transit_Days=mapped_days)
    return cur_obj

# insert_rows represent how many rows will insert, if query it will be 0
def get_row_number(insert_rows:int):
    #get true data row number
    db: Session = SessionLocal()
    try:
        max_row_number =db.query(func.max(models.Test.row_number)).scalar()
    except:
        max_row_number = 0
    if max_row_number is None:
        true_number_of_rows = 0
    else:
        true_number_of_rows = max_row_number // dataPerTrue + 1
    
    scale = math.ceil(math.log(dataPerTrue, 10))
    """with open("pi.txt") as f:
        digits = f.read((true_number_of_rows+insert_rows)*scale)"""
    seed = 314
    random.seed(seed)
    true_row_number = []
    if insert_rows:
        cur_base=true_number_of_rows
        #digits = digits[true_number_of_rows*scale:]
        for i in range(true_number_of_rows*scale):
            random.randint(0, 9)
    else:
        cur_base = 0
    for i in range(insert_rows if insert_rows else true_number_of_rows):
        cur_digits = 0
        digit_base = 1
        for j in range(scale):
            cur_digits += digit_base * random.randint(0, 9)
            digit_base *= 10
        true_row_number.append(cur_base*dataPerTrue+int(cur_digits))
        cur_base+=1
    

    return true_row_number




@app.get("/config")
async def get_config():
    return {"dataPerTrue": dataPerTrue}