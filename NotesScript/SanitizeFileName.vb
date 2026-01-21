Function SanitizeFileName(fileName As String) As String
	Dim illegalChars As String
	illegalChars = "\/:*?""<>|"
	
	Dim cleaned As String
	cleaned = ""
	
	Dim i As Integer
	Dim ch As String
	Dim code As Long
	
	For i = 1 To Len(fileName)
		ch = Mid$(fileName, i, 1)
		code = Asc(ch)
		
		' 跳過非法符號
		If Instr(illegalChars, ch) > 0 Then
			cleaned = cleaned & "_"
		' 跳過控制字元
		Elseif code < 32 Or code = 127 Then
			cleaned = cleaned & "_"
		' 跳過 Unicode 擴展字元（LotusScript 無法直接判斷 > U+FFFF，只能透過無法解析的字元排除）
		Elseif code = Asc("?") And ch <> "?" Then
			cleaned = cleaned & "_" ' 無法被 LotusScript 正常處理的擴展字元（如𡘙）通常變成「?」
		Else
			cleaned = cleaned & ch
		End If
	Next
	
	SanitizeFileName = cleaned
End Function