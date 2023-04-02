import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category, db

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
    page = request.args.get("page", 1, type = int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    app.app_context().push()
    setup_db(app)

    cors = CORS(app)

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, true')
        response.headers.add('Access-Control-Allow-Headers', 'GET, POST, PATCH, DELETE, OPTIONS')
        return response

    @app.route('/categories')
    def get_categories():
        categories = Category.query.order_by(Category.id).all()

        if len(categories) == 0:
            abort(404)

        formatted_categories = [category.format() for category in categories]
        return jsonify(
            {
                "success": True,
                "categories": formatted_categories,
            }
        )

    @app.route('/questions')
    def get_questions():
        questions = Question.query.order_by(Question.id).all()

        current_questions = []
        if len(questions) > 0:
            current_questions = paginate_questions(request, questions)

        if len(current_questions) == 0:
            abort(404)

        categories = Category.query.all()
        formatted_categories = [category.format() for category in categories]

        return jsonify(
            {
                "success": True,
                "questions": current_questions,
                "total_questions": len(questions),
                "categories": formatted_categories,
                "current_category": []
            }
        )

    @app.route('/questions/<int:id>', methods = ['DELETE'])
    def remove_question(id):
        question = Question.query.filter(Question.id == id).one_or_none()

        if question is None:
            abort(404)

        try:
            question.delete()

            questions_remain = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, questions_remain)

            return jsonify(
                {
                    "success": True,
                    "questions": current_questions,
                    "total_questions": len(questions_remain),
                    "deleted": id
                }
            )
        except:
            db.session.rollback()
            abort(422)

    @app.route('/questions', methods = ['POST'])
    def create_question():
        body = request.get_json()

        try:
            question = Question(
                question = body.get("question", None),
                answer = body.get("answer", None),
                category = body.get("category", None),
                difficulty = body.get("difficulty", None)
            )
            question.insert()

            questions = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, questions)

            return jsonify(
                {
                    "success": True,
                    "questions": current_questions,
                    "total_questions": len(questions),
                    "created": question.id
                }
            )
        except:
            db.session.rollback()
            abort(422)

    @app.route('/questions/search', methods = ['POST'])
    def search_question():
        search_term = request.get_json().get("searchTerm", None)
        
        if search_term:
            questions = Question.query.order_by(Question.id).filter(
                        Question.question.ilike("%{}%".format(search_term))
            ).all()

            if len(questions) == 0:
                abort(404)

            current_questions = paginate_questions(request, questions)

            return jsonify(
                {
                    "success": True,
                    "questions": current_questions,
                    "total_questions": len(questions),
                    "current_category": []
                }
            )

        abort(400)

    @app.route('/categories/<int:cat_id>/questions')
    def get_questions_of_category(cat_id):
        questions = Question.query.filter(Question.category == cat_id).order_by(Question.id).all()
        formatted_questions = []

        if (len(questions) > 0):
            formatted_questions = [question.format() for question in questions]

        return jsonify(
            {
                "success": True,
                "current_category": cat_id,
                "questions": formatted_questions,
                "total_questions": len(questions)
            }
        )

    @app.route('/quizzes', methods = ['POST'])
    def play_quiz():
        try:
            body = request.get_json()
            previous_questions = body.get("previous_questions", None)
            quiz_category = body.get("quiz_category", None)

            if quiz_category is None:
                questions = Question.query.filter(Question.id.notin_(previous_questions)).all()
            else:
                questions = Question.query \
                            .filter(Question.category == quiz_category['id']) \
                            .filter(Question.id.notin_(previous_questions)).all()

            question = random.choice(questions)

            return jsonify(
                {
                    "success": True,
                    "question": question.format()
                }
            )

        except:
            db.session.rollback()
            abort(422)

    @app.errorhandler(400)
    def bad_request(error):
        return (
            jsonify(
                {
                    "success": False,
                    "error": 400,
                    "message": "Bad Request"}
            ),
            400
        )

    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify(
                {
                    "success": False,
                    "error": 404,
                    "message": "Not Found"
                }
            ),
            404
        )

    @app.errorhandler(405)
    def not_found(error):
        return (
            jsonify(
                {
                    "success": False,
                    "error": 405,
                    "message": "Method Not Allowed"
                }
            ),
            405
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify(
                {
                    "success": False,
                    "error": 422,
                    "message": "Unprocessable"
                }
            ),
            422
        )

    @app.errorhandler(500)
    def internal_server_error(error):
        return (
            jsonify(
                {
                    "success": False,
                    "error": 500,
                    "message": "Internal Server Error"
                }
            ),
            500
        )

    return app

