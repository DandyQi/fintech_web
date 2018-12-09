# -*- coding: utf-8 -*-

# Author: Dandy Qi
# Created time: 2018/12/8 14:55
# File usage: web controller

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask import render_template

import ConfigParser


cf = ConfigParser.ConfigParser()
cf.read("config.conf")
db_host = cf.get("db", "db_local_host")
db_user = cf.get("db", "db_user")
db_password = cf.get("db", "db_password")
db_database = cf.get("db", "db_database")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://%s:%s@%s/%s' % (db_user, db_password, db_host, db_database)
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

db = SQLAlchemy(app)


class Entity(db.Model):
    __tablename__ = 'entity'

    id = db.Column('id', db.Integer, primary_key=True)
    category = db.Column('category', db.VARCHAR)
    token = db.Column('token', db.VARCHAR)
    synonym = db.Column('synonym', db.VARCHAR)
    norm_token = db.Column('norm_token', db.VARCHAR)
    extra = db.Column('extra', db.VARCHAR)
    pos = db.Column('pos', db.VARCHAR)

    def __repr__(self):
        return '<entity {}>'.format(self.id, self.token, self.category, self.synonym, self.norm_token, self.extra,
                                    self.pos)


db.create_all()


@app.route('/index')
def index():
    context = {
        'entity': Entity.query.all()
    }
    return render_template("index.html", **context)


if __name__ == '__main__':
    e = Entity()
    print(e.query.first().token)
    app.run()
