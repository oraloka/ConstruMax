from app import db

class PaymentProof(db.Model):
    __tablename__ = 'payment_proof'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    mimetype = db.Column(db.String(64), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=db.func.now())
    order = db.relationship('Order', backref=db.backref('payment_proof', uselist=False), foreign_keys=[order_id])
