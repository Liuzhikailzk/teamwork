import random
import time
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import re

app = Flask(__name__)

# 数据库
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 初始化数据库



# 创建用户表模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    login_count = db.Column(db.Integer, default=0)


with app.app_context():
    db.create_all()

@app.route('/')
def login():
    return render_template('login.html')
@app.route('/register')
def register():
    return render_template('register.html')
@app.route('/home')
def home():
    return render_template('home.html')
@app.route('/change_password', methods=['GET'])
def change_password_page():
    return render_template('change_password.html')


@app.route('/send_sms', methods=['POST'])
def send_sms():
    # 模拟发送短信验证码
    phone_number = request.form['phone']
    # 生成一个随机的六位数验证码
    verification_code = random.randint(100000, 999999)
    # 在这里你可以调用实际的短信发送接口
    print(f"Sending SMS to {phone_number} with verification code: {verification_code}")
    # 将验证码返回给前端
    return jsonify({"code": verification_code})

@app.route('/register', methods=['POST'])
def register_user():
    phone = request.form['phone']
    code = request.form['code']
    input_code = request.form['input_code']
    agreement = request.form['agreement'] == 'true'

    if code != input_code:
        return jsonify({"success": False, "message": "短信验证码错误"})

    if not agreement:
        return jsonify({"success": False, "message": "没有选择用户使用协议"})

    user = User(phone=phone, password=phone)
    db.session.add(user)
    db.session.commit()

    return jsonify({"success": True, "message": "注册成功", "redirect": url_for('login')})



@app.route('/login', methods=['POST'])
def login_user():
    phone = request.form['phone']
    password = request.form['password']
    user = User.query.filter_by(phone=phone).first()

    if user and user.password == password:
        if password == phone:
            return jsonify({"change_password": True})
        user.login_count += 1
        db.session.commit()
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "账号和密码不正确"})
@app.route('/change_password', methods=['POST'])
def change_password():
    phone = request.form['phone']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']
    email = request.form['email']

    if not re.match(r'[A-Za-z0-9]{6,}', new_password):
        return jsonify({"success": False, "message": "密码要数字和字母组成，且长度大于六位"})

    if new_password != confirm_password:
        return jsonify({"success": False, "message": "两次密码不一致"})

    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return jsonify({"success": False, "message": "请输入正确电子邮箱"})

    user = User.query.filter_by(phone=phone).first()
    print(f"User found: {user}")
    if user:
        user.password = new_password
        db.session.commit()
        return jsonify({"success": True, "redirect": url_for('home')})
    return jsonify({"success": False, "message": "用户不存在"})


@app.route('/update_user', methods=['POST'])
def update_user():
    phone = request.form['phone']
    new_password = request.form['new_password']
    user = User.query.filter_by(phone=phone).first()

    if user:
        user.password = new_password
        db.session.commit()
        return jsonify({"success": True, "message": "用户信息更新成功"})
    return jsonify({"success": False, "message": "用户不存在"})


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
