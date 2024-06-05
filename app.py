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
    role = db.Column(db.String(20), default='user')  # 新增字段，用于区分用户角色


# 初始化数据库
with app.app_context():
    db.create_all()
    # 创建管理员账号
    if not User.query.filter_by(phone='admin').first():
        admin_user = User(phone='admin', password='admin', role='admin')
        db.session.add(admin_user)
        db.session.commit()



@app.route('/')
def login():
    return render_template('login.html')


@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')


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
        if user.role == 'admin':
            return jsonify({"success": True, "redirect": url_for('admin_dashboard')})
        if password == phone:
            return jsonify({"change_password": True})
        user.login_count += 1
        db.session.commit()
        return jsonify({"success": True, "redirect": url_for('home')})
    return jsonify({"success": False, "message": "账号和密码不正确"})


def calculate_password_strength(password):
    score = 0

    # 一、密码长度
    if len(password) <= 4:
        score += 5
    elif 5 <= len(password) <= 7:
        score += 10
    else:
        score += 25

    # 二、字母
    if re.search('[a-zA-Z]', password):
        if re.search('[a-z]', password) and re.search('[A-Z]', password):
            score += 20
        else:
            score += 10
    else:
        score += 0

    # 三、数字
    if re.search('[0-9]', password):
        score += 10
    else:
        score += 0

    return score

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

    password_strength = calculate_password_strength(new_password)
    if password_strength < 30:
        return jsonify({"success": False, "message": "密码强度不够，请使用更复杂的密码"})

    user = User.query.filter_by(phone=phone).first()
    if user:
        user.password = new_password
        db.session.commit()
        return jsonify({"success": True, "redirect": url_for('home')})
    return jsonify({"success": False, "message": "用户不存在"})



@app.route('/logout', methods=['POST'])
def logout():
    # 在这里可以执行任何需要的清理操作，例如清理会话数据
    return jsonify({"success": True, "redirect": url_for('login')})


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

#todo 需要修改home.html实现抽奖功能

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)

