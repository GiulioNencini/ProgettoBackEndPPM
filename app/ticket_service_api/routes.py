from flask.views import MethodView
from flask import request, jsonify, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from models.user import User
from models.reservation import Reservation
from models.scheduling import Scheduling
from models.showing import Showing
from db import db, to_dict
from datetime import datetime, date



bp = Blueprint('events', __name__, url_prefix='/api')

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
        showing_scheduling: Scheduling = Scheduling.query.filter_by(Scheduling.date < showDate).all()

        if showing_scheduling is None:
            return jsonify({'msg' : f'No results after {showDate_str}'}), 404
        
        
        # maggiori informazioni sullo spettacolo
        showing: Showing = Showing.query.filter_by(id = showing_scheduling.idShow).all()
        if showing is None: #anche se in teoria non è possibile per integrità referenziale
            return jsonify({'msg' : 'No showing found'}), 404
        
        result = []
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

            result.append(event_data)

        return jsonify(to_dict(result)), 200

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


bp.add_url_rule('/events', view_func=EventsView.as_view('events'))

@bp.route('/scheduling/<int:showId>', methods = ['POST']) 
@jwt_required()
def postScheduling(showId):
    user_id = get_jwt_identity()
    user: User = User.query.filter_by(id=user_id).first()

    if not user.is_admin:
        return jsonify({'msg': 'Admin reserved area'}), 403

    data = request.get_json()

    show: Showing = Showing.query.filter_by(id = showId).first()
    if not show:
        return jsonify({'msg' : 'Show not found for scheduling'})

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