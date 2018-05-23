import json
import unittest


from playhouse.test_utils import test_database
from peewee import *

from app import app
from models import User, Todo

TEST_DB = SqliteDatabase(':memory:')


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()
        
        TEST_DB.connect()
        TEST_DB.create_tables([User, Todo], safe=True)
    
    def tearDown(self):
        TEST_DB.drop_tables(User, Todo)
        TEST_DB.close()
        


class UserModelTestCase(BaseTestCase):
    ''' test cases for the user model '''
    @staticmethod # static method as it does not access anything in the class
    def create_users(count=2):
        ''' this test creates 2 users in the database via a function called
            create_users 
        '''
        for i in range(count):
            User.create_user(
                username='user_{}'.format(i),
                email='test_{}@example.com'.format(i),
                password='password'
            )

    def test_create_user(self):
        ''' test the creation of the user '''
        with test_database(TEST_DB, (User, )):
            self.create_users()
            self.assertEqual(User.select().count(), 2)
            self.assertNotEqual(
                User.select().get().password,
                'password'
            )

class TodoModelTestCase(BaseTestCase):
    ''' test cases for the todo model '''
    @staticmethod
    def create_todos():
        UserModelTestCase.create_users(1)
        user = User.select().get()
        Todo.create(name='Walk Dog', created_by=user.id)
        Todo.create(name='Clean Car', created_by=user.id)


    def test_create_todos(self):
        ''' test the creation of todos '''
        with test_database(TEST_DB, (Todo, )):    
            self.create_todos()
            self.assertEqual(Todo.select().count(), 2)
            self.assertEqual(
                Todo.select().get().name,
                'Walk Dog'
            )

class ViewTestCase(BaseTestCase):
    ''' test the index page loads with the appropriate data '''
    def test_index_page_loads(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('<h1>My TODOs!</h1>', response.get_data(as_text=True))

class UserResourceTestCase(BaseTestCase):
    ''' test the user api resourcses '''
    def test_new_user(self):
        user_data = {
            'username': 'stuart',
            'email': 's@test.com',
            'password': 'password',
            'verify_password': 'password'
        }

        with test_database(TEST_DB, (User,)):
            response = self.app.post('/api/v1/users', data=user_data)
            self.assertEqual(response.status_code, 201)  
         
    def test_bad_password_combination(self):
        user_data = {
            'username': 'stuart',
            'email': 's@test.com',
            'password': 'password',
            'verify_password': 'pass'
        }
        r_test = '{"error": "Password and password verification do not match"}'
        with test_database(TEST_DB, (User,)):
            response = self.app.post('/api/v1/users', data=user_data)
            self.assertEqual(response.status_code, 400)  
            self.assertIn(r_test,
                        response.get_data(as_text=True))    

class TodoResourceTestCase(BaseTestCase):
    '''


        # TodoModelTestCase.create_todos()
        # todo = Todo.select().get()
        #     basic_header = {
        #         'Authorization': 'Basic ' + base64.b64encode(
        #             bytes(user.username + ':' + 'password', 'ascii')
        #         ).decode('ascii')
        #     }
        #     rv = self.app.get('/api/v1/users/token', headers=basic_header)
        #     self.assertEqual(rv.status_code, 200)
          
'''
Tests:

3. Check the tasks resource - add 2 new todos and check the response headers 
    'location' and that the resource data contains the 2 new todos
4. Check the tasks resource for a post with 'no task provided in json response'
5. Check for a single todo response with teh corrct location id'
6. Check for a 404 response if todo id does not exist
7. Check for updated Todo - changes in resource data 
8. Check for updated Todo in response 
9. Check for deleted Tdod - i.e. get 404 does not exist
10. Check login and not login - i.e. No todos and todoa 

'''


if __name__ == '__main__':
    unittest.main()
