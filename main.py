from flask import Flask, request, jsonify, redirect, url_for
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity
from flask.views import MethodView
from concurrent.futures import ThreadPoolExecutor
import mysql.connector as ms
import redis

app = Flask(__name__)
jwt = JWTManager(app)
app.config['JWT_TOKEN_LOCATION'] = ['headers', 'query_string']
app.config["JWT_SECRET_KEY"] = "eyJhbGciOiJIUzI1NiJ9.eyJSb2xlIjoiQWRtaW4iLCJJc3N1ZXIiOiJJc3N1ZXIiLCJVc2VybmFtZSI6IkphdmFJblVzZSIsImV4cCI6MTY4NTY4MzI3MCwiaWF0IjoxNjg1NjgzMjcwfQ.CWpNPSb5eYAyL-PIHFBgLmm5BFK71NWEtZ_IMm7i0FM"

cache = redis.Redis(host='localhost', port=6379, db=0)

#SQL connectivity
mydb = ms.connect(host='localhost', user='root', database='campaigner', password='')
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
    
# @app.route('/login', methods=['GET'])
# @jwt_required()
# def login(): 
#     current_user_id = get_jwt_identity()[0]
#     db_cursor.execute(f'select username from customers where userid={current_user_id}')
#     user = db_cursor.fetchone()
#     if user is not None:
#         return "Hello World"
#     else:
#         return jsonify({'msg': 'Invalid jwt token'}), 401
    
class ChannelsView(MethodView):
    threads = 10

    def get(self):
        json_data = request.get_json()
        jwt_token = json_data.get('jwt')

        # Pass the JWT to get_jwt_identity function
        current_user_id = get_jwt_identity(jwt_token)
        db_cursor.execute(f'select username from customers where userid={current_user_id}')
        user = db_cursor.fetchone()[0]
        channels = request.args.get('channels')
        if user is not None:
            cache.set('User', user)
            is_route_active = cache.get('route_active')
            cache.set('route_active', 'true')
            channels = channels.split(',')
            executor = ThreadPoolExecutor(max_workers = self.threads)
            if is_route_active is None or is_route_active.decode('utf-8') != 'true':
                for process in channels:
                    executor.submit(channels[process])
            
        else:
            return jsonify({'msg': 'Access forbidden'}), 403
    
app.add_url_rule('/channels', view_func=ChannelsView.as_view('channels'))

if __name__=="__main__":
    app.run(debug=True)