import subprocess, sys, os, time
d=os.path.dirname(os.path.abspath(__file__)); py=os.path.join(os.path.dirname(sys.executable),"python.exe")
while True:
    with open(os.path.join(d,"watcher.log"),"a") as log:
        subprocess.run([py,os.path.join(d,"watcher.py")],cwd=d,stdout=log,stderr=log,creationflags=0x08000000)
    time.sleep(5)
