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
from faker import Faker 
import time
import os 
import csv
import psutil
import threading
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
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:8080", "http://localhost:8081"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



models.Base.metadata.create_all(bind=engine)

# represent number of rows for 1 true data. e.g if for every 1 true data there will be another 9 fake data, then it will be set 10
dataPerTrue = 10
upload_eval_dict = {}
read_eval_dict = {}
user_dependency = Annotated[dict, Depends(get_current_user)]

# Helper functions for CPU and memory tracking
def get_memory_mb():
    """Get current process memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # Convert bytes to MB

def get_cpu_percent(interval=0.1):
    """Get current process CPU usage percentage"""
    process = psutil.Process(os.getpid())
    return process.cpu_percent(interval=interval)

class ResourceTracker:
    """Context manager to track peak memory and CPU during an operation"""
    def __init__(self, operation_name="operation", sample_interval=0.1):
        self.operation_name = operation_name
        self.sample_interval = sample_interval
        self.start_memory = None
        self.end_memory = None
        self.peak_memory = 0
        self.peak_cpu = 0
        self.process = psutil.Process(os.getpid())
        self._monitoring = False
        self._monitor_thread = None
        
    def __enter__(self):
        self.start_memory = get_memory_mb()
        self.peak_memory = self.start_memory
        self.peak_cpu = 0
        
        # Start monitoring in a separate thread
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_resources, daemon=True)
        self._monitor_thread.start()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
        self.end_memory = get_memory_mb()
        # Final check for peak values
        current_memory = get_memory_mb()
        current_cpu = self.process.cpu_percent(interval=0.1)
        
        # Handle None values from cpu_percent
        if current_cpu is None:
            current_cpu = 0
        
        if current_memory > self.peak_memory:
            self.peak_memory = current_memory
        if current_cpu > self.peak_cpu:
            self.peak_cpu = current_cpu
        return False
    
    def _monitor_resources(self):
        """Monitor resources in a separate thread"""
        while self._monitoring:
            try:
                current_memory = get_memory_mb()
                current_cpu = self.process.cpu_percent(interval=self.sample_interval)
                
                # Handle None values from cpu_percent (can happen on first call)
                if current_cpu is None:
                    current_cpu = 0
                
                if current_memory > self.peak_memory:
                    self.peak_memory = current_memory
                if current_cpu > self.peak_cpu:
                    self.peak_cpu = current_cpu
                    
                time.sleep(self.sample_interval)
            except Exception:
                break
    
    def get_metrics(self):
        """Get all tracked metrics"""
        # Ensure all values are numbers, defaulting to 0 if None
        start_memory = self.start_memory if self.start_memory is not None else 0.0
        end_memory = self.end_memory if self.end_memory is not None else (get_memory_mb() if self.start_memory is not None else 0.0)
        peak_memory = self.peak_memory if (self.peak_memory is not None and self.peak_memory > 0) else (start_memory if start_memory else 0.0)
        peak_cpu = self.peak_cpu if (self.peak_cpu is not None and self.peak_cpu >= 0) else 0.0
        
        memory_delta = end_memory - start_memory
        
        return {
            f"{self.operation_name}_memory_start_mb": round(float(start_memory), 2),
            f"{self.operation_name}_memory_end_mb": round(float(end_memory), 2),
            f"{self.operation_name}_memory_delta_mb": round(float(memory_delta), 2),
            f"{self.operation_name}_memory_peak_mb": round(float(peak_memory), 2),
            f"{self.operation_name}_cpu_percent": round(float(peak_cpu), 2)
        }

def track_resource_usage(start_memory, start_time, operation_name="operation"):
    """Track resource usage during an operation and return metrics (legacy function for compatibility)"""
    end_memory = get_memory_mb()
    memory_delta = end_memory - start_memory
    
    # Get CPU usage (non-blocking, uses last interval)
    cpu_percent = get_cpu_percent(interval=0.1)
    
    return {
        f"{operation_name}_memory_start_mb": round(start_memory, 2),
        f"{operation_name}_memory_end_mb": round(end_memory, 2),
        f"{operation_name}_memory_delta_mb": round(memory_delta, 2),
        f"{operation_name}_cpu_percent": round(cpu_percent, 2)
    }

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

def create_fake_rows(num=1):
    fake = Faker()
    fake_data = [{"Shipment_ID":fake.bothify(text="SH#####") , 
                            "Origin_Warehouse": "Warehouse_"+fake.city()[:3].upper(), 
                            "Shipment_Date": fake.date_between(start_date='-2y'), 
                            "Weight_kg": fake.random_int(min=1, max=1000)/10, 
                            "Transit_Days": fake.random_int(min=1, max=10)} for x in range(num)]
    return fake_data

# only for evaluation purpose
@app.get("/delete-table/")
def delete_table():
    db: Session = SessionLocal()
    db.query(models.Test).delete()
    db.commit()
    db.close()


@app.post("/upload-csv/")
async def upload_csv(file: UploadFile):
    #Check if file is csv
    start_time = time.time()
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400,detail="Only csv file allowed")

    raw = await file.read()
    df = pd.read_csv(StringIO(raw.decode("utf-8-sig", errors="replace")), engine="python", on_bad_lines="skip")

    if df.empty:
        raise HTTPException(status_code=400, detail="CSV file is empty or contains no data")
    
    # Track peak resources during the entire upload operation
    with ResourceTracker("upload", sample_interval=0.1) as resource_tracker:
        # read fake data
        upload_eval_dict["data_per_true"] = dataPerTrue
        data_quantity = dataPerTrue * len(df)
        generate_fakes_start_time = time.time()
        fake_dict = create_fake_rows(data_quantity)
        upload_eval_dict["generate_fake_rows_time"] = time.time() - generate_fakes_start_time
        db: Session = SessionLocal()
        try:
            # Time database query for max_row_number
            db_query_start_time = time.time()
            max_row_number = db.query(func.max(models.Test.row_number)).scalar()
            upload_eval_dict["db_query_time"] = time.time() - db_query_start_time
            if max_row_number is None:
                max_row_number = 0
            else:
                max_row_number += 1
        except:
            max_row_number = 0
            upload_eval_dict["db_query_time"] = 0

        #check data model
        try:
            records = df.to_dict(orient="records")
           
            # Map to ORM objects - obfuscate only real data, fake data added directly
            objects = []
            true_row_number = get_row_number(len(records))
            
            idx  = 0
            obfuscation_time_total = 0
            for i in range(data_quantity):
                cur_row_number = max_row_number + i 
                if cur_row_number not in true_row_number:
                    # Fake data - add directly without obfuscation
                    cur_obj = get_model_data_unobfuscated(cur_row_number, fake_dict[i])
                else:
                    # Real data - obfuscate before adding
                    obfuscation_start_time = time.time()
                    cur_obj = get_model_data_obfuscated(cur_row_number, records[idx])
                    obfuscation_time_total += time.time() - obfuscation_start_time
                    idx += 1
                objects.append(cur_obj)
            upload_eval_dict["obfuscation_time"] = obfuscation_time_total
         

            # Time database write operations
            db_write_start_time = time.time()
            db.add_all(objects)
            db.commit()
            upload_eval_dict["db_write_time"] = time.time() - db_write_start_time
            upload_eval_dict["upload_time"] = time.time() - start_time
            upload_eval_dict["real_data_rows"] = len(records)
            upload_eval_dict["fake_data_rows"] = data_quantity - len(records)
            
            # Get peak resource metrics from tracker
            resource_metrics = resource_tracker.get_metrics()
            upload_eval_dict.update(resource_metrics)
            
            # Write upload metrics to CSV
            upload_field_names = ["data_per_true", "real_data_rows", "fake_data_rows", "generate_fake_rows_time", "obfuscation_time","numbers_of_real_data_in_db_before_upload", "db_query_time", "db_write_time", "upload_time", "upload_memory_start_mb", "upload_memory_end_mb", "upload_memory_delta_mb", "upload_memory_peak_mb", "upload_cpu_percent"]
            upload_eval_file_name = "./upload_eval.csv"
            try:
                with open(upload_eval_file_name, mode='a') as f:
                    writer = csv.DictWriter(f, fieldnames=upload_field_names)
                    if os.stat(upload_eval_file_name).st_size == 0:
                        writer.writeheader()
                    writer.writerow(upload_eval_dict)
            except Exception as e:
                print(f"Error writing to CSV: {str(e)}")
            # Reset upload_eval_dict for next upload
            upload_eval_dict.clear()
            
            return {"status": "success", "rows": len(objects)}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}")
        finally:
            db.close()

@app.get("/real-data/")
async def read_real(user = get_optional_user()):
    db: Session = SessionLocal()
    start_time = time.time()
    # Debug logging
    security_logger.info(f"DEBUG: user object = {user}, type = {type(user)}")
    
    username = "unknown"
    if user:
        security_logger.info(f"DEBUG: user dict = {user}, username field = {user.get('username', 'NOT_FOUND')}")
        username = user.get("username", "unknown")
    else:
        security_logger.info("DEBUG: user is None or falsy")

    # Track peak resources during the entire read operation
    with ResourceTracker("read", sample_interval=0.1) as resource_tracker:
        true_row_number = get_row_number(0)
        
        # Log frontend access with all accessed rows
        security_logger.info(
            f"FRONTEND_ACCESS - accessing_rows:{true_row_number} "
            f"requested_by:{username} timestamp:{datetime.now().isoformat()}"
        )
        
        # Time database query
        db_query_start_time = time.time()
        result = db.query(models.Test).filter(models.Test.row_number.in_(true_row_number)).all()
        read_eval_dict["db_query_time"] = time.time() - db_query_start_time

        real_data = []

        # Time deobfuscation
        deobfuscation_start_time = time.time()
        for i in result:
            cur_dict = {}
            cur_dict["Shipment_ID"] = deobfuscate_str(i.Shipment_ID)
            cur_dict["Origin_Warehouse"] = deobfuscate_str(i.Origin_Warehouse)
            cur_dict["Shipment_Date"] = deobfuscate_date(i.Shipment_Date)
            cur_dict["Weight_kg"] = deobfuscate_number(i.Weight_kg)
            cur_dict["Transit_Days"] = deobfuscate_number(i.Transit_Days)
            real_data.append(cur_dict)
        read_eval_dict["deobfuscation_time"] = time.time() - deobfuscation_start_time
        
        read_eval_dict["read_real_data_time"] = time.time() - start_time
        read_eval_dict["total_read_rows"] = len(real_data)
        read_eval_dict["data_per_true"] = dataPerTrue
        
        # Get peak resource metrics from tracker
        resource_metrics = resource_tracker.get_metrics()
        read_eval_dict.update(resource_metrics)
    
    # Write read metrics to CSV
    read_field_names = ["read_real_data_time", "db_query_time", "deobfuscation_time", "numbers_of_real_data_in_db_before_read","total_read_rows", "data_per_true", "read_memory_start_mb", "read_memory_end_mb", "read_memory_delta_mb", "read_memory_peak_mb", "read_cpu_percent"]
    read_eval_file_name = "./read_eval.csv"
    with open(read_eval_file_name, mode='a') as f:
        writer = csv.DictWriter(f, fieldnames=read_field_names)
        if os.stat(read_eval_file_name).st_size == 0:
            writer.writeheader()
        writer.writerow(read_eval_dict)
    
    # Reset read_eval_dict for next read
    read_eval_dict.clear()
   
    return real_data


def get_model_data_obfuscated(mapped_row, rec):
    """
    Create model object with obfuscated data (for real data)
    """
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

def get_model_data_unobfuscated(mapped_row, rec):
    """
    Create model object without obfuscation (for fake data)
    """
    sh_id = rec.get("Shipment_ID")
    wh = rec.get("Origin_Warehouse")
    date = rec.get("Shipment_Date")
    weight = rec.get("Weight_kg")
    days = rec.get("Transit_Days")
    
    cur_obj = models.Test(row_number = mapped_row,
        Shipment_ID=sh_id,
        Origin_Warehouse=wh,
        Shipment_Date=date,
        Weight_kg=weight,
        Transit_Days=days)
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
        true_number_of_rows = math.ceil(max_row_number / dataPerTrue)
    read_eval_dict["numbers_of_real_data_in_db_before_read"] = true_number_of_rows
    upload_eval_dict["numbers_of_real_data_in_db_before_upload"] = true_number_of_rows
    scale = math.ceil(math.log(dataPerTrue, 10))
    if math.log(dataPerTrue, 10) == scale:
        restrict_scale = None
    else:
        restrict_scale = dataPerTrue//((scale - 1)*10)
    """with open("pi.txt") as f:
        digits = f.read((true_number_of_rows+insert_rows)*scale)"""
    seed = 314
    random.seed(seed)
    true_row_number = []
    if insert_rows:
        cur_base=true_number_of_rows
        #digits = digits[true_number_of_rows*scale:]
        # if there is already rows in database, we need to generate previous rows random number to keep the generator consistent for retreieve
        for i in range(true_number_of_rows):
            for j in range(scale):
                if j==scale-1 and restrict_scale is not None:
                    
                    random.randint(0, restrict_scale-1)
                    
                else:
                    random.randint(0, 9)
    else:
        cur_base = 0
    for i in range(insert_rows if insert_rows else true_number_of_rows):
        cur_digits = 0
        digit_base = 1
        for j in range(scale):
            if j==scale-1 and restrict_scale is not None:
                cur_digits += digit_base * random.randint(0, restrict_scale-1)
            else:
                cur_digits += digit_base * random.randint(0, 9)
            digit_base *= 10
        true_row_number.append(cur_base*dataPerTrue+int(cur_digits))
        cur_base+=1
    

    return true_row_number




@app.get("/config")
async def get_config():
    return {"dataPerTrue": dataPerTrue}