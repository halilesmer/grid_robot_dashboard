Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
strDir = fso.GetParentFolderName(WScript.ScriptFullName)

' 1. Uygulama ortamını ve portunu VBS üzerinden RAM'e yazıyoruz
Set env = WshShell.Environment("PROCESS")
env("ROBOT_ENV") = "TEST"
env("STREAMLIT_PORT") = "8501"

' 2. Doğrudan sanal ortamdaki görünmez Python'u (pythonw.exe) hedef alıyoruz
pythonPath = strDir & "\.venv\Scripts\pythonw.exe"
launcherPath = strDir & "\scripts\launcher.py"

' 3. Tamamen sessiz (0 parametresi) başlatma!
WshShell.Run """" & pythonPath & """ """ & launcherPath & """ --open-browser", 0, False