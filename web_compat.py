"""
web.py兼容模块 - 为Python 3.13提供web.py的基本功能
使用Flask作为底层实现
"""

from flask import Flask, request, Response
import threading
import logging

# 禁用Flask的日志输出
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

class WebApplication:
    def __init__(self):
        self.app = Flask(__name__)
        self.urls = []
        self.handlers = {}
        self.server_thread = None
        
    def add_mapping(self, pattern, handler_class):
        """添加URL映射"""
        self.urls.extend([pattern, handler_class])
        self.handlers[pattern] = handler_class
        
        # 为Flask添加路由
        endpoint = f"handler_{len(self.handlers)}"
        self.app.add_url_rule(
            pattern, 
            endpoint=endpoint, 
            view_func=self._create_handler_func(handler_class),
            methods=['GET', 'POST', 'PUT', 'DELETE']
        )
    
    def _create_handler_func(self, handler_class):
        """创建处理函数"""
        def handler_func():
            handler = handler_class()
            method = request.method.upper()
            
            if hasattr(handler, method):
                return getattr(handler, method)()
            elif hasattr(handler, method.lower()):
                return getattr(handler, method.lower())()
            else:
                return Response("Method not allowed", status=405)
        
        return handler_func
    
    def run(self, port=8080, host='0.0.0.0'):
        """运行web服务器"""
        def run_server():
            self.app.run(host=host, port=port, debug=False, use_reloader=False)

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        return self.server_thread

    def wsgifunc(self):
        """返回WSGI应用函数"""
        return self.app

# 全局应用实例
_app = WebApplication()

# web.py兼容接口
def application(*args, **kwargs):
    """创建web应用"""
    # 忽略web.py特有的参数
    autoreload = kwargs.get('autoreload', False)

    if args:
        # 第一个参数通常是URL映射元组
        urls = args[0]
        if isinstance(urls, (tuple, list)):
            # 处理URL映射: (pattern, handler, pattern, handler, ...)
            for i in range(0, len(urls), 2):
                if i + 1 < len(urls):
                    pattern = urls[i]
                    handler_name = urls[i + 1]

                    # 如果handler_name是字符串，需要从globals中获取实际的类
                    if isinstance(handler_name, str) and len(args) > 1:
                        globals_dict = args[1]
                        # 解析模块路径
                        parts = handler_name.split('.')
                        handler_class = globals_dict
                        for part in parts:
                            if hasattr(handler_class, part):
                                handler_class = getattr(handler_class, part)
                            else:
                                # 尝试导入模块
                                try:
                                    module_path = '.'.join(parts[:-1])
                                    class_name = parts[-1]
                                    import importlib
                                    module = importlib.import_module(module_path)
                                    handler_class = getattr(module, class_name)
                                    break
                                except:
                                    handler_class = None
                                    break
                    else:
                        handler_class = handler_name

                    if handler_class:
                        _app.add_mapping(pattern, handler_class)
    return _app

def webapi():
    """获取web API对象"""
    return request

def data():
    """获取请求数据"""
    if request.method == 'POST':
        return request.get_data()
    return b''

def input(**kwargs):
    """获取请求参数"""
    result = {}
    for key, default in kwargs.items():
        if request.method == 'GET':
            result[key] = request.args.get(key, default)
        else:
            result[key] = request.form.get(key, default)
    return type('WebInput', (), result)()

class HTTPError(Exception):
    """HTTP错误"""
    def __init__(self, status, message=""):
        self.status = status
        self.message = message
        super().__init__(f"{status}: {message}")

def badrequest(message="Bad Request"):
    """返回400错误"""
    return Response(message, status=400)

def notfound(message="Not Found"):
    """返回404错误"""
    return Response(message, status=404)

def internalerror(message="Internal Server Error"):
    """返回500错误"""
    return Response(message, status=500)

# 模拟web.py的ctx对象
class Context:
    def __init__(self):
        self.env = {}
        
    @property
    def environ(self):
        return request.environ if request else {}

ctx = Context()

# httpserver模块兼容
class HTTPServer:
    @staticmethod
    def runsimple(wsgi_app, server_address):
        """运行简单HTTP服务器"""
        host, port = server_address

        def run_server():
            # 使用Flask的内置服务器
            from werkzeug.serving import run_simple
            run_simple(host, port, wsgi_app, use_reloader=False, use_debugger=False)

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        return server_thread

httpserver = HTTPServer()

# 运行函数
def run(app, port=8080, host='0.0.0.0'):
    """运行web应用"""
    return app.run(port=port, host=host)
