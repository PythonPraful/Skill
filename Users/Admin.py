from flask_restful import Resource
from flask_api import status
from flask import g, request, jsonify
from datetime import datetime
import config


class Admin(Resource):
    def post(self):
        try:
            data = request.json
            if "username" and "password" in data:
                user_name = config.config.get('username') == data['username']
                password = config.config.get('password') == data['password']
                if user_name and password:
                    return jsonify({"status": status.HTTP_200_OK, "Response": "Login successfully"})
            return jsonify({"status": status.HTTP_404_NOT_FOUND, "Response": "Invalid Credentials"})
        except Exception as err:
            return jsonify({"Error": str(err)})


class AddQuestion(Resource):
    def post(self):
        try:
            data = request.json
            cursor = g.appdb.cursor()
            created_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if 'category_id' not in data.keys():
                search_query = cursor.execute(("select category_id from Category where category_name=%s"),data['category_name'])
                if search_query:
                    category_id = search_query
                else:
                    cursor.execute("INSERT INTO Category(category_name) VALUES(%s)", (data['category_name'].upper()))
                    g.appdb.commit()
                    category_id = cursor.lastrowid
            else:
                category_id = data['category_id']

            cursor.execute("""INSERT INTO Question_master(question_name, category_id, created_at) \
                            VALUES(%s,%s,%s)""", (data['question'], category_id, created_date))
            g.appdb.commit()
            question_id = cursor.lastrowid
            cursor.execute("INSERT INTO Answer(question_id, opt1, opt2, opt3, opt4, correct) \
                            VALUES(%s,%s,%s,%s,%s,%s)", (question_id, data['option 1'],
                                                         data['option 2'], data['option 3'], data['option 4'],
                                                         data['correct']))
            g.appdb.commit()
            return jsonify({"status": status.HTTP_200_OK, "Response": "Question Created Successfully"})
        except Exception as err:
            return jsonify({"Error": str(err)})


class Category(Resource):
    def get(self):
        try:
            cursor = g.appdb.cursor()
            cursor.execute("select category_id,category_name from Category")
            category = cursor.fetchall()
            return jsonify({"status": "success", "response": category})
        except Exception as err:
            return jsonify({"Error": str(err)})


class Questions(Resource):
    def get(self):
        if "page" and "count" in request.args:
            cursor = g.appdb.cursor()
            page = int(request.args.get('page'))
            count = int(request.args.get('count'))
            start = (page - 1) * count

            query1 = """SELECT c.category_name,q.question_id,q.question_name,
                        a.correct,te.test_taken_on FROM Category c
                        INNER JOIN Question_master q ON c.category_id=q.category_id
                        INNER JOIN Answer a ON q.question_id=a.question_id 
                        INNER JOIN  Test_question t ON t.question_id=q.question_id 
                        INNER JOIN Test_details te ON t.test_id=te.test_id 
                        WHERE flag='active' LIMIT {start}, {count}"""

            query2 = "SELECT COUNT(*) AS total FROM Question_master"
            cursor.execute(query2)
            total_records = cursor.fetchall()

            filter_data = query1.format(start=start, count=count)
            cursor.execute(filter_data)
            result = cursor.fetchall()
            return jsonify({"status": "success", "response": result,"per_page": count,"page":page,"total_record": total_records[0]["total"]})
        else:
            return jsonify({"status": "Count not found in query parameter", "response": "failure"})

    def put(self):
        try:
            cursor = g.appdb.cursor()
            data = request.json
            query = "update Question_master SET flag='delete' where question_id= %s"
            question_update = cursor.execute(query, data['question_id'])
            g.appdb.commit()
            return jsonify({"status": status.HTTP_200_OK, "response": question_update})
        except Exception as err:
            return jsonify({"Error": str(err)})


class Participants(Resource):
    def get(self):
        try:
            cursor = g.appdb.cursor()
            cursor.execute("select name from User_details")
            result = cursor.fetchall()
            return jsonify({"status": status.HTTP_200_OK, "response": result})
        except Exception as err:
            return jsonify({"Error": str(err)})


class Statistics(Resource):
    def get(self):
        try:
            cursor = g.appdb.cursor()
            cursor.execute(
                "select count(category_id) as categories from Category;")
            categories = cursor.fetchall()[0]['categories']

            cursor = g.appdb.cursor()
            cursor.execute(
                "select count(user_id) as participants from User_details;")
            participants_list = cursor.fetchall()[0]['participants']

            cursor = g.appdb.cursor()
            cursor.execute(
                "select count(question_id) as questions from Question_master where flag='active'")
            questions = cursor.fetchall()[0]['questions']

            cursor = g.appdb.cursor()
            cursor.execute("select count(test_id) as tests from Test_details")
            test_details = cursor.fetchall()[0]['tests']
            return jsonify({"status": status.HTTP_200_OK,
                            "response": [{"total_tests": test_details, "total_category": categories,
                                         "total_questions": questions, "total_participants_list": participants_list}]})
        except Exception as err:
            return jsonify({"Error": str(err)})


class RandomQuestions(Resource):
    def get(self):
        try:
            cursor = g.appdb.cursor()
            no_questions = request.args.get('questions')
            category_id = tuple(request.args.getlist("category_id"))
            query = """select c.category_name,q.question_name,q.question_id,a.correct,a.opt1,a.opt2,a.opt3,a.opt4
                        from Category c inner join Question_master q on c.category_id=q.category_id 
                        inner join Answer a on q.question_id=a.question_id 
                        where {part} and flag='active' order by RAND() LIMIT {no_questions}"""

            if len(category_id) == 1:
                part = 'c.category_id = %s' % category_id[0]
            else:
                part = 'c.category_id IN {category_id}'.format(category_id=category_id)
            query = query.format(part=part, no_questions=no_questions)
            cursor.execute(query)
            questions = cursor.fetchall()
            selected_question = []

            for one in questions:
                options = []
                options.append({'name': one['opt1']})
                options.append({'name': one['opt2']})
                options.append({'name': one['opt3']})
                options.append({'name': one['opt4']})
                one.pop('opt1')
                one.pop('opt2')
                one.pop('opt3')
                one.pop('opt4')
                one['options'] = options
                selected_question.append(one)

            return jsonify({"status": status.HTTP_200_OK, "response": selected_question})
        except Exception as err:
            return jsonify({"Error": str(err)})


class UserTestCount(Resource):
    def get(self, id):
        try:
            cursor = g.appdb.cursor()
            cursor.execute(
                f"select count(user_id) as user_id from Test_details where user_id = {id};")
            user_count = cursor.fetchall()[0]['user_id']
            return jsonify({"status": status.HTTP_200_OK, "total_tests": user_count})
        except Exception as err:
            return jsonify({"Error": str(err)})


class NumberOfQuestion(Resource):
    def get(self):
        if "page" and "count" in request.args:
            cursor = g.appdb.cursor()
            page = int(request.args.get('page'))
            count = int(request.args.get('count'))
            start = (page - 1) * count

            query1 = """SELECT qm.question_id,qm.question_name,ca.category_name,
                        DATE_FORMAT(qm.created_at,"%Y-%m-%d")AS DATE,an.correct FROM Question_master qm
                        INNER JOIN Answer an ON
                        qm.question_id=an.question_id
                        INNER JOIN Category ca ON
                        qm.category_id=ca.category_id LIMIT {start},{count}"""

            query2="SELECT COUNT(*) AS total FROM Question_master"
            cursor.execute(query2)
            total_records= cursor.fetchall()
            filter_data= query1.format(start=start, count=count)
            cursor.execute(filter_data)
            result = cursor.fetchall()
            return jsonify({"status": "success", "response": result,"per_page": count,"page": page,"total_record": total_records[0]["total"]})
        else:
            return jsonify({"status": "page/ count not found in query parameter", "response": "failure"})

