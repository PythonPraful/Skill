from flask import Flask, g
from flask_restful import Api
from Users.Admin import Admin, AddQuestion, Questions, Participants,\
    Statistics, Category, RandomQuestions, UserTestCount, NumberOfQuestion
from Users.Auth import UserLogin
from Users.Test import TestDetails, TestResult, TestResultsById, TakingTest,\
                        ParticipantsTests
import pymysql
import config
import sys

app = Flask(__name__)
api = Api(app)


def connect_db():
    try:
        db = pymysql.connect(host=config.config.get('dbhost'),
                             user=config.config.get("dbuser"),
                             passwd=config.config.get("dbpass"),
                             db=config.config.get("dbname"),
                             cursorclass=pymysql.cursors.DictCursor)
        return db
    except ConnectionError as error:
        sys.exit(str(error))


def get_db():
    if not hasattr(g, 'appdb'):
        g.appdb = connect_db()
    return g.appdb


@app.before_request
def before_request():
    g.appdb = get_db()


@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'appdb'):
        g.appdb.close()


api.add_resource(Admin, '/adminlogin', endpoint="Admin")
api.add_resource(UserLogin, '/userlogin/<string:action>', endpoint="UserLogin")
api.add_resource(AddQuestion, '/addquestion', endpoint="Add_Question")
api.add_resource(Category, '/catogorylist', endpoint="Catogory")
api.add_resource(RandomQuestions, '/testquestions', endpoint="Random_questions")
api.add_resource(TakingTest, '/savetestresults', endpoint="TakingTest")
api.add_resource(TestDetails, '/testDetails', endpoint="TestDetails")
api.add_resource(TestResult, '/testresults/<user_id>', endpoint="TestResult")
api.add_resource(TestResultsById, '/testresultsbyId/<test_id>',
                 endpoint="TestResultsById")
api.add_resource(NumberOfQuestion, '/numberofquestion',
                 endpoint="NumberOfQuestion")
api.add_resource(Questions, '/question', endpoint="Questions")
api.add_resource(Participants, '/participentslist', endpoint="Participents")
api.add_resource(Statistics, '/stats', endpoint="Statistics")
api.add_resource(UserTestCount, '/usertestcount/<id>',
                 endpoint="UserTestCount")
api.add_resource(ParticipantsTests, '/participantstests', endpoint="ParticipantsTests")


if __name__ == '__main__':
    app.run(debug=True, host="192.168.2.58")
