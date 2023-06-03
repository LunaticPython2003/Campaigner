from flask import Flask, request, jsonify, redirect, url_for
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity
from flask.views import MethodView
from concurrent.futures import ThreadPoolExecutor
import mysql.connector as ms
import redis
import os
from dotenv import load_dotenv

load_dotenv()

secret_key = os.getenv('secret_key')
HOST = os.getenv('HOST')
DATABASE = os.getenv('database')
USER = os.getenv('USER')

app = Flask(__name__)
jwt = JWTManager(app)
app.config['JWT_TOKEN_LOCATION'] = ['headers', 'query_string']
app.config["JWT_SECRET_KEY"] = secret_key
app.debug = True

# cache = redis.Redis(host='localhost', port=6379, db=0)

#SQL connectivity
mydb = ms.connect(host=HOST, user=USER, database=DATABASE, password='')
db_cursor = mydb.cursor()

@app.route('/user')
def validate():
    query = request.args.values()
    username = next(query)
    userkey = next(query)
    print(type(username))
    db_cursor.execute(f'select userid from customers where username={username} and userkey={userkey}')
    userid = db_cursor.fetchone()
    if userid is None:
        return jsonify({'msg': 'Wrong username or userid'}), 401
    else:
        access_token = create_access_token(identity=userid)
        return jsonify({ "token": access_token, "user_id": userid })
    
    
class ChannelsView(MethodView):
    threads = 10

    @jwt_required()
    def post(self):
        json_data = request.get_json()
        jwt_token = json_data.get('jwt')
        current_user_id = str(get_jwt_identity()[0])

        db_cursor.execute(f"SELECT username FROM customers WHERE userid={current_user_id}")
        user = db_cursor.fetchone()[0]
        channels = json_data.get('channels')
        print(channels)
        if user is not None:
            # cache.set('User', user)
            # is_route_active = cache.get('route_active')
            # cache.set('route_active', 'true')
            for something in channels:
                print(something)

            return channels
            # executor = ThreadPoolExecutor(max_workers = self.threads)
            # if is_route_active is None or is_route_active.decode('utf-8') != 'true':
            #     for process in channels:
            #         executor.submit(channels[process])
            
        else:
            return jsonify({'msg': 'Access forbidden'}), 403
    
app.add_url_rule('/channels', view_func=ChannelsView.as_view('channels'))

if __name__=="__main__":
    app.run(debug=True)