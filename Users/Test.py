from flask_restful import Resource
from flask import g, jsonify, request
from flask_api import status
from datetime import datetime


class TestDetails(Resource):
    def get(self):
        try:
            if "page" and "count" in request.args:
                cursor = g.appdb.cursor()
                page = int(request.args.get('page'))
                count = int(request.args.get('count'))
                start = (page - 1) * count
                query = """SELECT ud.user_id, ud.name, COUNT(td.user_id) AS no_attempts FROM Test_details td
                                    INNER JOIN User_details ud ON td.user_id = ud.user_id 
                                    GROUP BY td.user_id"""
                pagequery = query + ' LIMIT {start}, {count}'.format(start=start, count=count)
                cursor.execute(query)
                total_recs = cursor.fetchall()
                cursor.execute(pagequery)
                current_page = cursor.fetchall()

                return jsonify({"status": status.HTTP_200_OK, "Response": current_page, "per_page": count, "page":page,
                                'total_recs': len(total_recs)})
            else:
                return jsonify({"status": "Count not found in query parameter", "response": "failure"})
        except Exception as err:
            return jsonify({"Error": str(err)})

class TestResult(Resource):
    def get(self,user_id):
        if "page" and "count" in request.args:
            cursor = g.appdb.cursor()
            page = int(request.args.get('page'))
            count = int(request.args.get('count'))
            start = (page - 1) * count

            query1 = """SELECT tq.test_id, ud.name, td.no_questions, td.marks,\
                            date_format(td.test_taken_on,'%Y-%m-%d') as test_date\
                            FROM Test_details td JOIN User_details ud ON td.user_id = ud.user_id\
                            JOIN Test_question tq ON tq.test_id=td.test_id\
                            JOIN Question_master qm ON qm.question_id=tq.question_id\
                            JOIN Category c ON c.category_id=qm.category_id where ud.user_id= {user_id}
                            group by td.test_id LIMIT {start},{count}"""
            
            filter_data = query1.format(user_id=user_id, start=start, count=count)
            cursor.execute(filter_data)
            result = cursor.fetchall()
            return jsonify({"status": "success", "response": result, "per_page": count, "page":page})
        else:
            return jsonify({"status": "Count not found in query parameter", "response": "failure"})


class TestResultsById(Resource):
    def get(self, test_id):
        try:
            cursor = g.appdb.cursor()
            query = """SELECT td.marks, qm.question_name, tq.user_answer, tq.correct FROM Test_question tq
                        join Test_details td on td.test_id = tq.test_id 
                        join Question_master qm on qm.question_id= tq.question_id where tq.test_id = %s"""
            cursor.execute(query, test_id)
            result = cursor.fetchall()
            return jsonify({"status": status.HTTP_200_OK, "Response": result})
        except Exception as err:
            return jsonify({"Error": str(err)})


class TakingTest(Resource):
    def post(self):
        answers = request.json['answer']
        user_id = request.json['user_id']
        cursor = g.appdb.cursor()
        marks = 0
        total_questions = len(answers)
        test_taken_on = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        test_results = []
        for record in answers:
            q_id = record["question_id"]
            useranswer = record["correct"]
            query = '''SELECT correct FROM Answer WHERE question_id = %s'''
            cursor.execute(query, q_id)
            result = cursor.fetchone()
            if result['correct'] == useranswer:
                marks += 1
            else:
                pass
            values = q_id, useranswer, result['correct']
            test_results.append(values)
        insert_query = """INSERT INTO Test_details(user_id, marks, test_taken_on, no_questions) VALUES (%s,%s,%s,%s)"""
        cursor.execute(insert_query, (user_id, marks,
                                      test_taken_on, total_questions))
        g.appdb.commit()
        test_id = cursor.lastrowid
        insert_TestQuestion = """INSERT INTO Test_question (test_id, question_id, user_answer, correct) VALUES (%s,%s,%s,%s)"""
        for rec in test_results:
            cursor.execute(insert_TestQuestion,
                           (test_id, rec[0], rec[1], rec[2]))
            g.appdb.commit()
        return jsonify({"total_questions": total_questions, 'score': marks})

class ParticipantsTests(Resource):
    def get(self):
        user_id = request.args.get('user_id')
        cursor = g.appdb.cursor()
        query1 = """select ud.user_id, ud.name, td.no_questions,
                    td.test_taken_on, td.marks from Test_details td 
                    join User_details ud on td.user_id = ud.user_id 
                    where ud.user_id={user_id}"""
        
        filter_data = query1.format(user_id=user_id)
        cursor.execute(filter_data)
        result = cursor.fetchall()
        return jsonify({"status": "success", "response": result})