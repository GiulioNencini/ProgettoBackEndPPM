from flask.views import MethodView
from flask import request, jsonify, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from models.user import User
from models.reservation import Reservation
from models.scheduling import Scheduling
from models.showing import Showing
from app.db import db
from datetime import datetime



ticket_service_bp = Blueprint('events', __name__, url_prefix='/api')

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
            user_id = None #In questo caso abbiamo a che fare con un anonimo

        #Tutti gli eventi post showDate_str
        showing_scheduling: Scheduling = Scheduling.query.filter(Scheduling.date > showDate).all()

        if showing_scheduling is None:
            return jsonify({'msg' : f'No results after {showDate_str}'}), 404
        
        results = []
        for sched in showing_scheduling:
            # Sfruttiamo la relazione per prendere i dati dello spettacolo associato
            show = sched.showing  
            
            # Struttura dati base (per utenti anonimi e loggati)
            event_data = {
                "id_scheduling": sched.id,
                "date": sched.date.strftime('%Y-%m-%d'),
                "time": sched.time.strftime('%H:%M'),
                "show_title": show.title,
                "description": show.description,
                "price": show.price
            }
            
            # SE L'UTENTE È AUTENTICATO, AGGIUNGIAMO I POSTI RIMANENTI
            """SELECT scheduling.*, showing.title, (scheduling.totalSeats - COUNT(reservation.id)) AS seats_left
                FROM scheduling
                JOIN showing ON scheduling.idShow = showing.id
                LEFT JOIN reservation ON scheduling.id = reservation.idScheduling
                WHERE scheduling.date > '2026-06-08'
                GROUP BY scheduling.id;"""
            if user_id is not None:
                # len(sched.reservations) conta quante prenotazioni esistono per questa recita
                posti_occupati = len(sched.reservations)
                posti_rimanenti = sched.totalSeats - posti_occupati
                
                event_data["seats_remaining"] = posti_rimanenti
                event_data["total_seats"] = sched.totalSeats

            results.append(event_data)

        return jsonify(results), 200

    @jwt_required()
    def post(self):#azioni dell'admin
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


ticket_service_bp.add_url_rule('/events', view_func=EventsView.as_view('events'))

@ticket_service_bp.route('/scheduling/<int:showId>', methods = ['POST']) 
@jwt_required()
def postScheduling(showId):
    user_id = get_jwt_identity()
    user: User = User.query.filter_by(id=user_id).first()

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


@ticket_service_bp.route('/reservation_create/<int:schedulingId>', methods = ['POST'])
@jwt_required()
def postReservation(schedulingId):
    user_id = get_jwt_identity()
    user: User = User.query.filter_by(id=user_id).first()

    if not user:
        return jsonify({'msg': 'Login required'}), 403
    
    scheduling: Scheduling = Scheduling.query.filter_by(id = schedulingId).first()
    if not scheduling:
        return jsonify({'msg' : 'Scheduling not found for reservation'}), 404
    
    data = request.get_json()
    res_seatNumber = data.get('seatNumber')

    if res_seatNumber < 1 or res_seatNumber > scheduling.totalSeats:
        return jsonify({'msg': f'Invalid seat number. Choose between 1 and {scheduling.totalSeats}'}), 400

    existing_reservation = Reservation.query.filter_by(
        schedulingId=schedulingId, 
        seatNumber=res_seatNumber
    ).first()
    
    if existing_reservation:
        return jsonify({'msg': f'Seat {res_seatNumber} is already taken'}), 409

    reservation = Reservation(
        userId = user_id,
        schedulingId = schedulingId,
        seatNumber = res_seatNumber
    )

    db.session.add(reservation)
    db.session.commit()

    return jsonify({'msg' : 'Reservation successfully completed'}), 201


@ticket_service_bp.route('/reservation_delete/<int:schedulingId>/<int:seatNumber>', methods = ['DELETE'])
@jwt_required()
def deleteReservation(schedulingId, seatNumber):
    user_id = get_jwt_identity()
    user: User = User.query.filter_by(id=user_id).first()

    if not user:
        return jsonify({'msg': 'Login required'}), 403
    
    reservation: Reservation = Reservation.query.filter_by(userId = user_id, schedulingId = schedulingId, seatNumber = seatNumber).first()

    if not reservation:
        return jsonify({'msg' : 'Reservation not found for delete'}), 404
    
    db.session.delete(reservation)
    db.session.commit()

    return jsonify({'msg' : 'Reservation successfully deleted'}), 200

#È la get di tutte le prenotazioni effettuate da un preciso utente, vengono ritornate le informazioni strettamente necessarie all'utente
@ticket_service_bp.route('/reservation_get', methods = ['GET'])
@jwt_required()
def getReservation():
    user_id = get_jwt_identity()
    user: User = User.query.filter_by(id=user_id).first()

    if not user:
        return jsonify({'msg': 'Login required'}), 403
    
    user_reservation : Reservation = Reservation.query.filter_by(userId = user_id).all()

    if not user_reservation:
        return jsonify({'msg' : f'No reservation found for userId:{user_id}'}), 404
    
    results = []

    for usRes in user_reservation:
        sched = usRes.scheduling
        show = sched.showing

        reservation_data = {
            "id_reservation" : usRes.id,
            "show_title" : show.title,
            "date" : sched.date.strftime('%Y-%m-%d'),
            "time" : sched.time.strftime('%H:%M'),
            "seatNumber" : usRes.seatNumber
        }

        results.append(reservation_data)
    
    return jsonify(results), 200

@ticket_service_bp.route('/reservation_update/<int:reservationId>', methods = ['PATCH']) # ho optato per il metodo patch poiché la modifica dell'oggetto Reservation è solo parziale
@jwt_required()
def updateReservation(reservationId):
    user_id = get_jwt_identity()
    user: User = User.query.filter_by(id=user_id).first()

    if not user:
        return jsonify({'msg': 'Login required'}), 403
    
    reservation : Reservation = Reservation.query.filter_by(id = reservationId).first()
    if not reservation:
        return jsonify({'msg' : 'Reservation not found'}), 404
    if not reservation.userId == user_id:
        return jsonify({'msg' : 'userId and reservationId are not compatible'}), 403
    
    actualScheduling : Scheduling = Scheduling.query.filter_by(id = reservation.schedulingId).first()
    
    data = request.get_json()
    new_sched_id = data.get('schedulingId') # per il cambio della data -> si tratta letteralmente di modificare la schedulazione stessa
    new_seat_number = data.get('seatNumber') # se si vuol cambiare solo il posto non importa cambiare la schedulazione stessa

    if new_sched_id is not None:
        new_scheduling :Scheduling = Scheduling.query.filter_by(id = new_sched_id).first()
        if not new_scheduling:
            return jsonify({'msg' : 'Scheduling not found for update'}), 404
        
        # Controlliamo se il posto attuale dell'utente è libero nella NUOVA data
        seat_to_assign = reservation.seatNumber
        seat_taken = Reservation.query.filter_by(schedulingId=new_sched_id, seatNumber=seat_to_assign).first()
    
        # Se il posto è già occupato nella nuova data, cerchiamo il primo disponibile
        if seat_taken:
            assigned = False
            for seat in range(1, new_scheduling.totalSeats + 1):
                # Controlla se questo specifico numero di sedia è libero la nuova sera
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
        return jsonify({'msg' : 'The date reserved has been changed successfully'}), 200
    
    if new_seat_number is not None and new_seat_number != reservation.seatNumber:
        if new_seat_number < 1 or new_seat_number > actualScheduling.totalSeats:
            return jsonify({'msg' : 'Invalid seat number'}), 400
        
        reservationBySeatNumber: Reservation = Reservation.query.filter_by(schedulingId = reservation.schedulingId, seatNumber = new_seat_number).filter(~Reservation.id.in_([reservationId])).first()

        if reservationBySeatNumber:
            return jsonify({'msg' : f'The seat number {new_seat_number} is already taken'}), 403
        
        reservation.seatNumber = new_seat_number
        db.session.commit()
        return jsonify({'msg' : 'The seat number has been changed successfully'}), 200

    return jsonify({'msg': 'No changes detected'}), 200