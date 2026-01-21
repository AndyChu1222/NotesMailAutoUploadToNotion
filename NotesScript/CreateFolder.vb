Sub CreateFolder(path As String)
	Dim parts As Variant
	Dim currentPath As String
	Dim i As Integer
	
	parts = Split(path, "\")
	currentPath = parts(0)
	
	For i = 1 To Ubound(parts)
		currentPath = currentPath & "\" & parts(i)
		If Dir$(currentPath, 16) = "" Then
			Mkdir currentPath
		End If
	Next
End Sub