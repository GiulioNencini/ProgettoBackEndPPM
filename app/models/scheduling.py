from sqlalchemy import ForeignKey
from datetime import date as dt_date, time as dt_time

from db import db
from sqlalchemy.orm import mapped_column, Mapped, relationship

class Scheduling(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    idShow: Mapped[int] = mapped_column(ForeignKey('showing.id'), nullable=False)
    date: Mapped[dt_date] = mapped_column(nullable=False)
    time: Mapped[dt_time] = mapped_column(nullable=False)
    totalSeats: Mapped[int] = mapped_column(nullable=False)

reservations = relationship('Reservation', backref='scheduling')
