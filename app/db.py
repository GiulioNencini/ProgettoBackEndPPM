from flask_sqlalchemy import SQLAlchemy
from datetime import date, time

db = SQLAlchemy()

def to_dict(data):
    results = {}
    for column in data.__table__.columns:
        attr = getattr(data, column.name)

        if isinstance(attr, (date, time)): # converte in stringa le variabili della forma 'YYYY-MM-DD' o 'HH:MM:SS'
            attr = attr.isoformat()  
        
        results[column.name] = attr #si costruisce la forma chiave : attributo
    return results