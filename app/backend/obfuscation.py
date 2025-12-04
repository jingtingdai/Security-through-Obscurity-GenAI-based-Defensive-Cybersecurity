
# first get ord(c) for each c in string s, then rotate ord by offset
import datetime
import random
from pathlib import Path
from decimal import Decimal
secret_file = Path("./secret.txt")
if secret_file.is_file():
    with open(secret_file) as f:
        secret_key = int(f.read())
else:
    secret_key = random.randint(1,127)
    with open(secret_file,'w') as f:
        f.write(str(secret_key))

def obfuscate_str(s:str):
    if s is None:
        return None
    new_string = ""
    offset = secret_key
    for c in s:
        cur = ord(c)
        new_string += chr((cur+offset) % 128)
        
    return new_string

def obfuscate_number(i):
    if i is None:
        return None
    offset = secret_key
    return Decimal(i) + offset

def obfuscate_date(date):
    if date is None:
        return None
    offset_days = secret_key
    try:
        date = datetime.date.fromisoformat(date)
    except:
        return date+datetime.timedelta(days=offset_days)
    return date + datetime.timedelta(days=offset_days)

def deobfuscate_str(s:str):
    if s is None:
        return None
    new_string = ""
    offset = secret_key
    for c in s:
        cur = ord(c)
        new_string += chr((cur-offset) % 128)
    
    return new_string

def deobfuscate_number(i):
    if i is None:
        return None
    return Decimal(i) - secret_key

def deobfuscate_date(date):
    if date is None:
        return None
    offset_days = secret_key
    return date - datetime.timedelta(days=offset_days)