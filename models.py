from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Lottery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    prizes = db.Column(db.String(200), nullable=False)
    participants = db.relationship('User', secondary='lottery_participants', backref='lotteries')
    winners = db.relationship('User', secondary='lottery_winners', backref='won_lotteries')

    def draw_winners(self):
        import random
        participants_list = self.participants[:]
        random.shuffle(participants_list)
        winners = participants_list[:len(self.prizes.split(','))]
        self.winners.extend(winners)
        return [winner.phone_number for winner in winners]

lottery_participants = db.Table('lottery_participants',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('lottery_id', db.Integer, db.ForeignKey('lottery.id'), primary_key=True)
)

lottery_winners = db.Table('lottery_winners',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('lottery_id', db.Integer, db.ForeignKey('lottery.id'), primary_key=True)
)
