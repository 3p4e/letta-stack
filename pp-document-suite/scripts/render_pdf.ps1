# render_pdf.ps1 — render every .docx in a folder to PDF via Microsoft Word COM.
# Usage:  powershell -File render_pdf.ps1 -dir "C:\path\to\folder"
param([Parameter(Mandatory=$true)][string]$dir)
$word = New-Object -ComObject Word.Application
$word.Visible = $false; $word.DisplayAlerts = 0
Get-ChildItem $dir -Filter *.docx | ForEach-Object {
    $pdf = [System.IO.Path]::ChangeExtension($_.FullName, ".pdf")
    $doc = $word.Documents.Open($_.FullName, $false, $true)   # confirmConversions=false, readOnly=true
    $doc.ExportAsFixedFormat($pdf, 17)                        # 17 = wdExportFormatPDF
    $doc.Close(0)                                             # 0 = wdDoNotSaveChanges
    "rendered: " + (Split-Path $pdf -Leaf)
}
$word.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
