import gldcore
class Property:
    properties = {}
    def __init__(self,obj,name,using_type=None,from_class=None):
        if not using_type:
            using_type = gldcore.get_class(from_class)[name]['type']
        if not obj in self.properties.keys():
            data = {}
            self.properties[obj] = data
        else:
            data = self.properties[obj]
        if not name in data.keys():
            addr = gldcore.get_property(obj,name)
            data[name] = addr
        else:
            addr = data[name]
        self.addr = gldcore.get_property(obj,name)
        self.get_value = eval(f"gldcore.get_{using_type}")
        self.set_value = eval(f"gldcore.set_{using_type}")

    def get(self):
        return self.get_value(self.addr)

    def set(self,value):
        return self.set_value(self.addr,value)

    def __str__(self):
        return str(self.get_value(self.addr))

    def __repr__(self):
        return f"<gldcore.property {self.addr}>"


