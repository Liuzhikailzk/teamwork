import random
import time
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import re
import qrcode
from io import BytesIO
from flask import send_file

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




class LotteryRule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    prizes = db.relationship('Prize', backref='lottery_rule', lazy=True, cascade='all, delete-orphan')
    participants = db.Column(db.String(100), nullable=False)
    mode = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(100), default='admin')
    department = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='draft')

class Prize(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    details = db.Column(db.String(200))
    lottery_rule_id = db.Column(db.Integer, db.ForeignKey('lottery_rule.id'), nullable=False)



class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    lottery_rule_id = db.Column(db.Integer, db.ForeignKey('lottery_rule.id'), nullable=True)


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

# 实现了搜索的功能
@app.route('/lottery_rules', methods=['GET', 'POST'])
def lottery_rules():
    if request.method == 'POST':
        search_query = request.form.get('search_query', '')
        rules = LotteryRule.query.filter(LotteryRule.name.contains(search_query)).filter_by(status='final').all()
    else:
        rules = LotteryRule.query.filter_by(status='final').all()
    return render_template('lottery_rules.html', rules=rules)



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


@app.route('/add_lottery_rule', methods=['GET', 'POST'], endpoint='add_lottery_rule')
def add_lottery_rule():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        participants = request.form['participants']
        mode = request.form['mode']
        department = request.form['department']
        status = request.form['status']

        # 检查是否已有暂存的规则，如果有则更新
        existing_rule = LotteryRule.query.filter_by(status='draft').first()
        if existing_rule:
            existing_rule.name = name
            existing_rule.description = description
            existing_rule.participants = participants
            existing_rule.mode = mode
            existing_rule.department = department
            existing_rule.status = status
            db.session.commit()

            # 删除现有奖品，添加新奖品
            Prize.query.filter_by(lottery_rule_id=existing_rule.id).delete()
            prize_names = request.form.getlist('prize_name[]')
            prize_quantities = request.form.getlist('prize_quantity[]')
            prize_details = request.form.getlist('prize_details[]')

            for i in range(len(prize_names)):
                prize = Prize(name=prize_names[i], quantity=prize_quantities[i], details=prize_details[i],
                              lottery_rule_id=existing_rule.id)
                db.session.add(prize)

            db.session.commit()

            if status == 'draft':
                return jsonify({"success": True, "message": "暂存成功"})
            else:
                existing_rule.status = 'final'
                db.session.commit()
                return jsonify({"success": True, "message": "提交成功"})
        else:
            rule = LotteryRule(name=name, description=description, participants=participants, mode=mode,
                               department=department, status=status)
            db.session.add(rule)
            db.session.commit()

            prize_names = request.form.getlist('prize_name[]')
            prize_quantities = request.form.getlist('prize_quantity[]')
            prize_details = request.form.getlist('prize_details[]')

            for i in range(len(prize_names)):
                prize = Prize(name=prize_names[i], quantity=prize_quantities[i], details=prize_details[i],
                              lottery_rule_id=rule.id)
                db.session.add(prize)

            db.session.commit()

            if status == 'draft':
                return jsonify({"success": True, "message": "暂存成功"})
            else:
                rule.status = 'final'
                db.session.commit()
                return jsonify({"success": True, "message": "提交成功"})

    # 获取暂存的数据，如果有的话
    draft_rule = LotteryRule.query.filter_by(status='draft').first()
    return render_template('add_lottery_rule.html', rule=draft_rule)


@app.route('/edit_lottery_rule/<int:id>', methods=['GET', 'POST'], endpoint='edit_lottery_rule')
def edit_lottery_rule(id):
    rule = LotteryRule.query.get(id)
    if request.method == 'POST':
        rule.name = request.form['name']
        rule.description = request.form['description']
        rule.participants = request.form['participants']
        rule.mode = request.form['mode']
        rule.department = request.form['department']
        rule.status = request.form['status']

        Prize.query.filter_by(lottery_rule_id=id).delete()
        prize_names = request.form.getlist('prize_name[]')
        prize_quantities = request.form.getlist('prize_quantity[]')
        prize_details = request.form.getlist('prize_details[]')

        for i in range(len(prize_names)):
            prize = Prize(name=prize_names[i], quantity=prize_quantities[i], details=prize_details[i],
                          lottery_rule_id=rule.id)
            db.session.add(prize)

        db.session.commit()

        if rule.status == 'draft':
            return jsonify({"success": True, "message": "暂存成功"})
        else:
            return jsonify({"success": True, "message": "提交成功"})

    return render_template('edit_lottery_rule.html', rule=rule)


@app.route('/delete_lottery_rule', methods=['POST'])
def delete_lottery_rule():
    rule_id = request.form.get('id')
    app.logger.info(f"Received request to delete rule with id: {rule_id}")
    rule = LotteryRule.query.get(rule_id)
    if rule:
        db.session.delete(rule)
        db.session.commit()
        app.logger.info(f"Successfully deleted rule with id: {rule_id}")
        return jsonify({"success": True})
    else:
        app.logger.error(f"Rule with id: {rule_id} not found")
        return jsonify({"success": False, "message": "Rule not found"}), 404

@app.route('/generate_qr_code', methods=['GET'])
def generate_qr_code():
    # 构造二维码数据
    name = request.args.get('name', 'Default Rule Name')
    description = request.args.get('description', 'Default Description')
    department = request.args.get('department', 'Default Department')
    participants = request.args.get('participants', 'Default Participants')
    mode = request.args.get('mode', 'Default Mode')

    data = f"Name: {name}\nDescription: {description}\nDepartment: {department}\nParticipants: {participants}\nMode: {mode}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    buffer = BytesIO()
    img.save(buffer, 'PNG')
    buffer.seek(0)
    return send_file(buffer, mimetype='image/png', as_attachment=False)
# todo 需要修改home.html实现抽奖功能
# 初始化数据库
with app.app_context():
    db.create_all()
    # 创建管理员账号
    if not User.query.filter_by(phone='admin').first():
        admin_user = User(phone='admin', password='admin', role='admin')
        db.session.add(admin_user)
        db.session.commit()


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
