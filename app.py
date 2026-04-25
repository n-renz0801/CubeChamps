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

@app.route("/persons")
def global_persons():
    all_competitors = Competitor.query.filter(
        Competitor.name != "",
        Competitor.name != "New Solver"
    ).order_by(Competitor.name.asc()).all()

    # Deduplicate by name since "Jed" may exist across multiple meets
    seen = set()
    unique_competitors = []
    for c in all_competitors:
        if c.name not in seen:
            seen.add(c.name)
            unique_competitors.append(c)

    return render_template("global_persons.html", competitors=unique_competitors)


@app.route("/meet/<int:meet_id>/person/<int:competitor_id>")
def person_detail(meet_id, competitor_id):
    meet = CubeMeet.query.get_or_404(meet_id)
    competitor = Competitor.query.get_or_404(competitor_id)

    # All solves for this competitor in this meet
    solves = (
        Solve.query
        .filter_by(competitor_id=competitor_id)
        .join(Event, Solve.event_id == Event.id)
        .filter(Event.cubemeet_id == meet_id)
        .all()
    )

    # Group solves by event → round
    events_map = {}
    for solve in solves:
        event = solve.round.event
        if event.id not in events_map:
            events_map[event.id] = {'event': event, 'rounds': []}
        events_map[event.id]['rounds'].append(solve)

    # Build result with ranking per round
    def rank_key(s):
        times = [s.attempt1, s.attempt2, s.attempt3, s.attempt4, s.attempt5]
        avg = compute_average(times)
        count = len([t for t in times if t is not None])
        avg_numeric = float('inf') if (avg is None or avg == 'DNF') else avg
        return (count, -avg_numeric)

    result = []
    for event_id, data in events_map.items():
        rounds_info = []
        for solve in sorted(data['rounds'], key=lambda s: s.round.round_number):
            # Rank: compare against all solves in that round
            all_round_solves = Solve.query.filter_by(round_id=solve.round_id).all()
            sorted_round = sorted(all_round_solves, key=rank_key, reverse=True)
            rank = next((i + 1 for i, s in enumerate(sorted_round) if s.id == solve.id), '-')

            times = [solve.attempt1, solve.attempt2, solve.attempt3, solve.attempt4, solve.attempt5]
            rounds_info.append({
                'round': solve.round,
                'solve': solve,
                'times': times,
                'average': compute_average(times),
                'best': compute_best(times),
                'rank': rank
            })

        result.append({'event': data['event'], 'rounds': rounds_info})

    return render_template(
        'person_detail.html',
        meet=meet,
        competitor=competitor,
        events_data=result,
        not_homepage=True
    )


@app.route("/persons/<string:competitor_name>")
def global_person_detail(competitor_name):
    # Get all Competitor rows that share this name (across all meets)
    all_entries = Competitor.query.filter_by(name=competitor_name).all()
    competitor_ids = [c.id for c in all_entries]

    # Get all solves for this person across all meets
    solves = Solve.query.filter(Solve.competitor_id.in_(competitor_ids)).all()

    # Group by event NAME (not id, since same event can exist in diff meets)
    events_map = {}  # event_name → { best_single, best_avg }

    for solve in solves:
        event = solve.round.event
        event_name = event.name

        times = [
            solve.attempt1, solve.attempt2, solve.attempt3,
            solve.attempt4, solve.attempt5
        ]

        single = compute_best(times)
        avg = compute_average(times)

        if event_name not in events_map:
            events_map[event_name] = {'best_single': None, 'best_avg': None}

        # Update best single
        if single is not None:
            current_single = events_map[event_name]['best_single']
            if current_single is None or single < current_single:
                events_map[event_name]['best_single'] = single

        # Update best average (lower is better, DNF is worst)
        if avg is not None and avg != 'DNF':
            current_avg = events_map[event_name]['best_avg']
            if current_avg is None or avg < current_avg:
                events_map[event_name]['best_avg'] = avg

    # Sort events alphabetically
    records = sorted(
        [{'event': name, **data} for name, data in events_map.items()],
        key=lambda x: x['event']
    )

    return render_template(
        'global_person_detail.html',
        competitor_name=competitor_name,
        records=records
    )


@app.route("/meet/<int:meet_id>/podiums")
def podiums(meet_id):
    meet = CubeMeet.query.get_or_404(meet_id)

    events_podiums = []

    for event in meet.events:
        # Get the last round of this event
        last_round = (
            Round.query
            .filter_by(event_id=event.id)
            .order_by(Round.round_number.desc())
            .first()
        )
        if not last_round:
            continue

        # Get all solves in that last round
        solves = Solve.query.filter_by(round_id=last_round.id).all()

        def rank_key(s):
            times = [s.attempt1, s.attempt2, s.attempt3, s.attempt4, s.attempt5]
            avg = compute_average(times)
            count = len([t for t in times if t is not None])
            avg_numeric = float('inf') if (avg is None or avg == 'DNF') else avg
            return (count, -avg_numeric)

        sorted_solves = sorted(solves, key=rank_key, reverse=True)
        top3 = sorted_solves[:3]

        podium_rows = []
        for rank, solve in enumerate(top3, start=1):
            times = [solve.attempt1, solve.attempt2, solve.attempt3, solve.attempt4, solve.attempt5]
            podium_rows.append({
                'rank': rank,
                'name': solve.competitor.name,
                'times': times,
                'average': compute_average(times),
                'best': compute_best(times),
            })

        events_podiums.append({
            'event': event,
            'last_round': last_round,
            'podium': podium_rows
        })

    return render_template(
        'podiums.html',
        meet=meet,
        events_podiums=events_podiums,
        not_homepage=True
    )

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)