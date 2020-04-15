# -*- coding: utf-8 -*-
"""
Created on Wed Apr 15 21:49:44 2020

@author: Demo
"""
from flask_restful import Resource
from flask import request
#import copy

class ModelFactory():
    def __init__ (self,db,ma):
        self.db = db
        self.ma = ma
    
    def CreateModelFromTable(self,tablename):
        ## 获取表字段结构
        sql = '''SELECT format_type(a.atttypid,a.atttypmod) as type,a.attname as name,
                        a.attnotnull as notnull FROM pg_class as c,pg_attribute as a 
                    where c.relname = '%s' and a.attrelid = c.oid and a.attnum>0  '''\
                    %(tablename.lower())
        sql_query = self.db.session.execute(sql)
        fields_ = sql_query.fetchall()
        print (f"fields_ :  {fields_} ")
        types = {'text' : self.db.Text, "integer" : self.db.Integer , \
                 "character": self.db.String , "timestamp": self.db.DateTime,\
                 "real": self.db.Float  ,"double": self.db.Float  ,}
        columns = []
        for type_,name,primary_key in fields_:
            temp = {}
            temp = {'name':name,"type_":types[type_.split(' ')[0]]}        
            if primary_key:
                temp["primary_key"] = True
            columns.append(self.db.Column(**temp))
        TableClass = self.db.Table(tablename,self.db.metadata,*columns)
        BaseModel = type('BaseModel', (object,), {
            '__init__': lambda self, name: setattr(self, 'name', name)
            })
        self.db.mapper(BaseModel, TableClass)     
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

class ResourceFactory():
    class BaseResource(Resource):
        def options(self):
            return 'ok' 

    def __init__(self,api):
        self.api = api

    def CreateResourceFromModel(self,Model):
        
        class ModelListResource(self.BaseResource):
            def get(self):
                ## 查                
                args = request.json
                if args is None:
                    res = Model.query.all()
                else:
                    res = Model.query.filter_by(**args).all()
                return list(map(lambda x:x.jsonfy(),res))
        
            def post(self):        
                ## 增
                args = request.json
                item = Model(**args)
                item.insert()
                return item.jsonfy()
                
        class ModelResource(self.BaseResource):
            def get(self, id_):
                ## 查
                item = Model.query.get_or_404(id_)
                return item.jsonfy()
        
            def put(self, id_):
                ## 改
                item = Model.query.get_or_404(id_)
                item.update(request.json)
                return item.jsonfy()
        
            def delete(self, id_):
                ## 删
                item = Model.query.get_or_404(id_)
                item.delete()
                return '', 204

        tablename = Model.__tablename__
        UrlList = []
        basename = ''.join(map(lambda x:x.capitalize(),tablename.split("_"))) ## 动态创建类
        url = f'/{tablename}'
        UrlList.append(url)
        self.api.add_resource(type(f'{basename}ListClass',(ModelListResource,),{}), url)

        primary_keys = Model.__table__.primary_key.columns
        primary_keys = [(i.name,str(i.type)) for i in  primary_keys]
        if len(primary_keys)==1:
            ## 考虑单一主键情况，可绑定两接口
            types_ = {"INTEGER":"int:","TEXT":"","CHARACTER":""}
            k_name,type_ = primary_keys[0]
            url = f'/{tablename}/<{types_[type_]}id_>'
            UrlList.append(url)
            self.api.add_resource(type(f'{basename}Class',(ModelResource,),{}), url)
        ## 多主键情况后续升级
                
        return UrlList    