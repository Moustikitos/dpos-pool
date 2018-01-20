py -3.5-32 "C:\Python35\Scripts\cxfreeze" lib\pool.py --compress --target-dir=app/dpos-pool-win32 --include-modules=cffi,arky.ark,arky.lisk,arky.cli,ledgerblue
C:\Users\Bruno\upx.exe --best app\dpos-pool-win32\python*.dll
C:\Users\Bruno\upx.exe --best app\dpos-pool-win32\img\*.dll
C:\Users\Bruno\upx.exe --best app\dpos-pool-win32\*.pyd
