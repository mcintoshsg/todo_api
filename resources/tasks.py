''' todo resource for the flask api '''

import pdb

from flask import jsonify, Blueprint, abort, g
from flask_restful import (Resource, Api, reqparse, inputs, fields, marshal,
                            marshal_with, url_for)

from auth import auth
import models

todo_fields = {
    'id': fields.Integer,
    'name': fields.String,
}

def todo_or_404(todo_id):
    try:
        todo = models.Todo.get(models.Todo.id==todo_id)
    except models.Todo.DoesNotExist:
        abort(404)
    else:
        return todo   

class TodoList(Resource):
    ''' task list resource '''
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'name', required=True,
            help='No task provided',
            location=['form', 'json'],
           
        )
        super().__init__()

    def get(self):
        todos = [marshal(todos, todo_fields)
                    for todos in models.Todo.select()]
        print(type(todos))            
        return todos

    @marshal_with(todo_fields)
    @auth.login_required
    def post(self):
        args = self.reqparse.parse_args()
        todo = models.Todo.create(created_by=g.user, **args)
        return (todo, 201, {
                'Location': url_for('resources.todos.todo', id=todo.id)}
               )

class Todo(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'name', required=True,
            help='No task provided',
            location=['form', 'json'],
           
        )
        super().__init__()

    @marshal_with(todo_fields) # use marshal_with with a single return
    def get(self, id):
        return todo_or_404(id)

    @marshal_with(todo_fields)
    @auth.login_required   
    def put(self, id):
        args = self.reqparse.parse_args()
        query = models.Todo.update(**args).where(models.Todo.id==id)
        query.execute()
        return (models.Todo.get(models.Todo.id==id), 200,
                {'Location': url_for('resources.todos.todo', id=id)})

    @auth.login_required
    def delete(self, id):
        query = models.Todo.delete().where(models.Todo.id==id)
        query.execute()
        return '', 204, {'Location': url_for('resources.todos.todos')}

todos_api = Blueprint('resources.todos', __name__)
api = Api(todos_api)
api.add_resource(TodoList, '/todos', endpoint='todos')
api.add_resource(Todo, '/todos/<int:id>', endpoint='todo')
    