from flask_sqlalchemy import SQLAlchemy
from datetime import date, time

db = SQLAlchemy()

def to_dict(data):
    results = {}
    for column in data.__table__.columns:
        attr = getattr(data, column.name)

        if isinstance(attr, (date, time)):
            attr = attr.isoformat()  
        
        results[column.name] = attr
    return results