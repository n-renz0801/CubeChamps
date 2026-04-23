# from flask import Flask, render_template, request, redirect
# from flask_sqlalchemy import SQLAlchemy
# from datetime import datetime
# from werkzeug.security import generate_password_hash, check_password_hash
# from flask import session


# cubechamps/
# │
# ├── app.py
# ├── models.py
# ├── requirements.txt
# │
# ├── templates/
# │   ├── base.html
# │   ├── home.html
# │   ├── create_meet.html
# │   ├── meet_detail.html
# │
# ├── static/
# │   ├── css/
# │   │   └── styles.css
# │   ├── js/
# │   │   ├── create_meet.js
# │   │   └── main.js
# │   └── images/


from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


app = Flask(__name__)
app.secret_key = 'cubemeettara'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://cubechamps_user:rCxlw73610w9oU60Q2srBvmq9ULk2Pav@dpg-d7i7059j2pic73akrnv0-a.virginia-postgres.render.com/cubechamps'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# ── Models ────────────────────────────────────────────────────────────────────

class CubeMeet(db.Model):
    __tablename__ = 'cubemeets'

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    date       = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    events      = db.relationship('Event', backref='cubemeet', lazy=True, cascade='all, delete-orphan')
    # competitors = db.relationship('Competitor', backref='cubemeet', lazy=True, cascade='all, delete-orphan')


class Event(db.Model):
    __tablename__ = 'events'

    id          = db.Column(db.Integer, primary_key=True)
    cubemeet_id = db.Column(db.Integer, db.ForeignKey('cubemeets.id'), nullable=False)
    name        = db.Column(db.String(50), nullable=False)   # e.g. "3x3x3 Cube"
    rounds      = db.Column(db.Integer, nullable=False)

    # solves = db.relationship('Solve', backref='event', lazy=True, cascade='all, delete-orphan')


# class Competitor(db.Model):
#     __tablename__ = 'competitors'

#     id          = db.Column(db.Integer, primary_key=True)
#     cubemeet_id = db.Column(db.Integer, db.ForeignKey('cubemeets.id'), nullable=False)
#     name        = db.Column(db.String(100), nullable=False)

#     solves = db.relationship('Solve', backref='competitor', lazy=True, cascade='all, delete-orphan')


# class Solve(db.Model):
#     __tablename__ = 'solves'

#     id            = db.Column(db.Integer, primary_key=True)
#     event_id      = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
#     competitor_id = db.Column(db.Integer, db.ForeignKey('competitors.id'), nullable=False)
#     round_number  = db.Column(db.Integer, nullable=False)
#     time_ms       = db.Column(db.Integer, nullable=True)       # stored in milliseconds; NULL = not yet entered
#     penalty       = db.Column(db.String(10), default='none')   # 'none' | '+2' | 'dnf'

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    meets = CubeMeet.query.order_by(CubeMeet.date.desc()).all()
    return render_template("home.html", meets=meets)


@app.route('/meet/create', methods=['GET', 'POST'])
def create_meet():
    if request.method == 'POST':
        meet_name = request.form.get('meet_name')
        event_date = request.form.get('event_date')

        event_names = request.form.getlist('event_name[]')
        rounds_list = request.form.getlist('rounds[]')

        # Create meet
        new_meet = CubeMeet(
            name=meet_name,
            date=datetime.strptime(event_date, '%Y-%m-%d')
        )
        db.session.add(new_meet)
        db.session.commit()

        # Create multiple events
        for name, rounds in zip(event_names, rounds_list):
            event = Event(
                name=name,
                rounds=int(rounds),
                cubemeet_id=new_meet.id
            )
            db.session.add(event)

        db.session.commit()

        return redirect(url_for('home'))

    return render_template('create_meet.html')


@app.route("/meet/<int:meet_id>")
def meet_detail(meet_id):
    meet = CubeMeet.query.get_or_404(meet_id)
    return render_template("meet_detail.html", meet=meet)

# @app.route("/cubemeet/<int:meet_id>/competitors")
# def meet_competitors(meet_id):
#     meet = CubeMeet.query.get_or_404(meet_id)
#     return render_template("cubemeet/competitors.html", meet=meet)

# @app.route("/cubemeet/<int:meet_id>/results")
# def meet_results(meet_id):
#     meet = CubeMeet.query.get_or_404(meet_id)
#     return render_template("cubemeet/results.html", meet=meet)


# @app.route("/cubemeet/<int:meet_id>/event/<int:event_id>/round/<int:round_number>")
# def round_detail(meet_id, event_id, round_number):
#     meet  = CubeMeet.query.get_or_404(meet_id)
#     event = Event.query.get_or_404(event_id)
#     solves = Solve.query.filter_by(event_id=event_id, round_number=round_number).all()
#     return render_template(
#         "round/round_detail.html",
#         meet=meet, event=event,
#         round_number=round_number,
#         solves=solves
#     )

# @app.route("/cubemeet/<int:meet_id>/event/<int:event_id>/round/<int:round_number>/save", methods=["POST"])
# def save_solves(meet_id, event_id, round_number):
#     return redirect(url_for("round_detail", meet_id=meet_id, event_id=event_id, round_number=round_number))


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)