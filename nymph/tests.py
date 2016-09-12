from django.test import TestCase

# Create your tests here.

class Test1:
    t=5
    def __init__(self,**kwargs):
        self.a=kwargs.pop('a')
        self.b=kwargs.pop('b')
        super().__init__(**kwargs)

    def print(self):
        print(self.a,self.b)

    @classmethod
    def print(cls):
        print(cls.t)

class Test2:
    def __init__(self,**kwargs):
        self.c = kwargs.pop('c')
        self.d = kwargs.pop('d')
        super().__init__(**kwargs)

    def print(self):
        print(self.c, self.d)

    def add(self):
        return  self.c+self.d
class Test4:
    def __init__(self,**kwargs):
        self.e = kwargs.pop('e')
        self.f = kwargs.pop('f')
        super().__init__(**kwargs)

class Test3(Test1,Test2,Test4):
    # def __init__(self,*args,**kwargs):
    #     super().__init__(*args,**kwargs)

    # def print(self):
    #     super().print()
    #     print(self.b,self.a)
    def print(self):
        print(self.a,self.b,self.c,self.d,self.e,self.f)



if __name__=="__main__":
    t1=Test1(a=1,b=2)
    t1.print()
    t3=Test3(a=1,b=2,c=3,d=4,e=5,f=6)
    t3.print()
    print(t3.add())