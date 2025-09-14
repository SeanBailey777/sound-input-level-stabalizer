# sound-input-level-stabalizer

## requirement:
python3, pip, pyinstaller

## compile to binary

```shell

linux$ pyinstaller ./app.py -F --dist ./
windows> pyinstaller .\src\app.py --onefile
```

## False positive
Windows defender may block the compiled binary, execute action restore in the Windows defender.