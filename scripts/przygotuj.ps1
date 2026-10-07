# =====================================================================
#  Osobisty Asystent AI - przygotowanie komputera (Windows)
#
#  Sprawdza, czy masz wszystko, czego potrzebuje asystent, i doinstalowuje
#  braki przez winget: Git (z Git Bash), Python, Node.js, GitHub CLI,
#  Obsidian oraz Claude Code. Na koncu pyta, czy zalogowac GitHuba
#  (potrzebny do kopii zapasowej vaulta).
#
#  Uruchomienie (PowerShell, NIE jako administrator):
#    irm https://raw.githubusercontent.com/AIBiz-Automatyzacje/osobisty-asystent-plugin/main/scripts/przygotuj.ps1 | iex
#
#  Tylko sprawdzenie, bez instalowania:
#    $env:TYLKO_SPRAWDZ=1; irm https://raw.githubusercontent.com/AIBiz-Automatyzacje/osobisty-asystent-plugin/main/scripts/przygotuj.ps1 | iex
#
#  Skrypt mozna odpalac wielokrotnie - to, co juz jest, zostawia w spokoju.
#  Plik celowo bez polskich znakow: Windows PowerShell 5.1 czyta skrypty
#  bez BOM jako ANSI i psuje litery z ogonkami.
# =====================================================================

function Invoke-PrzygotujAsystenta {
    # Calosc w funkcji: przy `irm | iex` polecenie `exit` zamkneloby okno PowerShella.
    $ErrorActionPreference = "Continue"
    $NodeMin = 18
    $TylkoSprawdz = ($env:TYLKO_SPRAWDZ -eq "1")
    $ClaudeLocalBin = Join-Path $HOME ".local\bin"

    function Ok($t)    { Write-Host "  [OK]    $t" -ForegroundColor Green }
    function Brak($t)  { Write-Host "  [BRAK]  $t" -ForegroundColor Red }
    function Uwaga($t) { Write-Host "  [UWAGA] $t" -ForegroundColor Yellow }
    function Naglowek($t) { Write-Host ""; Write-Host $t -ForegroundColor Cyan }

    function Zapytaj($pytanie, $domyslnaTak) {
        $podp = if ($domyslnaTak) { "[T/n]" } else { "[t/N]" }
        $odp = Read-Host "$pytanie $podp"
        if ([string]::IsNullOrWhiteSpace($odp)) { return $domyslnaTak }
        return @("t", "tak", "y", "yes") -contains $odp.Trim().ToLower()
    }

    # Po instalacji przez winget biezace okno nie widzi nowych sciezek - doczytujemy PATH z rejestru.
    function Odswiez-Path {
        $m = [Environment]::GetEnvironmentVariable("Path", "Machine")
        $u = [Environment]::GetEnvironmentVariable("Path", "User")
        $env:Path = (@($u, $m) | Where-Object { $_ }) -join ";"
        if ((Test-Path $ClaudeLocalBin) -and ($env:Path -notlike "*$ClaudeLocalBin*")) { $env:Path = "$ClaudeLocalBin;$env:Path" }
    }

    # ------------------------------------------------------------------
    #  Wykrywanie
    # ------------------------------------------------------------------

    function Znajdz($nazwa) {
        $c = Get-Command $nazwa -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($c) { return $c.Source } else { return $null }
    }

    function Git-Bash {
        $kandydaci = @(
            "$env:ProgramFiles\Git\bin\bash.exe",
            "${env:ProgramFiles(x86)}\Git\bin\bash.exe",
            "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe"
        )
        $git = Znajdz "git"
        if ($git) { $kandydaci += (Join-Path (Split-Path (Split-Path $git)) "bin\bash.exe") }
        foreach ($k in $kandydaci) { if ($k -and (Test-Path $k)) { return $k } }
        return $null
    }

    # "python" z WindowsApps to atrapa ze Sklepu Microsoft - otwiera Sklep zamiast dzialac.
    function Prawdziwy-Python {
        foreach ($n in @("python", "python3", "py")) {
            foreach ($c in @(Get-Command $n -All -ErrorAction SilentlyContinue)) {
                if ($c.Source -and ($c.Source -notlike "*WindowsApps*")) { return $c.Source }
            }
        }
        return $null
    }

    function Node-Major {
        $v = (& node --version 2>$null)
        if ($v -match "^v(\d+)") { return [int]$Matches[1] } else { return 0 }
    }

    function Obsidian-Sciezka {
        foreach ($k in @("$env:LOCALAPPDATA\Programs\Obsidian\Obsidian.exe", "$env:LOCALAPPDATA\Obsidian\Obsidian.exe", "$env:ProgramFiles\Obsidian\Obsidian.exe")) {
            if (Test-Path $k) { return $k }
        }
        return $null
    }

    function Sprawdz-Wszystko {
        $braki = New-Object System.Collections.ArrayList

        if (Znajdz "git") {
            Ok ("Git: " + ((& git --version) -replace "git version ", ""))
            if (Git-Bash) { Ok "Git Bash (potrzebny dla Claude Code)" } else { Brak "Git Bash - brak (przeinstaluj Git)"; [void]$braki.Add("git") }
        } else { Brak "Git (z Git Bash)"; [void]$braki.Add("git") }

        $py = Prawdziwy-Python
        if ($py) { Ok ("Python: " + ((& $py --version 2>&1) -replace "Python ", "")) }
        else { Brak "Python 3 (jesli 'python' otwiera Sklep Microsoft, to atrapa - instalujemy prawdziwy)"; [void]$braki.Add("python") }

        if (Znajdz "node") {
            $m = Node-Major
            if ($m -ge $NodeMin) { Ok ("Node.js: " + (& node --version)) }
            else { Brak ("Node.js " + (& node --version) + " - za stary, potrzebny co najmniej v$NodeMin"); [void]$braki.Add("node") }
        } else { Brak "Node.js"; [void]$braki.Add("node") }

        if (Znajdz "gh") {
            $wer = ((& gh --version | Select-Object -First 1) -split " ")[2]
            & gh auth status *> $null
            if ($LASTEXITCODE -eq 0) { Ok "GitHub CLI: $wer (zalogowany)" }
            else { Ok "GitHub CLI: $wer"; Uwaga "GitHub CLI nie jest zalogowany (potrzebne do kopii zapasowej)" }
        } else { Brak "GitHub CLI (gh)"; [void]$braki.Add("gh") }

        if (Znajdz "claude") { Ok ("Claude Code: " + (& claude --version 2>$null | Select-Object -First 1)) }
        elseif (Test-Path (Join-Path $ClaudeLocalBin "claude.exe")) { Brak "Claude Code jest zainstalowany, ale terminal go nie widzi (brak w PATH)"; [void]$braki.Add("claude_path") }
        else { Brak "Claude Code"; [void]$braki.Add("claude") }

        if (Obsidian-Sciezka) { Ok "Obsidian" } else { Brak "Obsidian"; [void]$braki.Add("obsidian") }

        return ,$braki
    }

    # ------------------------------------------------------------------
    #  Instalacja
    # ------------------------------------------------------------------

    function Winget-Instaluj($id, $opis, $override) {
        Naglowek "-> $opis"
        $argumenty = @("install", "--id", $id, "-e", "--source", "winget", "--accept-package-agreements", "--accept-source-agreements", "--silent")
        if ($override) { $argumenty += @("--override", $override) }
        & winget @argumenty
        Odswiez-Path
        # winget zwraca niezerowy kod takze wtedy, gdy pakiet juz jest - ocenia to ponowne sprawdzenie na koncu.
    }

    function Dopisz-ClaudePath {
        $u = [Environment]::GetEnvironmentVariable("Path", "User")
        if (-not $u) { $u = "" }
        if ($u -notlike "*$ClaudeLocalBin*") {
            [Environment]::SetEnvironmentVariable("Path", ($ClaudeLocalBin + ";" + $u).TrimEnd(";"), "User")
            Ok "Dopisalem $ClaudeLocalBin do PATH uzytkownika - dziala w kazdym nowym oknie"
        }
        Odswiez-Path
    }

    function Instaluj-Claude {
        Naglowek "-> Claude Code"
        try { Invoke-RestMethod https://claude.ai/install.ps1 | Invoke-Expression }
        catch { Brak ("Instalator Claude Code zglosil blad: " + $_.Exception.Message) }
        Dopisz-ClaudePath
    }

    # ------------------------------------------------------------------
    #  Start
    # ------------------------------------------------------------------

    Write-Host ""
    Write-Host "Osobisty Asystent AI - sprawdzam Twoj komputer" -ForegroundColor White
    $os = $null
    if (Get-Command Get-CimInstance -ErrorAction SilentlyContinue) { $os = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue }
    if ($os) { Write-Host ("{0} (kompilacja {1}), procesor {2}" -f $os.Caption, $os.BuildNumber, $env:PROCESSOR_ARCHITECTURE) }

    Odswiez-Path
    Naglowek "Stan przed instalacja"
    $braki = Sprawdz-Wszystko

    if ($braki.Count -eq 0) {
        Naglowek "Wszystko jest na miejscu."
    }
    elseif ($TylkoSprawdz) {
        Naglowek "Czegos brakuje ([BRAK] wyzej). Zeby doinstalowac, odpal skrypt bez TYLKO_SPRAWDZ."
        Remove-Item Env:TYLKO_SPRAWDZ -ErrorAction SilentlyContinue
        return
    }
    else {
        $potrzebaWinget = @($braki | Where-Object { $_ -in @("git", "python", "node", "gh", "obsidian") }).Count -gt 0
        if ($potrzebaWinget -and -not (Znajdz "winget")) {
            Brak "Brak winget (Instalator aplikacji Microsoft)."
            Write-Host "  Otworz Microsoft Store, wyszukaj 'Instalator aplikacji' (App Installer), kliknij Aktualizuj,"
            Write-Host "  potem zamknij PowerShell, otworz nowy i odpal skrypt jeszcze raz."
            return
        }
        Write-Host ""
        if (Zapytaj "Zainstalowac brakujace rzeczy teraz? Windows moze kilka razy zapytac o zgode - klikaj Tak." $true) {
            foreach ($b in $braki) {
                switch ($b) {
                    "git"         { Winget-Instaluj "Git.Git" "Git (z Git Bash)" $null }
                    "python"      { Winget-Instaluj "Python.Python.3.12" "Python 3.12" "/quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1" }
                    "node"        { Winget-Instaluj "OpenJS.NodeJS.LTS" "Node.js (LTS)" $null }
                    "gh"          { Winget-Instaluj "GitHub.cli" "GitHub CLI" $null }
                    "obsidian"    { Winget-Instaluj "Obsidian.Obsidian" "Obsidian" $null }
                    "claude"      { Instaluj-Claude }
                    "claude_path" { Naglowek "-> Claude Code do PATH"; Dopisz-ClaudePath }
                }
            }
            Naglowek "Stan po instalacji"
            $braki = Sprawdz-Wszystko
        }
        else { Write-Host "OK, nic nie instaluje." }
    }

    # Logowanie do GitHuba - opcjonalne, potrzebne w lekcji o kopii zapasowej.
    if ((Znajdz "gh") -and -not $TylkoSprawdz) {
        & gh auth status *> $null
        if ($LASTEXITCODE -ne 0) {
            Write-Host ""
            if (Zapytaj "Zalogowac sie teraz do GitHuba? (potrzebne do kopii zapasowej, mozesz zrobic to pozniej)" $false) {
                Write-Host "  Wybieraj: GitHub.com -> HTTPS -> Yes -> Login with a web browser. Kod skopiuj do przegladarki."
                & gh auth login -h github.com -p https -w
                if ($LASTEXITCODE -eq 0) { & gh auth setup-git; Ok "GitHub zalogowany" }
            }
        }
    }

    Naglowek "Co dalej"
    if ($braki.Count -eq 0) {
        Write-Host "  1. Zamknij to okno PowerShella i otworz nowe - dopiero nowe okno widzi swiezo zainstalowane programy."
        Write-Host "  2. Otworz Obsidiana i wroc do lekcji."
    } else {
        Write-Host "  Czesc rzeczy dalej brakuje ([BRAK] wyzej). Zamknij PowerShell, otworz nowy i odpal skrypt jeszcze raz."
        Write-Host "  Jesli znowu sie nie uda, wklej caly wynik w komentarzu pod lekcja."
    }
    Remove-Item Env:TYLKO_SPRAWDZ -ErrorAction SilentlyContinue
}

Invoke-PrzygotujAsystenta
