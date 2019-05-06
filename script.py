from flask import jsonify, abort, url_for
from geopy import distance
from geopy import location
import psycopg2
from datetime import datetime
import os
from flask import request
from werkzeug.utils import secure_filename
from flask import send_from_directory
from flask import Flask
from flask_uploads import IMAGES, UploadSet
from database import Database



# Конфигурация запускаемого приложения Flask
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'your_folder'
photos = UploadSet('photos', IMAGES)

        


@app.route('/location/api/v1.0/devices', methods=['GET', 'POST'])
def devices():
    all_users = []
    inf_all_users = {}
    # получаем координаты и время запроса
    lat = request.json.get('latitude', '')
    long = request.json.get('longitude', '')
    nick = request.json.get('nickname', '')
    tim = datetime.now()
    print(nick, long, lat, tim)
    Database.insertion("UPDATE devices SET latitude = (%s), longitude = (%s), timestamp =(%s) WHERE nickname = (%s)",
                   (lat, long, tim, nick,))
    rows = Database.connection("SELECT nickname from devices;","")
    for row in rows:
        if nick != row[0]:
            ls = Database.connection("SELECT latitude, longitude from devices WHERE nickname = (%s);",
                           (row[0],))
            for l in ls:
                point1 = location.Point(float(lat), float(long))
                point2 = location.Point(float(l[0]), float(l[1]))
                dist = distance.great_circle(point1, point2).m
                print(dist)
                if dist < 500.0:
                    print('found' + ' ' + row[0])
                    if row[0] not in all_users:
                        all_users.append(row[0])
                        infs = Database.connection(
                            "SELECT name, lastname, description, image from users WHERE nickname = (%s);",
                            (row[0],))
                        for inf in infs:
                            if inf[3] is not None:
                                link = 'location/api/v1.0/get_photo/' + inf[3]
                            else:
                                link = ''
                        inf_all_users[row[0]] = (inf[0], inf[1], inf[2], link)

    return jsonify(count=len(all_users), nicknames=all_users, info=inf_all_users)


# функция регистрации
@app.route('/location/api/v1.0/base', methods=['GET', 'POST'])
def database():
    try:
        # Получаем информацию о пользователе
        na = str(request.json.get('name', ''))
        ema = request.json.get('email', '')
        lastna = request.json.get('lastname', '')
        passw = request.json.get('password', '')
        bir = request.json.get('birth', '')
        nick = request.json.get('nickname', '')
        gend = request.json.get('gender', '')
        desc = request.json.get('description', '')
        print('Name:', na)
        print('Email:', ema)
        print('Lastname: ', lastna)
        print('Password:', passw)
        print('Birth:', bir)
        print('Nickname:', nick)
        print('Gender:', gend)
        #Database.hash_password(passw)

        try:
            Database.insertion("INSERT INTO users (name, email, lastname, password, birth, nickname, gender) VALUES (%s, %s, %s, %s, %s, %s, %s);",
                               (na, ema, lastna, passw, bir, nick, gend))
            print('User successfully registered')
            return jsonify(200)

        except Exception as e:
            print('User already existed')
            print(e)
            abort(400, 'User Already existed')


    except Exception as e:
        print('Global Error:', e)
        abort(400)


# функция входа
@app.route('/location/api/v1.0/entrance', methods=['GET', 'POST'])
def entrance():
    passw = request.json.get('password', '')
    ema = request.json.get('email', '')
    rows = Database.connection("SELECT name, email, lastname, password, birth, nickname, gender, image from users;", "")
    for row in rows:
        if ema == row[1]:
            print('User has been found')
            if passw == row[3]:
                print('ENTERED')
                les = Database.connection("SELECT nickname from devices;", '')
                if len(les) == 0:    ##################################################
                    Database.insertion("INSERT INTO devices (nickname) VALUES (%s);", (row[5],))
                else:
                    for le in les:
                        if row[5] != le[0]:
                            Database.insertion("INSERT INTO devices (nickname) VALUES (%s);", (row[5],))
                if row[7] is not None:
                    link = 'location/api/v1.0/get_photo/' + row[7]
                else:
                    link = ''
                return jsonify(name=row[0], email=row[1], lastname=row[2], password=row[3], birth=row[4],
                                       nickname=row[5], gender=row[6], image=link)

            else:
                abort(500, 'Wrong login or password')
    return jsonify(500)

# Функция загрузки фотографий
# curl -F file=@/Users/kim_folder/Documents/lol.png http://localhost:5000/location/api/v1.0/photo
@app.route('/location/api/v1.0/photo', methods=['GET', 'POST'])
def upload_photo():
    nick = request.headers.get('nickname')
    file = request.files[nick]
    # filename = secure_filename(file.filename)
    filename = secure_filename(file.filename)  # !!!!!!!!!!!!!!!!!!!!
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], nick + '_' + filename))
    Database.insertion("UPDATE users SET IMAGE = (%s) WHERE nickname = (%s)", (nick + '_' + filename, nick,))
    print('Uploaded. Name of the picture:' + ' ' + nick + '_' + filename)
    link = 'location/api/v1.0/get_photo/' + nick + '_' + filename
    return jsonify(image=link)


# curl http://localhost:5000/location/api/v1.0/get_photo/lolkek
@app.route('/location/api/v1.0/get_photo/<filename>', methods=['GET', 'POST'])
def send_photo(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)



if __name__ == '__main__':
    app.run('0.0.0.0', 5000)






