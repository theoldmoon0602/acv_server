def withIndent(s, i):
    return (" " * i) + s


class Expr(object):
    pass

class Id(object):
    def __init__(self, v):
        self.v = v

    def emit(self, indent):
        return withIndent("{}".format(self.v), indent)

class Assign(object):
    def __init__(self, lhs, rhs):
        if not isinstance(lhs, Id) and not isinstance(lhs, Expr):
            lhs = Id(lhs)
        if not isinstance(rhs, Id) and not isinstance(rhs, Expr):
            rhs = Id(rhs)
        self.lhs = lhs
        self.rhs = rhs

    def emit(self, indent):
        return withIndent("{} = {};".format(self.lhs.emit(0), self.rhs.emit(0)), indent)

class Print(object):
    def __init__(self, s):
        if not isinstance(s, Id) and not isinstance(s, Expr):
            s = Id(s)
        self.s = s

    def emit(self, indent):
        return withIndent("printf(\"%s\\n\", \"{}\");".format(self.s.emit(0)), indent)

class Printi(Print):
    def emit(self, indent):
        return withIndent("printf(\"%d\\n\", {});".format(self.s.emit(0)), indent)
    
class Case(object):
    def __init__(self, expr, isDefault=False):
        self.expr = expr
        self.body = []
        self.isDefault = isDefault

    def statement(self, stmt):
        self.body.append(stmt)
        return self

    def emit(self, indent):
        s = []
        if self.isDefault:
            s.append(withIndent("default:", indent))
        else:
            s.append(withIndent("case {}:".format(self.expr.emit(0)), indent))

        for stmt in self.body:
            s.append(stmt.emit(indent + 4))
        s.append(withIndent("break;", indent + 4))
        return "\n".join(s)


class Default(Case):
    def __init__(self):
        super().__init__(None, True)

class Switch(object):
    def __init__(self, expr):
        self.expr = expr
        self.cases =[]

    def statement(self, case):
        self.cases.append(case)
        return self

    def close(self):
        pass

    def emit(self, indent):
        s = [withIndent("switch ({}) {{".format(self.expr.emit(0)), indent)]
        for c in self.cases:
            s.append(c.emit(indent + 4))
        s.append(withIndent("}", indent))
        return "\n".join(s)

class For(object):
    def __init__(self, var, start, end):
        self.var = var
        self.start = start
        self.end = end
        self.stmts = []

    def statement(self, stmt):
        self.stmts.append(stmt)
        return self

    def close(self):
        pass

    def emit(self, indent):
        s = []
        s.append(withIndent("for (int {var} = {start}; {var} < {end}; {var}++) {{".format(var=self.var.emit(0), start=self.start.emit(0), end=self.end.emit(0)), indent))
        for stmt in self.stmts:
            s.append(stmt.emit(indent + 4))
        s.append(withIndent("}", indent))
        return "\n".join(s)


class If(object):
    def __init__(self, expr):
        self.expr = expr
        self.stmts = []

    def statement(self, stmt):
        self.stmts.append(stmt)
        return self

    def close(self):
        pass

    def emit(self, indent):
        s = []
        s.append(withIndent("if ({}) {{".format(self.expr.emit(0)), indent))
        for stmt in self.stmts:
            s.append(stmt.emit(indent + 4))
        s.append(withIndent("}", indent))
        return "\n".join(s)

class ElseIf(If):
    def emit(self, indent):
        s = []
        s.append(withIndent("else if ({}) {{".format(self.expr.emit(0)), indent))
        for stmt in self.stmts:
            s.append(stmt.emit(indent + 4))
        s.append(withIndent("}", indent))
        return "\n".join(s)


class Else(object):
    def __init__(self):
        self.stmts = []

    def statement(self, stmt):
        self.stmts.append(stmt)
        return self

    def close(self):
        pass

    def emit(self, indent):
        s = []
        s.append(withIndent("else {", indent))
        for stmt in self.stmts:
            s.append(stmt.emit(indent + 4))
        s.append(withIndent("}", indent))
        return "\n".join(s)



class Main(object):
    def __init__(self):
        self.stmts = []

    def statement(self, stmt):
        self.stmts.append(stmt)
        return self

    def close(self):
        pass

    def emit(self, indent):
        s = [withIndent("int main() {\n", indent)]
        for stmt in self.stmts:
            s.append(stmt.emit(indent + 4))
        s.append(withIndent("return 0;", indent + 4))
        s.append(withIndent("}", indent))
        return "\n".join(s)


class Program(object):
    def __init__(self):
        self.cur = Main()
        self.stack = []

    def close(self):
        self.buf = []
        x = None
        while len(self.stack) > 0:
            x = self.stack.pop()
            if hasattr(x, "close"):
                for y in self.buf:
                    x.statement(y)
                self.stack.append(x)
                break
            else:
                self.buf.append(x)

        if x is None:
            for y in self.buf:
                self.stack.append(y)
        return x

    def switch(self, expr):
        if not isinstance(expr, Id) and not isinstance(expr, Expr):
            expr = Id(expr)

        if self.cur is not None:
            self.stack.append(self.cur)
        self.cur = Switch(expr)

    def __docase(self, case):
        self.buf = []
        self.stack.append(self.cur)
        if not isinstance(self.cur, Switch):
            while True:
                x = self.close()
                if isinstance(x, Switch):
                    break
                x = self.stack.pop()
                self.stack[-1].statement(x)
        self.cur = case

    def case(self, expr):
        if not isinstance(expr, Id) and not isinstance(expr, Expr):
            expr = Id(expr)
        self.__docase(Case(expr))

    def default(self):
        self.__docase(Default())

    def if_(self, expr):
        if not isinstance(expr, Id) and not isinstance(expr, Expr):
            expr = Id(expr)
        self.stack.append(self.cur)
        self.cur = If(expr)

    def else_(self):
        self.stack.append(self.cur)
        while True:
            x = self.close()
            x = self.stack.pop()
            self.stack[-1].statement(x)
            if isinstance(x, If):
                break
        self.cur = Else()

    def elseif(self, expr):
        if not isinstance(expr, Id) and not isinstance(expr, Expr):
            expr = Id(expr)
        self.stack.append(self.cur)
        while True:
            x = self.close()
            x = self.stack.pop()
            self.stack[-1].statement(x)
            if isinstance(x, If):
                break
        self.cur = ElseIf(expr)

    def for_(self, var, start, end):
        if not isinstance(var, Id) and not isinstance(var, Expr):
            var = Id(var)
        if not isinstance(start, Id) and not isinstance(start, Expr):
            start = Id(start)
        if not isinstance(end, Id) and not isinstance(end, Expr):
            end = Id(end)
        self.stack.append(self.cur)
        self.cur = For(var, start, end)


    def statement(self, stmt):
        self.cur.statement(stmt)
        
    def emit(self, indent):
        self.stack.append(self.cur)
        while True:
            x = self.close()
            if len(self.stack) == 1:
                break
            x = self.stack.pop()
            self.stack[-1].statement(x)
        return self.stack[0].emit(indent)

    def doclose(self):
        self.stack.append(self.cur)
        self.close()
        x = self.stack.pop()
        self.stack[-1].statement(x)
        self.cur = self.stack[-1]
        self.stack.pop()


def emit(program):
    from copy import deepcopy 
    p2 = deepcopy(program)
    return p2.emit(0) 

if __name__ == '__main__':
    program = Program()
    program.switch("x")
    program.case(1)
    program.statement(Assign(Id("y"), Id(0)))
    program.case(2)
    program.statement(Assign(Id("y"), Id(100)))
    program.default()
    program.statement(Assign(Id("y"), Id(10000)))
    program.doclose()
    program.for_("i", 0, 16)
    program.if_("y == 0")
    program.statement(Printi(1000))
    program.elseif("y == 1")
    program.statement(Print("Fizz"))
    program.else_()
    print(emit(program))

