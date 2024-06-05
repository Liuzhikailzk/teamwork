import random
import time
from flask import Flask, render_template, request, redirect, url_for, jsonify
import re

app = Flask(__name__)

# 模拟数据库
users = {}


@app.route('/')
def login():
    return render_template('login.html')


@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/home')
def home():
    return render_template('home.html')
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

    users[phone] = {"password": phone}
    return jsonify({"success": True, "message": "注册成功", "redirect": url_for('login')})



@app.route('/login', methods=['POST'])
def login_user():
    phone = request.form['phone']
    password = request.form['password']

    if phone in users and users[phone]['password'] == password:
        if password == phone:
            return jsonify({"change_password": True})
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

    users[phone]['password'] = new_password
    users[phone]['email'] = email
    return jsonify({"success": True})


if __name__ == '__main__':
    app.run(debug=True)
