from db import db
from sqlalchemy.orm import mapped_column, Mapped, relationship

class Showing(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(db.Text, nullable=True)
    price: Mapped[int] = mapped_column(nullable=False)

    scheduledOn = relationship('Scheduling', backref='showing')