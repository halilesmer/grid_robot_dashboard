Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' strDir artık ana klasör
strDir = fso.GetParentFolderName(WScript.ScriptFullName)

venvPath = strDir & "\.venv"
launcherPath = strDir & "\scripts\launcher.py"

' 1. Uygulama ortamını ve portunu VBS üzerinden RAM'e yazıyoruz
Set env = WshShell.Environment("PROCESS")
env("ROBOT_ENV") = "LIVE"
env("STREAMLIT_PORT") = "8520"

' 2. Akıllı Kurulum Kontrolü (Self-Healing)
If Not fso.FolderExists(venvPath) Then
    ' Eğer .venv yoksa: Kullanıcıyı uyarır ve kurulumu gözüken bir pencerede yapar
    MsgBox "İlk kurulum algılandı. Gerekli kütüphaneler indirilirken lütfen açılan siyah pencerenin otomatik kapanmasını bekleyin (1-2 dakika sürebilir).", 64, "Kurulum"
    
    installCmd = "cmd.exe /c cd /d """ & strDir & """ && python -m venv .venv && .venv\Scripts\python.exe -m pip install -r requirements.txt && .venv\Scripts\pythonw.exe """ & launcherPath & """ --open-browser"
    WshShell.Run installCmd, 1, False
Else
    ' Eğer .venv zaten varsa: Siyah ekran OLMADAN tamamen sessiz başlatır!
    pythonwPath = venvPath & "\Scripts\pythonw.exe"
    WshShell.Run """" & pythonwPath & """ """ & launcherPath & """ --open-browser", 0, False
End If