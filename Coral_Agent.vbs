Set objFSO = CreateObject("Scripting.FileSystemObject")
strScriptDir = objFSO.GetParentFolderName(WScript.ScriptFullName)

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = strScriptDir
WshShell.Run "venv\Scripts\pythonw.exe main.py", 0, False
