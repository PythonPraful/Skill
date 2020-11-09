from datetime import datetime

from flask import g, request, jsonify
from flask_restful import Resource
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from random import sample
from string import ascii_letters as letters, digits as digits
import smtplib
import config


class SendMail:
    def sendmail(self, mails, username, otp):
        smtp_server = config.config.get("smtpserver")
        smtp_port = config.config.get("smtpport")
        recipient = mails
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'one time password'
        msg['From'] = config.config.get("email")
        msg['To'] = recipient
        text = f"""Hi {username}

                                         ######### Welcome to Skill Test #########

                                         Your otp is : {otp}"""
        part = MIMEText(text, 'plain')
        msg.attach(part)
        mail = smtplib.SMTP(smtp_server, smtp_port)
        mail.ehlo()
        mail.starttls()
        mail.login(config.config.get("email"), config.config.get("smtppass"))
        mail.sendmail(config.config.get("email"), recipient, msg.as_string())
        mail.quit()


class UserLogin(Resource):
    def post(self, action):
        mail = SendMail()
        if action == 'generateotp':
            cur = g.appdb.cursor()
            data = request.json
            username = data["username"]
            email = data["email"]
            if 'username' not in data and 'email' not in data:
                return jsonify({"message": "failed", "status": "HTTP_400_BAD_REQUEST"})
            otp = ''.join(sample(letters + digits, 6))
            mail.sendmail(email, username, otp)
            cur.execute("select email from User_details where email=%s", email)
            user_data = cur.fetchone()
            created_on = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            if user_data and user_data.get("email"):
                cur.execute("update User_details set otp=%s where email=%s", (otp, email))
                g.appdb.commit()
                return jsonify({'status': 'Success', 'Response': "OTP sent Successfully"})
            else:
                cur.execute("""insert into User_details(name,email,otp,created_on) values(%s,%s,%s,%s)""", (username, email, otp,created_on))
                g.appdb.commit()
                return jsonify({'status': 'Success', 'Response': "User registered and otp sent successfully"})
        if action == 'validate':
            cur = g.appdb.cursor()
            data = request.json
            email = data.get("email", False)
            otp = data.get('otp', False)
            validate_query = "select user_id,name,email,otp from User_details where email=%s and otp=%s"
            cur.execute(validate_query, (email, otp))
            user_data = cur.fetchone()
            print("##################", user_data)
            if email == user_data.get("email") and otp == user_data.get("otp"):
                cur.execute("update User_details set otp ='valid' where email = %s", email)
                g.appdb.commit()
                return jsonify({'status': 'success', 'action': 'Validation Done',
                                "user_id": user_data["user_id"], "user_name": user_data["name"]})
            else:
                return jsonify({'status': 'Failed', 'action': 'Invalid OTP'})
