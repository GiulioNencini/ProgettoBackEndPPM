from db import db
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import ForeignKey

class Reservation(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    idUser: Mapped[int] = mapped_column(ForeignKey('user.id'), nullable=False)
    idScheduling: Mapped[int] = mapped_column(ForeignKey('scheduling.id'), nullable=False)
    seatNumber: Mapped[int] = mapped_column(nullable=False)