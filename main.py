# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 18:47:34 2020

@author: Demo
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_restful import Api
from flask_restful.utils import cors
from OrmApiFactory import ModelFactory,ResourceFactory
app = Flask(__name__)
app.secret_key = '123'

api = Api(app)
api.decorators = [cors.crossdomain(origin='*',\
    headers=['accept', 'Content-Type','Authorization'],methods={"HEAD","POST","GET",'OPTIONS','PUT','DELETE'})] ## 支持跨域

# 配置SQLALCHEMY
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:postgres@127.0.0.1/test"
app.config['SQLALCHEMY_COMMIT_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
db = SQLAlchemy(app)
ma = Marshmallow(app)
model_factory = ModelFactory(db,ma)
resource_factory = ResourceFactory(api)

## 获取所有表
sql = "select tablename from pg_tables where schemaname='public'"
sql_query = db.session.execute(sql)
tables = sql_query.fetchall()
api_urls = []
for (table,) in tables:    
    print (f"  Buliding Table {table} Model and ResourceList  ".center(70,"#"))
    Model = model_factory.CreateModelFromTable(table)    
    print (f"  Model : {table} is Already  ".center(70,"#"))
    UrlList = resource_factory.CreateResourceFromModel(Model)
    print (f"  ResourceList : {len(UrlList)} is Already  ".center(70,"#"))    
    api_urls.extend(UrlList)

print ("All Resource List Urls : ")
for url in api_urls:
    print (url)
# 
if __name__ == "__main__":
    app.run(host = '0.0.0.0',debug =True)