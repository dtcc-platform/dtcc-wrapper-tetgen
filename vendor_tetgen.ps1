#requires -Version 7.0

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$tetgenVersion = if ($env:TETGEN_VERSION) { $env:TETGEN_VERSION } else { "v1.6.0" }
$tetgenUrl = "https://codeberg.org/TetGen/TetGen/archive/$tetgenVersion.tar.gz"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = $scriptDir
$targetDir = Join-Path $repoRoot "dtcc_tetgen_wrapper/cpp/tetgen"

if (-not (Test-Path $targetDir)) {
    New-Item -ItemType Directory -Path $targetDir | Out-Null
}

$tmpTar = [System.IO.Path]::GetTempFileName()
$tmpDir = Join-Path ([System.IO.Path]::GetTempPath()) ([System.IO.Path]::GetRandomFileName())
New-Item -ItemType Directory -Path $tmpDir | Out-Null

try {
    Write-Host "Downloading $tetgenUrl"
    Invoke-WebRequest -Uri $tetgenUrl -OutFile $tmpTar

    Write-Host "Extracting archive"
    tar -xzf $tmpTar -C $tmpDir

    $srcDir = Get-ChildItem -Path $tmpDir -Directory | Select-Object -First 1
    if (-not $srcDir) {
        throw "Unable to locate extracted TetGen directory"
    }

    Write-Host "Syncing files into $targetDir"
    Get-ChildItem -Path $targetDir -Force | Remove-Item -Recurse -Force
    Copy-Item -Path (Join-Path $srcDir.FullName '*') -Destination $targetDir -Recurse -Force

    Write-Host "TetGen sources refreshed in $targetDir"
}
finally {
    if (Test-Path $tmpTar) { Remove-Item $tmpTar -Force }
    if (Test-Path $tmpDir) { Remove-Item $tmpDir -Recurse -Force }
}
