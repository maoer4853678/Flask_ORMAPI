# 基于ORM的RestFul API 的工厂函数

## flask_ormapi_factory [适用于Flask开发框架] ：

	1. ModelFactory 可根据数据库已有表自动构建 ORM Model
	2. ResourceFactory 可根据 Model 自动构建 具备CRUD 的RestFul API接口

### ModelFactory

	Model工厂需要对 app进行SQLAlchemy 和 Marshmallow 的实例化对象操作
	示范代码如下：

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_ormapi_factory import ModelFactory

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://username:password@hostip/datebase"
db = SQLAlchemy(app)
ma = Marshmallow(app)

model_factory = ModelFactory(db,ma) ## 实例化 model工厂
table = "test_table"  ## 数据库中已存在的数据表名
Model = model_factory.CreateModelFromTable(table) ## Model为 基于数据表 test_table 自动映射得到的 ORM Model

if __name__ == '__main__':
    app.run(debug=True)
```

### ResourceFactory

	Resource工厂需要对 app进行 Api 的实例化对象操作
	Resource工厂构建的所有API接口，均已 Json格式 接收传参，数据记录也均以Josn格式返回
	示范代码如下：

```python
from flask_restful import Api ## new
from flask_ormapi_factory import ResourceFactory  ## new

api = Api(app)  ## new 
resource_factory = ResourceFactory(api)  ## 实例化 resource工厂
UrlList = resource_factory.CreateResourceFromModel(Model) ## 基于Model 自动创建具备 CRUD操作的 RestFul Api接口

if __name__ == '__main__':
    app.run(debug=True)
```

####  UrlList

##### 接口1
	1. 接口地址 :  /api/test_table  , 接口以数据表名作为url地址
	2. 具备Get方法， 对应数据库的查看操作，支持接收参数进行Model的filter，返回符合条件的多条记录
	3. 具备Post方法，对应数据库的插入操作，支持接收参数进行Model的单条数据insert，返回新插入的单条记录

##### 接口2
	1. 接口地址 :  /api/test_table/<type:id>  , 接口以数据表名/主键名 作为url地址，目前只支持单一主键构建接口，支持id格式匹配转换。
	2. 具备Get方法，   对应数据库的查看操作，支持通过id查询Model，返回单条记录
	3. 具备Put方法，   对应数据库的修改操作，支持接收参数对单条记录的Update，返回修改后单条记录
	4. 具备Delete方法，对应数据库的插入操作，支持通过id对单条记录的Delete