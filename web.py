# -*- coding: utf-8 -*-

# Author: Dandy Qi
# Created time: 2018/12/8 14:55
# File usage: web controller

from flask import Flask, request, render_template
from flask.ext.sqlalchemy import SQLAlchemy
from flask_uploads import UploadSet, configure_uploads, patch_request_class, DATA
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField, SelectField
from wtforms.validators import DataRequired

import os
import ConfigParser
import pandas as pd

cf = ConfigParser.ConfigParser()
cf.read("config.conf")
db_host = cf.get("db", "db_remote_host")
db_user = cf.get("db", "db_user")
db_password = cf.get("db", "db_password")
db_database = cf.get("db", "db_database")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://%s:%s@%s/%s' % (db_user, db_password, db_host, db_database)
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

db = SQLAlchemy(app)

UPLOAD_PATH = "doc/"
ALLOWED_EXTENSIONS = ["csv"]

app.config['UPLOADED_DATA_DEST'] = UPLOAD_PATH
app.config['SECRET_KEY'] = 'nlp_resource'


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


class Relation(db.Model):
    __tablename__ = 'relation'

    id = db.Column('id', db.Integer, primary_key=True)
    category = db.Column('category', db.VARCHAR)
    token = db.Column('token', db.VARCHAR)
    synonym = db.Column('synonym', db.VARCHAR)
    norm_token = db.Column('norm_token', db.VARCHAR)
    extra = db.Column('extra', db.VARCHAR)
    pos = db.Column('pos', db.VARCHAR)

    def __repr__(self):
        return '<relation {}>'.format(self.id, self.token, self.category, self.synonym, self.norm_token, self.extra,
                                      self.pos)


db.create_all()


@app.route("/entity", methods=['GET'])
def entity():
    page = request.args.get('page', 1, type=int)
    context = {
        'entity': Entity.query.paginate(page, 20, False)
    }
    return render_template("entity.html", **context)


@app.route("/relation", methods=['GET'])
def relation():
    page = request.args.get('page', 1, type=int)
    context = {
        'relation': Relation.query.paginate(page, 20, False)
    }
    return render_template("relation.html", **context)


data = UploadSet("data", extensions=DATA)
configure_uploads(app, data)
patch_request_class(app)


class UploadForm(FlaskForm):
    doc = FileField(
        validators=[
            FileAllowed(data, u"只能上传CSV格式文件"),
            FileRequired(u"请选择上传文件")
        ],
        render_kw={
            "class": "form-control",
            "id": "doc"
        }
    )
    table = SelectField(
        validators=[DataRequired(u'请选择上传到哪张表')],
        choices=[(1, "entity"), (2, "relation")],
        default=1,
        coerce=int,
        render_kw={
            "class": "form-control",
            "id": "table"
        }
    )
    submit = SubmitField(
        u'上传',
        render_kw={
            "class": "btn btn-primary"
        }
    )


@app.route("/upload", methods=['GET', 'POST'])
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        filename = data.save(form.doc.data)
        file_url = data.url(filename)

        df = pd.read_csv(os.path.join(UPLOAD_PATH, filename), encoding="utf-8")
        if form.table.data == 2:
            for idx, row in df.iterrows():
                row = row.where(row.notnull(), None)
                r = Relation()
                r.category = row["category"]
                r.token = row["token"]
                r.synonym = row["synonym"]
                r.norm_token = row["norm_token"]
                r.pos = row["pos"]
                r.extra = row["extra"]
                db.session.add(r)
        elif form.table.data == 1:
            for idx, row in df.iterrows():
                row = row.where(row.notnull(), None)
                e = Entity()
                e.category = row["category"]
                e.token = row["token"]
                e.synonym = row["synonym"]
                e.norm_token = row["norm_token"]
                e.pos = row["pos"]
                e.extra = row["extra"]
                db.session.add(e)
        db.session.commit()
    else:
        file_url = None

    return render_template('upload.html', form=form, file_url=file_url)


if __name__ == '__main__':
    app.run()
