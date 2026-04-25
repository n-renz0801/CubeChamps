from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import re

PLAIN_NUMBER = re.compile(r'^\d+(\.\d+)?$')
PLUS2        = re.compile(r'^(\d+(\.\d+)?)\+2$')

app = Flask(__name__)
app.secret_key = 'cubemeettara'
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


class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    cubemeet_id = db.Column(db.Integer, db.ForeignKey('cubemeets.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)

    round_list = db.relationship(
        'Round',
        backref='event',
        cascade='all, delete-orphan',
        lazy=True
    )


class Round(db.Model):
    __tablename__ = 'rounds'

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)

    solves = db.relationship(
        'Solve',
        backref='round',
        cascade='all, delete-orphan',
        lazy=True
    )


class Competitor(db.Model):
    __tablename__ = 'competitors'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cubemeet_id = db.Column(db.Integer, db.ForeignKey('cubemeets.id'), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('name', 'cubemeet_id', name='unique_competitor_per_meet'),
    )


class Solve(db.Model):
    __tablename__ = 'solves'

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    competitor_id = db.Column(db.Integer, db.ForeignKey('competitors.id'), nullable=False)
    round_id = db.Column(db.Integer, db.ForeignKey('rounds.id'), nullable=False)

    attempt1 = db.Column(db.String(20))
    attempt2 = db.Column(db.String(20))
    attempt3 = db.Column(db.String(20))
    attempt4 = db.Column(db.String(20))
    attempt5 = db.Column(db.String(20))

    competitor = db.relationship('Competitor', backref='solves')

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

        new_meet = CubeMeet(
            name=meet_name,
            date=datetime.strptime(event_date, '%Y-%m-%d')
        )
        db.session.add(new_meet)
        db.session.commit()

        for name, rcount in zip(event_names, rounds_list):
            event = Event(
                name=name,
                cubemeet_id=new_meet.id
            )
            db.session.add(event)
            db.session.commit()

            for i in range(int(rcount)):
                new_round = Round(
                    event_id=event.id,
                    round_number=i + 1
                )
                db.session.add(new_round)

        db.session.commit()

        return redirect(url_for('meet_detail', meet_id=new_meet.id))

    return render_template('create_meet.html')


@app.route("/meet/<int:meet_id>")
def meet_detail(meet_id):
    meet = CubeMeet.query.get_or_404(meet_id)
    return render_template(
        "meet_detail.html",
        meet=meet,
        not_homepage=True
    )


@app.route("/event/<int:event_id>/add_round", methods=["POST"])
def add_round(event_id):
    event = Event.query.get_or_404(event_id)

    new_round = Round(
        event_id=event.id,
        round_number=len(event.round_list) + 1
    )

    db.session.add(new_round)
    db.session.commit()

    return redirect(url_for('meet_detail', meet_id=event.cubemeet_id))


@app.route("/event/<int:event_id>/remove_round", methods=["POST"])
def remove_round(event_id):
    event = Event.query.get_or_404(event_id)

    last_round = Round.query.filter_by(event_id=event.id)\
        .order_by(Round.round_number.desc())\
        .first()

    if last_round:
        db.session.delete(last_round)
        db.session.commit()

    return redirect(url_for('meet_detail', meet_id=event.cubemeet_id))


@app.route("/meet/<int:meet_id>/add_event", methods=["POST"])
def add_event(meet_id):
    event_name = request.form.get('event_name')
    rounds_count = int(request.form.get('rounds'))

    new_event = Event(
        name=event_name,
        cubemeet_id=meet_id
    )

    db.session.add(new_event)
    db.session.commit()

    for i in range(rounds_count):
        new_round = Round(
            event_id=new_event.id,
            round_number=i + 1
        )
        db.session.add(new_round)

    db.session.commit()

    return redirect(url_for('meet_detail', meet_id=meet_id))


@app.route("/event/<int:event_id>/delete", methods=["POST"])
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    meet_id = event.cubemeet_id

    db.session.delete(event)
    db.session.commit()

    return redirect(url_for('meet_detail', meet_id=meet_id))


# ── Helper Functions ──────────────────────────────────────────────────────────
def _parse_time(t):
    """Returns a float, or 'DNF'/'DNS', or None if invalid."""
    if t is None:
        return None
    t = str(t).strip().upper()
    if t in ("DNF", "DNS"):
        return t
    m = PLUS2.match(t)
    if m:
        return float(m.group(1)) + 2
    if PLAIN_NUMBER.match(t):
        return float(t)
    return None  # anything else (e.g. +3, 12+3) is rejected

def compute_average(times):
    parsed = []
    special_count = 0

    for t in times:
        result = _parse_time(t)
        if result is None:
            continue
        if result in ("DNF", "DNS"):
            special_count += 1
        else:
            parsed.append(result)

    if special_count >= 2:
        return "DNF"
    if len(parsed) < 3:
        return None

    parsed.sort()
    middle = parsed[1:] if special_count == 1 else parsed[1:-1]

    return sum(middle) / len(middle) if middle else None


def compute_best(times):
    parsed = [_parse_time(t) for t in times]
    nums = [v for v in parsed if isinstance(v, float)]
    return min(nums) if nums else None


def solve_stats(solve):
    times = [
        solve.attempt1,
        solve.attempt2,
        solve.attempt3,
        solve.attempt4,
        solve.attempt5
    ]

    avg = compute_average(times)
    valid = [t for t in times if t is not None]

    return len(valid), avg


app.jinja_env.globals.update(
    compute_average=compute_average,
    compute_best=compute_best
)

# ── Round & Solve Routes ──────────────────────────────────────────────────────

@app.route("/round/<int:round_id>")
def round_detail(round_id):
    round_obj = Round.query.get_or_404(round_id)
    event = round_obj.event
    meet = event.cubemeet

    solves = Solve.query.filter_by(round_id=round_id).all()

    def sort_key(s):
        count, avg = solve_stats(s)
        if avg is None:
            avg_numeric = float("inf")
        elif avg == "DNF":
            avg_numeric = float("inf")
        else:
            avg_numeric = avg
        return (count, -avg_numeric)

    solves = sorted(solves, key=sort_key, reverse=True)

    return render_template(
        "round_detail.html",
        round_obj=round_obj,
        event=event,
        meet=meet,
        solves=solves,
        not_homepage=True
    )


@app.route("/event/<int:event_id>/round/<int:round_number>/add_solver", methods=["POST"])
def add_solver(event_id, round_number):

    event = Event.query.get_or_404(event_id)

    round_obj = Round.query.filter_by(
        event_id=event.id,
        round_number=round_number
    ).first_or_404()

    # ✅ ALWAYS create a fresh competitor
    competitor = Competitor(
        name="",
        cubemeet_id=event.cubemeet_id
    )
    db.session.add(competitor)
    db.session.flush()

    solve = Solve(
        event_id=event.id,
        round_id=round_obj.id,
        competitor_id=competitor.id
    )

    db.session.add(solve)
    db.session.commit()

    return redirect(url_for('round_detail', round_id=round_obj.id))


@app.route("/solve/<int:solve_id>/update", methods=["POST"])
def update_solve(solve_id):

    solve = Solve.query.get_or_404(solve_id)
    data = request.get_json()

    name = data.get("name", "").strip()

    if name == "":
        db.session.delete(solve)
        db.session.commit()

        return jsonify({
            "deleted": True,
            "solve_id": solve_id
        })

    # 👇 THIS IS WHERE YOUR NEW BLOCK GOES
    old_competitor = solve.competitor

    existing = Competitor.query.filter_by(
        name=name,
        cubemeet_id=old_competitor.cubemeet_id
    ).first()

    if existing:
        solve.competitor = existing
    else:
        old_competitor.name = name

    db.session.flush()

    if not Solve.query.filter_by(competitor_id=old_competitor.id).first():
        db.session.delete(old_competitor)

    # attempts update stays the same
    solve.attempt1 = data.get("attempt1")
    solve.attempt2 = data.get("attempt2")
    solve.attempt3 = data.get("attempt3")
    solve.attempt4 = data.get("attempt4")
    solve.attempt5 = data.get("attempt5")

    db.session.commit()

    times = [
        solve.attempt1,
        solve.attempt2,
        solve.attempt3,
        solve.attempt4,
        solve.attempt5
    ]

    return jsonify({
        "average": compute_average(times),
        "best": compute_best(times),
        "solve_id": solve.id,
        "deleted": False
    })


@app.route("/solve/<int:solve_id>/delete", methods=["POST"])
def delete_solve(solve_id):
    solve = Solve.query.get_or_404(solve_id)
    competitor = solve.competitor

    db.session.delete(solve)
    db.session.commit()

    if not Solve.query.filter_by(competitor_id=competitor.id).first():
        db.session.delete(competitor)
        db.session.commit()

    return '', 204


@app.route("/meet/<int:meet_id>/persons")
def persons(meet_id):
    meet = CubeMeet.query.get_or_404(meet_id)

    competitors = Competitor.query.filter(
        Competitor.cubemeet_id == meet_id,
        Competitor.name != "",            # ✅ remove empty
        Competitor.name != "New Solver"   # (optional safety)
    ).order_by(Competitor.name.asc()).all()

    return render_template(
        "persons.html",
        competitors=competitors,
        meet=meet,
        not_homepage=True
    )


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)