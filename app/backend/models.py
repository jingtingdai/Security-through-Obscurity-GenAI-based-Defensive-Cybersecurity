from database import Base
from sqlalchemy import Numeric, Column, Integer, String, TIMESTAMP, Date
import datetime

class Test(Base):
    __tablename__ = "eval_100"
    row_number = Column(Integer,primary_key=True, index=True, nullable=True)
    Shipment_ID = Column(String,index=False)
    Origin_Warehouse = Column(String,index=True, nullable=True)
    Shipment_Date = Column(Date,index=True, nullable=True)
    Weight_kg = Column(Numeric(10,2),index=True, nullable=True)
    Transit_Days = Column(Integer,index=True, nullable=True)


class Users(Base):
    __tablename__ = "Users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    hashed_password = Column(String)