import subprocess
from uuid import uuid4
import os

def compile_and_run(program):
    base = str(uuid4()).replace("-", "")
    sname = "/tmp/" + base + ".c"
    oname = "/tmp/" + base + ".out"

    with open(sname, "w") as f:
        f.write(program)
    p = subprocess.Popen(["gcc", sname, "-o", oname], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    p.communicate(program.encode(), timeout=5)
    p.kill()
    try:
        r = subprocess.check_output([oname], timeout=5)
        return r.decode().splitlines(), True
    except subprocess.CalledProcessError:
        return "Compile Error", False
    except FileNotFoundError:
        return "Runtime Error", False

    try:
        os.remove(sname)
    except FileNotFoundError:
        pass
    try:
        os.remove(oname)
    except FileNotFoundError:
        pass
