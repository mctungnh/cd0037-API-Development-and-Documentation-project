import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        DB_HOST = os.getenv('DB_HOST', '127.0.0.1:5432')
        DB_USER = os.getenv('DB_USER', 'postgres')
        DB_NAME = os.getenv('DB_NAME', 'trivia_test')
        DB_PATH = 'postgresql+psycopg2://{}@{}/{}'.format(DB_USER, DB_HOST, DB_NAME)
        setup_db(self.app, DB_PATH)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
    
    def tearDown(self):
        """Executed after reach test"""
        pass

    def test_get_categories_200(self):
        '''
            Test getting categories successfully
        '''
        res = self.client().get("/categories")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(len(data["categories"]))

    def test_get_categories_405(self):
        '''
            Test using wrong method on categories endpoint
        '''
        res = self.client().delete("/categories")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 405)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "Method Not Allowed")

    def test_get_paginated_questions_200(self):
        '''
            Test getting paginated questions successfully
        '''
        res = self.client().get("/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["total_questions"])
        self.assertTrue(len(data["questions"]))
        self.assertTrue(len(data["categories"]))

    def test_get_paginated_questions_404(self):
        '''
            Test getting paginated questions out of range
        '''
        res = self.client().get("/questions?page=1000")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "Not Found")

    def test_remove_question_200(self):
        '''
            Test removing a question successfully
        '''
        removable_question = Question(question="Q", answer="A", category = 1, difficulty = 1)
        removable_question.insert()
        removable_question_id = removable_question.id

        res = self.client().delete('/questions/{}'.format(removable_question_id))
        data = json.loads(res.data)

        question = Question.query.filter(Question.id == removable_question_id).one_or_none()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["deleted"], removable_question_id)
        self.assertTrue(len(data["questions"]))
        self.assertTrue(data["total_questions"])
        self.assertEqual(question, None)

    def test_remove_question_404(self):
        '''
            Test removing a non-existed question
        '''
        res = self.client().delete('/questions/100')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "Not Found")

    def test_create_question_200(self):
        '''
            Test creating a new question successfully
        '''
        question_len = len(Question.query.all())

        new_question = {
            "question": "Q",
            "answer": "A",
            "difficulty": 1,
            "category": 1
        }

        res = self.client().post("/questions", json = new_question)
        data = json.loads(res.data)
        new_question_len = data["total_questions"]

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(new_question_len - 1, question_len)

    def test_create_question_400(self):
        '''
            Test creating a new question with bad request
        '''
        res = self.client().post("/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "Bad Request")

    def test_search_questions_200(self):
        '''
            Test searching questions
        '''
        search_term = {'searchTerm': 'Which'}
        res = self.client().post('/questions/search', json = search_term)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertIsNotNone(data["questions"])
        self.assertIsNotNone(data["total_questions"])

    def test_search_questions_400(self):
        '''
            Test searching questions with a bad request
        '''
        search_term = {'searchTerm': ''}
        res = self.client().post('/questions/search', json = search_term)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "Bad Request")

    def test_search_questions_404(self):
        '''
            Test searching non-existed question
        '''
        search_term = {'searchTerm': '>?<'}
        res = self.client().post('/questions/search', json = search_term)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "Not Found")

    def test_get_paginated_questions_of_category_200(self):
        '''
            Test getting paginated questions of a category successfully
        '''
        res = self.client().get('/categories/6/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["total_questions"])
        self.assertTrue(data["current_category"])
        self.assertTrue(len(data["questions"]))

    def test_play_quiz_200(self):
        '''
            Test playing quiz successfully
        '''
        quiz = {'quiz_category': {'type': 'Entertainment', 'id': 5}, 'previous_questions': []}
        res = self.client().post('/quizzes', json = quiz)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["question"])

    def test_play_quiz_422(self):
        '''
            Test playing quiz with no information
        '''
        res = self.client().post('/quizzes')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "Unprocessable")

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()