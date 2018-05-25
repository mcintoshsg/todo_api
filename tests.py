from base64 import b64encode, b64decode
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

    def get_headers(user):
        return {
                'Authorization': 'Basic ' + b64encode(
                    bytes(user.username + ':' + 'password', 'ascii')
                ).decode('ascii')
            }


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

    def test_get_users(self):
        with test_database(TEST_DB, (User,)):
            UserModelTestCase.create_users(1)
            response = self.app.get('/api/v1/users')
            self.assertEqual(User.select().get().username, 'user_0')  
      
    def test_post_new_user(self):
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

    def test_user_already_exists(self):
        user_data = {
                'username': 'user_1',
                'email': 'test_1@example.com',
                'password': 'password',
                'verify_password': 'passwor'
        }
        UserModelTestCase.create_users(1)
        
        with test_database(TEST_DB, (User,)):
            response = self.app.post('/api/v1/users', data=user_data)
            self.assertEqual(response.status_code, 400)  
            self.assertRaises(Exception)    

    def test_no_username_provided(self):
        user_data = {
            'email': 's@test.com',
            'password': 'password',
            'verify_password': 'password'
        }
        with test_database(TEST_DB, (User,)):
            response = self.app.post('/api/v1/users', data=user_data)
            self.assertEqual(response.status_code, 400)  
            self.assertIn('No username provided',
                        response.get_data(as_text=True))                        

    def test_no_email_provided(self):
        user_data = {
            'username': 'stuart',
            'password': 'password',
            'verify_password': 'password'
        }
        with test_database(TEST_DB, (User,)):
            response = self.app.post('/api/v1/users', data=user_data)
            self.assertEqual(response.status_code, 400)  
            self.assertIn('No email provided',
                        response.get_data(as_text=True))                        

    def test_no_password_provided(self):
        user_data = {
            'username': 'stuart',
            'email': 's@test.com',
            'verify_password': 'password'
        }
        with test_database(TEST_DB, (User,)):
            response = self.app.post('/api/v1/users', data=user_data)
            self.assertEqual(response.status_code, 400)  
            self.assertIn('No password provided',
                        response.get_data(as_text=True))                        

    def test_no_verify_password_provided(self):
        user_data = {
            'username': 'stuart',
            'email': 's@test.com',
            'password': 'password'
        }
        with test_database(TEST_DB, (User,)):
            response = self.app.post('/api/v1/users', data=user_data)
            self.assertEqual(response.status_code, 400)  
            self.assertIn('No password verification',
                        response.get_data(as_text=True))                        
                                  

class TodoResourceTestCase(BaseTestCase):
    ''' test the user api resourcses '''
    def test_get_todos_no_auth(self):
        response = self.app.get('/api/v1/todos')
        self.assertEqual(response.status_code, 401) 
        self.assertIn('Unauthorized Access',
                        response.get_data(as_text=True))

    def test_get_todos_with_auth(self):
        test = ['Walk Dog', 'Clean Car']
        
        with test_database(TEST_DB, (Todo, )):
            TodoModelTestCase.create_todos()
            user = User.select().get()
            headers = UserModelTestCase.get_headers(user)
            
            response = self.app.get('/api/v1/todos', headers=headers)
            self.assertEqual(response.status_code, 200) 
            for item in response.get_json():
                self.assertIn(item['name'], test)
    
    def test_get_single_todo(self):
       with test_database(TEST_DB, (Todo, )):
            TodoModelTestCase.create_todos()
            user = User.select().get()
            headers = UserModelTestCase.get_headers(user)
           
            response = self.app.get('/api/v1/todos/'
                                    + str(Todo.select().get().id),
                                    headers=headers)
            self.assertEqual(response.status_code, 200) 
            self.assertEqual(Todo.select().get().name, 'Walk Dog')

           
    def test_get_single_todo_does_not_exist(self):
       with test_database(TEST_DB, (Todo, )):
            TodoModelTestCase.create_todos()
            user = User.select().get()
            headers = UserModelTestCase.get_headers(user)
        
            response = self.app.get('/api/v1/todos/3', headers=headers)
            self.assertEqual(response.status_code, 404) 
               
    def test_good_post_todo(self):
        UserModelTestCase.create_users(1)
        user = User.select().get()
        todo_data = {
            'name': 'Finish Project',
            'created_by': user.id
        }
        headers = UserModelTestCase.get_headers(user)
        
        with test_database(TEST_DB, (Todo,)):
            response = self.app.post('/api/v1/todos', data=todo_data,
                                    headers=headers)
            self.assertEqual(response.status_code, 201)  
            self.assertEqual(Todo.select().get().name, 'Finish Project')
            self.assertEqual(response.location, 
                            'http://localhost/api/v1/todos/1') 

    def test_bad_post_todo(self):
        UserModelTestCase.create_users(1)
        user = User.select().get()
        todo_data = {
            'created_by': user.id
        }
        headers = UserModelTestCase.get_headers(user)

        with test_database(TEST_DB, (Todo,)):
            response = self.app.post('/api/v1/todos', data=todo_data,
                                    headers=headers)
            self.assertEqual(response.status_code, 400)  
            self.assertIn('No task provided',
                        response.get_data(as_text=True))
           
    def test_delete_todo(self):
       with test_database(TEST_DB, (Todo, )):
            TodoModelTestCase.create_todos()
            user = User.select().get()
            headers = UserModelTestCase.get_headers(user)
            
            response = self.app.delete('/api/v1/todos/' + 
                                        str(Todo.select().get().id), 
                                        headers=headers)

            self.assertEqual(response.status_code, 204) 
            self.assertNotEqual(Todo.select().get().name, 'Walk Dog')
            self.assertEqual(response.location, 
                            'http://localhost/api/v1/todos')    
        
    def test_put_todo(self):
       with test_database(TEST_DB, (Todo, )):
            TodoModelTestCase.create_todos()
            user = User.select().get()
            headers = UserModelTestCase.get_headers(user)
            
            todo_data = {'name': 'Feed Dog'}
           
            response = self.app.put('/api/v1/todos/' 
                                    + str(Todo.select().get().id), 
                                    data=todo_data, headers=headers)
            self.assertEqual(response.status_code, 200) 
            self.assertEqual(Todo.select().get().name, 'Feed Dog')
            self.assertEqual(response.location, 
                            'http://localhost/api/v1/todos/1') 
        
                     



if __name__ == '__main__':
    unittest.main()
