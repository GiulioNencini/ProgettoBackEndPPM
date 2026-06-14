from db import db
from sqlalchemy.orm import mapped_column, Mapped, relationship
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(nullable=False)
    is_admin: Mapped[bool] = mapped_column(default=False)

    reservations = relationship('Reservation', backref='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

def create_admin():# si assume che il sistema abbia un solo admin
    if not User.query.filter_by(is_admin=True).first():
        admin = User(username='admin', is_admin=True)
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()