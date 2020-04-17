# -*- coding: utf-8 -*-
"""
Created on Wed Apr 15 21:49:44 2020

@author: Demo
"""
from flask_restful import Api, Resource
from flask import request,jsonify,current_app
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import functools

def create_token(api_user):
    '''
    生成token
    :param api_user:用户id
    :return: token
    '''
    
    s = Serializer(current_app.config["SECRET_KEY"],expires_in=3600)
    token = s.dumps({"id":api_user}).decode("ascii")
    return token

def login_required(view_func):
    @functools.wraps(view_func)
    def verify_token(*args,**kwargs):
        try:
            token = request.headers["token"]
        except Exception:
            return jsonify(code = 4103,msg = '缺少参数token')
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            s.loads(token)
        except Exception:
            return jsonify(code = 4101,msg = "登录已过期")
        return view_func(*args,**kwargs)
    return verify_token

class ModelFactory():
    def __init__ (self,app):
        self.ma = Marshmallow(app)
        self.db = SQLAlchemy(app)
        self.types = {'text' : self.db.Text, "integer" : self.db.Integer , \
                 "character": self.db.String , "timestamp": self.db.DateTime,\
                 "real": self.db.Float  ,"double": self.db.Float  ,}
    
    def _create_basemodel(self,tablename, fields_):
        columns = []
        for type_,name,primary_key in fields_:
            temp = {}
            temp = {'name':name,"type_":self.types[type_.split(' ')[0]]}        
            if primary_key:
                temp["primary_key"] = True
            columns.append(self.db.Column(**temp))
        TableClass = self.db.Table(tablename,self.db.metadata,*columns)
        BaseModel = type('BaseModel', (object,), {
            '__init__': lambda self, name: setattr(self, 'name', name)
            })
        self.db.mapper(BaseModel, TableClass)
        return BaseModel
    
    def _create_model(self ,tablename , fields_):
        BaseModel = self._create_basemodel(tablename,fields_)
        
        class ModelSchema(self.ma.Schema):
            class Meta:
                fields = list(zip(*fields_))[1]
        class TableModel(BaseModel,self.db.Model):
            ## 表已存在
            __tablename__ = tablename
            model_schema = ModelSchema()
            
            def __init__ (self, **args):
                for k in args:
                    self.__setattr__(k,args[k])
#            def __repr__(self):
#            	return f"<FarmType {self.f_type_name}>"
            def delete(self):
                self.db.session.delete(self)
                self.db.session.commit()
            def insert(self):
                self.db.session.add(self)
                self.db.session.commit()
                return self.jsonfy()
            def update(self,kwargs):
                for k in self.model_schema.Meta.fields:
                    if kwargs.get(k) is not None :    
                        self.__setattr__(k,kwargs[k])
                self.db.session.commit()
                return self.jsonfy()
            def jsonfy(self):
                return self.model_schema.dump(self)
        
        return TableModel
    
    def CreateModelFromFields(self, tablename , fields_, create = False):
        model = self._create_model(tablename , fields_) 
        if create:
            self.db.create_all()
        return model
    
    def CreateModelFromTable(self,tablename):
        ## 获取表字段结构
        sql = '''SELECT format_type(a.atttypid,a.atttypmod) as type,a.attname as name,
                        a.attnotnull as notnull FROM pg_class as c,pg_attribute as a 
                    where c.relname = '%s' and a.attrelid = c.oid and a.attnum>0  '''\
                    %(tablename.lower())
        sql_query = self.db.session.execute(sql)
        fields_ = sql_query.fetchall()
        TableModel = self.CreateModelFromFields(tablename , fields_, create = False)
        return TableModel
    
        
class ResourceFactory():
    class BaseResource(Resource):
        def options(self):
            return 'ok' 

    def __init__(self,app):
        self.api = Api(app)

    def CreateResourceFromModel(self,Model):
        
        class ModelListResource(self.BaseResource):
            @login_required
            def get(self):
                ## 查                
                args = request.json
                if args is None:
                    res = Model.query.all()
                else:
                    res = Model.query.filter_by(**args).all()
                return list(map(lambda x:x.jsonfy(),res))
            
            @login_required
            def post(self):        
                ## 增
                args = request.json
                item = Model(**args)
                item.insert()
                return item.jsonfy()
                
        class ModelResource(self.BaseResource):
            @login_required
            def get(self, id_):
                ## 查
                item = Model.query.get_or_404(id_)
                return item.jsonfy()
            
            @login_required
            def put(self, id_):
                ## 改
                item = Model.query.get_or_404(id_)
                item.update(request.json)
                return item.jsonfy()
        
            @login_required
            def delete(self, id_):
                ## 删
                item = Model.query.get_or_404(id_)
                item.delete()
                return '', 204

        tablename = Model.__tablename__
        UrlList = []
        ResourceList = []
        basename = ''.join(map(lambda x:x.capitalize(),tablename.split("_"))) ## 动态创建类
        url = f'/api/{tablename}'        
        class_ = type(f'{basename}ListClass',(ModelListResource,),{})
        self.api.add_resource(class_, url)
        UrlList.append(url)
        ResourceList.append(class_)

        primary_keys = Model.__table__.primary_key.columns
        primary_keys = [(i.name,str(i.type)) for i in  primary_keys]
        if len(primary_keys)==1:
            ## 考虑单一主键情况，可绑定两接口
            types_ = {"INTEGER":"int:","TEXT":"","CHARACTER":""}
            k_name,type_ = primary_keys[0]
            url = f'/api/{tablename}/<{types_[type_]}id_>'
            class_ = type(f'{basename}Class',(ModelResource,),{})
            self.api.add_resource(class_, url)
            UrlList.append(url)
            ResourceList.append(class_)
        ## 多主键情况后续升级
                
        return ResourceList, UrlList    