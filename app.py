# from flask import Flask, render_template, request, redirect
# from flask_sqlalchemy import SQLAlchemy
# from datetime import datetime
# from werkzeug.security import generate_password_hash, check_password_hash
# from flask import session

# app = Flask(__name__)
# app.secret_key = 'cubemeettara'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://cubechamps_user:rCxlw73610w9oU60Q2srBvmq9ULk2Pav@dpg-d7i7059j2pic73akrnv0-a.virginia-postgres.render.com/cubechamps'
# db = SQLAlchemy(app)

# class Expense(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     amount = db.Column(db.Float)
#     description = db.Column(db.String(300))
#     date = db.Column(db.DateTime, default=datetime.utcnow)

#     def __repr__(self):
#         return '<Expense %r>' % self.id
    
# @app.route('/')
# def home():
#     return render_template('index.html')


# if __name__ == "__main__":
#     app.run(debug=True)


from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


app = Flask(__name__)
app.secret_key = 'cubemeettara'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://cubechamps_user:rCxlw73610w9oU60Q2srBvmq9ULk2Pav@dpg-d7i7059j2pic73akrnv0-a.virginia-postgres.render.com/cubechamps'
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
def index():
    meets = CubeMeet.query.order_by(CubeMeet.date.desc()).all()
    return render_template("index.html", meets=meets)


@app.route("/cubemeet/new", methods=["GET"])
def new_cubemeet():
    return render_template("cubemeet/new.html")

@app.route("/cubemeet/new", methods=["POST"])
def create_cubemeet():
    name         = request.form.get("name")
    date         = request.form.get("date")
    event_names  = request.form.getlist("event_name")
    event_rounds = request.form.getlist("event_rounds")

    meet = CubeMeet(name=name, date=datetime.strptime(date, "%Y-%m-%d").date())
    db.session.add(meet)
    db.session.flush()  # gets meet.id before commit

    for event_name, round_count in zip(event_names, event_rounds):
        if event_name:
            db.session.add(Event(cubemeet_id=meet.id, name=event_name, rounds=int(round_count)))

    db.session.commit()
    return redirect(url_for("meet_hub", meet_id=meet.id))


@app.route("/cubemeet/<int:meet_id>")
def meet_hub(meet_id):
    meet = CubeMeet.query.get_or_404(meet_id)
    return render_template("cubemeet/hub.html", meet=meet)

@app.route("/cubemeet/<int:meet_id>/competitors")
def meet_competitors(meet_id):
    meet = CubeMeet.query.get_or_404(meet_id)
    return render_template("cubemeet/competitors.html", meet=meet)

@app.route("/cubemeet/<int:meet_id>/results")
def meet_results(meet_id):
    meet = CubeMeet.query.get_or_404(meet_id)
    return render_template("cubemeet/results.html", meet=meet)


@app.route("/cubemeet/<int:meet_id>/event/<int:event_id>/round/<int:round_number>")
def round_detail(meet_id, event_id, round_number):
    meet  = CubeMeet.query.get_or_404(meet_id)
    event = Event.query.get_or_404(event_id)
    solves = Solve.query.filter_by(event_id=event_id, round_number=round_number).all()
    return render_template(
        "round/round_detail.html",
        meet=meet, event=event,
        round_number=round_number,
        solves=solves
    )

@app.route("/cubemeet/<int:meet_id>/event/<int:event_id>/round/<int:round_number>/save", methods=["POST"])
def save_solves(meet_id, event_id, round_number):
    return redirect(url_for("round_detail", meet_id=meet_id, event_id=event_id, round_number=round_number))


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)