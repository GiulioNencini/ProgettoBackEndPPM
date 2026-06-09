from db import db
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import ForeignKey

class Reservation(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    userId: Mapped[int] = mapped_column(ForeignKey('user.id'), nullable=False)
    schedulingId: Mapped[int] = mapped_column(ForeignKey('scheduling.id'), nullable=False)
    seatNumber: Mapped[int] = mapped_column(nullable=False)