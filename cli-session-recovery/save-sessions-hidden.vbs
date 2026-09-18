Option Explicit
Dim shell, fso, userProfile, command, result, statusPath, status, stream, process, startedAt
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
userProfile = shell.ExpandEnvironmentStrings("%USERPROFILE%")
command = "powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & userProfile & "\save-sessions.ps1"" -Pin"
Set process = shell.Exec(command)
startedAt = Now
Do While process.Status = 0
    result = shell.Popup("Pinning the latest completed automatic recovery set. The previous pin remains safe.", 1, "CLI Session Recovery", 64)
    If DateDiff("s", startedAt, Now) >= 10 Then
        process.Terminate
        status = "Desktop Save exceeded its 10-second deadline and was stopped. The previous recovery set remains safe."
        MsgBox status, 16, "CLI Session Save Failed"
        WScript.Quit 1
    End If
Loop
result = process.ExitCode
statusPath = userProfile & "\.cli-session-vault\last-save.txt"
status = "Session saver returned exit code " & result & "."
If fso.FileExists(statusPath) Then
    Set stream = fso.OpenTextFile(statusPath, 1, False)
    status = stream.ReadAll
    stream.Close
End If
If result = 0 Then
    MsgBox status, 64, "CLI Sessions Saved"
Else
    MsgBox status, 16, "CLI Session Save Failed"
End If
