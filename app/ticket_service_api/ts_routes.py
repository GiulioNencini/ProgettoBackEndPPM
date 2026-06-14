from flask.views import MethodView
from flask import request, jsonify, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from models.user import User
from models.reservation import Reservation
from models.scheduling import Scheduling
from models.showing import Showing
from db import db, to_dict
from datetime import datetime, date



ticket_service_bp = Blueprint('ticket_service', __name__, url_prefix='/api')

class EventsView(MethodView):
    def get(self):
        showDate_str = request.args.get('date')
        if not showDate_str:
            return jsonify({'msg': 'Missing parameters'}), 400
        
        try:
            showDate = datetime.strptime(showDate_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'msg': 'Invalid date format. Use YYYY-MM-DD'}), 400

        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
        except Exception:
            user_id = None

        showing_scheduling: Scheduling = Scheduling.query.filter(Scheduling.date > showDate).all()

        if showing_scheduling is None:
            return jsonify({'msg' : f'No results after {showDate_str}'}), 404
        
        results = []
        for sched in showing_scheduling:
            # Sfruttiamo la relationship per prendere i dati dello spettacolo associato
            show = sched.showing  
            
            event_data = {
                "id_scheduling": sched.id,
                "date": sched.date.strftime('%Y-%m-%d'),
                "time": sched.time.strftime('%H:%M'),
                "show_title": show.title,
                "description": show.description,
                "price": show.price
            }
            
            
            #La query eseguita è la seguente
            """SELECT scheduling.*, showing.title, (scheduling.totalSeats - COUNT(reservation.id)) AS seats_left
                FROM scheduling
                JOIN showing ON scheduling.idShow = showing.id
                LEFT JOIN reservation ON scheduling.id = reservation.idScheduling
                WHERE scheduling.date > '2026-06-08'
                GROUP BY scheduling.id;"""
            if user_id is not None:
                posti_occupati = len(sched.reservations)
                posti_rimanenti = sched.totalSeats - posti_occupati
                
                event_data["seats_remaining"] = posti_rimanenti
                event_data["total_seats"] = sched.totalSeats

            results.append(event_data)

        return jsonify(results), 200

    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()
        user: User = User.query.filter_by(id=user_id).first()

        if not user.is_admin:
            return jsonify({'msg': 'Admin reserved area'}), 403

        data = request.get_json()

        show_title = data.get('title')
        show_description = data.get('description')
        show_price = data.get('price')

        if not all([show_title, show_description, show_price]):
            return jsonify({'msg' : 'Missing parameters'}), 400
        
        new_show = Showing(
            title = show_title,
            description = show_description,
            price = show_price
        )

        db.session.add(new_show)
        db.session.commit()

        return jsonify({'msg': 'Show added successfully'}), 201


ticket_service_bp.add_url_rule('/events', view_func=EventsView.as_view('events'), methods = ['GET', 'POST'])

@ticket_service_bp.route('/scheduling/<int:showId>', methods = ['POST']) 
@jwt_required()
def postScheduling(showId):
    user_id = get_jwt_identity()
    user: User = User.query.filter_by(id=user_id).first()

    if not user:
        return jsonify({'msg' : 'Login required'}), 403

    if not user.is_admin:
        return jsonify({'msg': 'Admin reserved area'}), 403

    data = request.get_json()

    show: Showing = Showing.query.filter_by(id = showId).first()
    if not show:
        return jsonify({'msg' : 'Show not found for scheduling'}), 404

    sch_date = datetime.strptime(data.get('date') , '%Y-%m-%d')
    sch_time = datetime.strptime(data.get('time') , '%H:%M').time()
    sch_totalSeats = data.get('totalSeats')

    scheduling = Scheduling(
        showId = show.id,
        date = sch_date,
        time = sch_time,
        totalSeats = sch_totalSeats
    )

    db.session.add(scheduling)
    db.session.commit()

    return jsonify({'msg': 'Show scheduled successfully'}), 201

class ReservationView(MethodView):
    decorators = [jwt_required()]

    # Status delle prenotazioni dell'utente
    def get(self):
        user_id = get_jwt_identity()
        user: User = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({'msg': 'Login required'}), 403
        
        user_reservation = Reservation.query.filter_by(userId=user_id).all()
        if not user_reservation:
            return jsonify({'msg': f'No reservation found for userId:{user_id}'}), 404
        
        results = []
        for usRes in user_reservation:
            sched = usRes.scheduling
            show = sched.showing
            results.append({
                "id_reservation": usRes.id,
                "show_title": show.title,
                "schedulingId": usRes.schedulingId,
                "date": sched.date.strftime('%Y-%m-%d'),
                "time": sched.time.strftime('%H:%M'),
                "seatNumber": usRes.seatNumber
            })
        return jsonify(results), 200

    # Creazione di una prenotazione
    def post(self, scheduling_id):
        user_id = get_jwt_identity()
        user: User = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({'msg': 'Login required'}), 403
        
        scheduling : Scheduling = Scheduling.query.filter_by(id=scheduling_id).first()
        if not scheduling:
            return jsonify({'msg': 'Scheduling not found for reservation'}), 404
        
        data = request.get_json()
        res_seatNumber = data.get('seatNumber')

        if res_seatNumber < 1 or res_seatNumber > scheduling.totalSeats:
            return jsonify({'msg': f'Invalid seat number. Choose between 1 and {scheduling.totalSeats}'}), 400
        
        if scheduling.date < date.today():
            return jsonify({'msg' : 'This event is already ended'}), 403

        existing_reservation = Reservation.query.filter_by(schedulingId = scheduling_id).count()
        if existing_reservation == scheduling.totalSeats:
            return jsonify({'msg' : 'This day is SOLD-OUT'}), 403
        
        existing_reservation = None

        existing_reservation = Reservation.query.filter_by(
            schedulingId=scheduling_id, 
            seatNumber=res_seatNumber
        ).first()
        if existing_reservation:
            return jsonify({'msg': f'Seat {res_seatNumber} is already taken'}), 409

        reservation : Reservation= Reservation(
            userId=user_id,
            schedulingId=scheduling_id,
            seatNumber=res_seatNumber
        )
        db.session.add(reservation)
        db.session.commit()
        return jsonify({'msg': 'Reservation successfully completed'}), 201

    # Cancellazione di una prenotazione
    def delete(self, reservation_id):
        user_id = get_jwt_identity()
        user: User = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({'msg': 'Login required'}), 403
        
        reservation : Reservation = Reservation.query.filter_by(
            userId=user_id, 
            id = reservation_id, 
        ).first()
        if not reservation:
            return jsonify({'msg': 'Reservation not found for delete'}), 404
        
        db.session.delete(reservation)
        db.session.commit()
        return jsonify({'msg': 'Reservation successfully deleted'}), 200

    # PATCH: Modifica parziale
    def patch(self, reservation_id):
        user_id = get_jwt_identity()
        user: User = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({'msg': 'Login required'}), 403
        
        reservation : Reservation = Reservation.query.filter_by(id=reservation_id).first()
        if not reservation:
            return jsonify({'msg': 'Reservation not found'}), 404
        if reservation.userId != int(user_id):
            return jsonify({'msg': 'userId and reservationId are not compatible'}), 403
        
        actualScheduling : Scheduling = Scheduling.query.filter_by(id=reservation.schedulingId).first()
        
        data = request.get_json()
        new_sched_id = data.get('schedulingId')
        new_seat_number = data.get('seatNumber')

        if new_sched_id is not None:
            new_scheduling : Scheduling = Scheduling.query.filter_by(id=new_sched_id).first()
            if not new_scheduling:
                return jsonify({'msg': 'Scheduling not found for update'}), 404
            
            if new_scheduling.date.date() < date.today():
                return jsonify({'msg' : 'You are trying to modify into a scheduling already ended'}), 403
            
            if actualScheduling.showId != new_scheduling.showId:
                return jsonify({'msg' : 'Select a scheduling whose showId is the same of your current scheduling'})
            
            total_booked = Reservation.query.filter_by(schedulingId=new_sched_id).count()
            if total_booked >= new_scheduling.totalSeats:
                return jsonify({'msg': 'Target show is completely sold out, cannot move reservation'}), 400

            seat_to_assign = reservation.seatNumber
            seat_taken = Reservation.query.filter_by(schedulingId=new_sched_id, seatNumber=seat_to_assign).first()
        
            if seat_taken:
                assigned = False
                for seat in range(1, new_scheduling.totalSeats + 1):
                    check_seat = Reservation.query.filter_by(schedulingId=new_sched_id, seatNumber=seat).first()
                    if not check_seat:
                        seat_to_assign = seat
                        assigned = True
                        break
                if not assigned:
                    return jsonify({'msg': 'Target show is completely sold out, cannot move reservation'}), 400

            reservation.schedulingId = new_sched_id
            reservation.seatNumber = seat_to_assign
            db.session.commit()
            return jsonify({'msg': 'The date reserved has been changed successfully'}), 200
        
        if new_seat_number is not None and new_seat_number != reservation.seatNumber:
            if new_seat_number < 1 or new_seat_number > actualScheduling.totalSeats:
                return jsonify({'msg': 'Invalid seat number'}), 400
            
            reservationBySeatNumber : Reservation = Reservation.query.filter_by(
                schedulingId=reservation.schedulingId, 
                seatNumber=new_seat_number
            ).filter(~Reservation.id.in_([reservation_id])).first()

            if reservationBySeatNumber:
                return jsonify({'msg': f'The seat number {new_seat_number} is already taken'}), 403
            
            reservation.seatNumber = new_seat_number
            db.session.commit()
            return jsonify({'msg': 'The seat number has been changed successfully'}), 200

        return jsonify({'msg': 'No changes detected'}), 200

reservation_view = ReservationView.as_view('reservation_api')

ticket_service_bp.add_url_rule('/reservation', view_func=reservation_view, methods=['GET'])
ticket_service_bp.add_url_rule('/reservation/<int:scheduling_id>', view_func=reservation_view, methods=['POST'])
ticket_service_bp.add_url_rule('/reservation/<int:reservation_id>', view_func=reservation_view, methods=['DELETE'])
ticket_service_bp.add_url_rule('/reservation/<int:reservation_id>', view_func=reservation_view, methods=['PATCH'])

@ticket_service_bp.route('/userinfo')
@jwt_required()
def userInfo():
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()

    return jsonify(to_dict(user)), 200