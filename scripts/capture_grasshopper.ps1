Add-Type -AssemblyName System.Drawing
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Text;

public static class GhWindowApi
{
    public delegate bool WindowCallback(IntPtr handle, IntPtr data);
    [DllImport("user32.dll")] public static extern bool EnumWindows(WindowCallback callback, IntPtr data);
    [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr handle, StringBuilder text, int max);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr handle);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr handle, out uint processId);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr handle);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr handle, int command);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr handle, out Rect rect);
    [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr handle, IntPtr insertAfter, int x, int y, int width, int height, uint flags);

    [StructLayout(LayoutKind.Sequential)]
    public struct Rect { public int Left, Top, Right, Bottom; }
}
'@

$rhinoIds = @(Get-Process Rhino -ErrorAction Stop | ForEach-Object { [uint32]$_.Id })
$windows = New-Object System.Collections.ArrayList
$callback = [GhWindowApi+WindowCallback]{
    param([IntPtr]$handle, [IntPtr]$data)
    $processId = [uint32]0
    [void][GhWindowApi]::GetWindowThreadProcessId($handle, [ref]$processId)
    if ($rhinoIds -contains $processId -and [GhWindowApi]::IsWindowVisible($handle)) {
        $title = New-Object System.Text.StringBuilder 256
        [void][GhWindowApi]::GetWindowText($handle, $title, $title.Capacity)
        [void]$windows.Add([pscustomobject]@{ Handle = $handle; Title = $title.ToString() })
    }
    return $true
}
[void][GhWindowApi]::EnumWindows($callback, [IntPtr]::Zero)
$grasshopperWindows = @($windows | Where-Object { $_.Title -like 'Grasshopper*' })
if ($grasshopperWindows.Count -ne 1) {
    $grasshopperWindows | Select-Object Title
    throw "Expected one visible Grasshopper window; found $($grasshopperWindows.Count)."
}
$window = $grasshopperWindows[0]

$topmost = [IntPtr](-1)
$notTopmost = [IntPtr](-2)
$noMoveOrSize = [uint32]0x0003
$previous = [GhWindowApi]::GetForegroundWindow()
try {
    if (-not [GhWindowApi]::SetWindowPos($window.Handle, $topmost, 0, 0, 0, 0, $noMoveOrSize)) {
        throw 'Could not temporarily show Grasshopper above other windows.'
    }
    $activated = [GhWindowApi]::SetForegroundWindow($window.Handle)
    Start-Sleep -Milliseconds 500
    $rect = New-Object GhWindowApi+Rect
    if (-not [GhWindowApi]::GetWindowRect($window.Handle, [ref]$rect)) {
        throw 'Could not read Grasshopper window bounds.'
    }
    $width = $rect.Right - $rect.Left
    $height = $rect.Bottom - $rect.Top
    if ($width -le 0 -or $height -le 0) {
        throw 'Grasshopper window has invalid bounds.'
    }
    $bitmap = New-Object System.Drawing.Bitmap($width, $height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    try {
        $graphics.CopyFromScreen($rect.Left, $rect.Top, 0, 0, $bitmap.Size)
        $path = Join-Path (Split-Path -Parent $PSScriptRoot) 'references\rhino7-visible-probe-screen.png'
        $bitmap.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
        Write-Output "CAPTURED=$path TITLE=$($window.Title) SIZE=${width}x${height} ACTIVE=$activated"
    } finally {
        $graphics.Dispose()
        $bitmap.Dispose()
    }
} finally {
    [void][GhWindowApi]::SetWindowPos($window.Handle, $notTopmost, 0, 0, 0, 0, $noMoveOrSize)
    if ($previous -ne [IntPtr]::Zero) {
        [void][GhWindowApi]::SetForegroundWindow($previous)
    }
}
