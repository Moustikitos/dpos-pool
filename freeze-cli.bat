py -3.5 "C:\Python35\Scripts\cxfreeze" arky_1.x\pool.py --compress --target-dir=app/dpos-pool-amd64 --include-modules=cffi,arky.ark,arky.lisk,arky.cli
C:\Users\Bruno\upx.exe --best app\dpos-pool-amd64\python*.dll
C:\Users\Bruno\upx.exe --best app\dpos-pool-amd64\img\*.dll
C:\Users\Bruno\upx.exe --best app\dpos-pool-amd64\*.pyd

py -3.5-32 "C:\Program Files (x86)\Python35\Scripts\cxfreeze" arky_1.x\pool.py --compress --target-dir=app/dpos-pool-win32 --include-modules=cffi,arky.ark,arky.lisk,arky.cli
C:\Users\Bruno\upx.exe --best app\dpos-pool-win32\python*.dll
C:\Users\Bruno\upx.exe --best app\dpos-pool-win32\img\*.dll
C:\Users\Bruno\upx.exe --best app\dpos-pool-win32\*.pyd
