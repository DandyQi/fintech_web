# -*- coding: utf-8 -*-

# Author: Dandy Qi
# Created time: 2018/12/8 14:55
# File usage: web controller

from flask import Flask, request, render_template, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from flask_uploads import UploadSet, configure_uploads, patch_request_class, DATA
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField, SelectField, StringField
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
    domain = db.Column('domain', db.VARCHAR)
    category = db.Column('category', db.VARCHAR)
    token = db.Column('token', db.VARCHAR)
    synonym = db.Column('synonym', db.VARCHAR)
    norm_token = db.Column('norm_token', db.VARCHAR)
    extra = db.Column('extra', db.VARCHAR)
    pos = db.Column('pos', db.VARCHAR)

    def __repr__(self):
        return '<entity {}>'.format(self.id, self.token, self.domain, self.category, self.synonym, self.norm_token,
                                    self.extra, self.pos)


class Relation(db.Model):
    __tablename__ = 'relation'

    id = db.Column('id', db.Integer, primary_key=True)
    domain = db.Column('domain', db.VARCHAR)
    category = db.Column('category', db.VARCHAR)
    token = db.Column('token', db.VARCHAR)
    synonym = db.Column('synonym', db.VARCHAR)
    norm_token = db.Column('norm_token', db.VARCHAR)
    extra = db.Column('extra', db.VARCHAR)
    pos = db.Column('pos', db.VARCHAR)

    def __repr__(self):
        return '<relation {}>'.format(self.id, self.token, self.domain, self.category, self.synonym, self.norm_token,
                                      self.extra, self.pos)


class Knowledge(db.Model):
    __tablename__ = 'knowledge'

    id = db.Column('id', db.Integer, primary_key=True)
    category = db.Column('category', db.VARCHAR)
    sub_entity = db.Column('sub_entity', db.VARCHAR)
    relation = db.Column('relation', db.VARCHAR)
    obj_entity = db.Column('obj_entity', db.VARCHAR)
    extra = db.Column('extra', db.VARCHAR)

    def __repr__(self):
        return '<relation {}>'.format(self.id, self.category, self.sub_entity, self.relation, self.obj_entity,
                                      self.extra)


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


@app.route("/knowledge", methods=['GET'])
def knowledge():
    page = request.args.get('page', 1, type=int)
    context = {
        'knowledge': Knowledge.query.paginate(page, 20, False)
    }
    return render_template("knowledge.html", **context)


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
        choices=[(1, "entity"), (2, "relation"), (3, "knowledge")],
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
    if request.method == "POST":
        try:
            if form.validate_on_submit():
                filename = data.save(form.doc.data)
                df = pd.read_csv(os.path.join(UPLOAD_PATH, filename), encoding="utf-8", sep="\t")
                if form.table.data == 3:
                    for idx, row in df.iterrows():
                        row = row.where(row.notnull(), None)
                        k = Knowledge()
                        k.category = row["category"]
                        k.sub_entity = row["sub_entity"]
                        k.relation = row["relation"]
                        k.obj_entity = row["obj_entity"]
                        k.extra = row["extra"]
                        db.session.add(k)
                if form.table.data == 2:
                    for idx, row in df.iterrows():
                        row = row.where(row.notnull(), None)
                        r = Relation()
                        r.domain = row["domain"]
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
                        e.domain = row["domain"]
                        e.category = row["category"]
                        e.token = row["token"]
                        e.synonym = row["synonym"]
                        e.norm_token = row["norm_token"]
                        e.pos = row["pos"]
                        e.extra = row["extra"]
                        db.session.add(e)
                db.session.commit()
                msg = u"上传成功"
            else:
                msg = u"上传失败，请查看表格结构是否与上述说明相同"
        except Exception as e:
            msg = u"发生错误：%s" % e

        return render_template('upload.html', form=form, msg=msg)
    else:
        return render_template('upload.html', form=form, msg=None)


class UpdateForm(FlaskForm):
    keyword = StringField(
        render_kw={
            "class": "form-control",
            "id": "Keyword",
            "type": "hidden"
        }
    )
    table = StringField(
        render_kw={
            "class": "form-control",
            "id": "Table",
            "type": "hidden"
        }
    )
    id = StringField(
        render_kw={
            "class": "form-control",
            "id": "ID",
            "type": "hidden"
        }
    )
    domain = StringField(
        validators=[DataRequired(u'请填写所属垂域')],
        render_kw={
            "class": "form-control",
            "id": "Domain",
            "type": "text"
        }
    )
    category = StringField(
        validators=[DataRequired(u'请填写所属类别')],
        render_kw={
            "class": "form-control",
            "id": "Category",
            "type": "text"
        }
    )
    token = StringField(
        validators=[DataRequired(u'请填写词语')],
        render_kw={
            "class": "form-control",
            "id": "Token",
            "type": "text"
        }
    )
    synonym = StringField(
        render_kw={
            "class": "form-control",
            "id": "Synonym",
            "type": "text"
        }
    )
    norm_token = StringField(
        validators=[DataRequired(u'请填写规范化词语')],
        render_kw={
            "class": "form-control",
            "id": "Norm_Token",
            "type": "text"
        }
    )
    pos = StringField(
        render_kw={
            "class": "form-control",
            "id": "POS",
            "type": "text"
        }
    )
    extra = StringField(
        render_kw={
            "class": "form-control",
            "id": "Extra",
            "type": "text"
        }
    )
    submit = SubmitField(
        u'保存',
        render_kw={
            "class": "btn btn-primary"
        }
    )


@app.route('/search/', methods=['GET', 'POST'])
def search():
    form = UpdateForm()
    if request.method == "GET":
        keyword = request.args.get('keyword')
        entity_res = Entity.query.filter(
            or_(
                Entity.token.contains(keyword),
                Entity.norm_token.contains(keyword),
                Entity.synonym.contains(keyword)
            )
        ).all()
        relation_res = Relation.query.filter(
            or_(
                Relation.token.contains(keyword),
                Relation.norm_token.contains(keyword),
                Relation.synonym.contains(keyword)
            )
        ).all()
        return render_template('search_result.html', keyword=keyword, e_res=entity_res, r_res=relation_res, form=form)
    elif request.method == "POST":
        keyword = ""
        if form.validate_on_submit():
            keyword = form.keyword.data
            if form.table.data == "entity":
                item = Entity.query.filter_by(id=form.id.data).first()
                item.domain = form.domain.data
                item.category = form.category.data
                item.token = form.token.data
                item.synonym = form.synonym.data if form.synonym.data != "" else None
                item.norm_token = form.norm_token.data
                item.pos = form.pos.data
                item.extra = form.extra.data if form.extra.data != "" else None
                db.session.commit()
            elif form.table.data == "relation":
                item = Relation.query.filter_by(id=form.id.data).first()
                item.domain = form.domain.data
                item.category = form.category.data
                item.token = form.token.data
                item.synonym = form.synonym.data if form.synonym.data != "" else None
                item.norm_token = form.norm_token.data
                item.pos = form.pos.data
                item.extra = form.extra.data if form.extra.data != "" else None
                db.session.commit()

        return redirect('/search/?keyword=%s' % keyword)


if __name__ == '__main__':
    app.run()
