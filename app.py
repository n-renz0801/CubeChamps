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


from flask import Flask, render_template

app = Flask(__name__)
app.secret_key = 'cubemeettara'

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)