@echo off
setlocal
chcp 65001 >nul
title Civic Helper - 2-Stages Instap (Windows)
cd /d "%~dp0"

echo =======================================================================
echo          CIVIC HELPER - 2-STAGES INSTAP EN OMGEVINGSINRICHTER
echo                   Simon Stevin Keten-Grootboek
echo =======================================================================
echo.
echo Deze instap brengt je in twee rustige fasen van een schone computer
echo naar een volledig werkende persoonlijke werkomgeving:
echo.
echo   * STAGE 1 [Machinekamer]:
echo     Vraagt om je Gmail-adres, controleert Python 3, Git, Antigravity CLI
echo     [agy], haalt de GitHub-suite binnen, koppelt de gratis NVIDIA NIM
echo     modellen voor de Multi-LLM audit, en installeert alle benodigde tools.
echo.
echo   * STAGE 2 [Aan Tafel]:
echo     Opent het Tafelvenster [gui\tafel_gui.py] met de standaard-prompt
echo     'Verbind Omgeving'. Je lokale klerk [+agy] controleert rustig de
echo     mappen, het persoonsmasker [pii_mask.py] en e-mail, en stelt telkens
echo     maar een eenvoudige vraag tegelijk om dossiers op te bouwen.
echo.
echo =======================================================================
echo.

:: -------------------------------------------------------------------------
:: STAP 1: VRAAG OM HET GMAIL-ADRES
:: -------------------------------------------------------------------------
:vraag_gmail
set "GMAIL="
echo We beginnen met een gewoon Gmail-adres.
echo Dit adres geeft je 100%% gratis toegang tot twee onafhankelijke AI-pijlers:
echo   1. Google Antigravity CLI [Gemini Flash] als je lokale dossier-klerk.
echo   2. NVIDIA NIM [1.000 gratis model-credits op build.nvidia.com] voor de Multi-LLM audit.
echo Geen creditcard, geen betaald abonnement, geen verborgen kosten.
echo.
set /p GMAIL="Voer je Gmail-adres in (bijv. voornaam.achternaam@gmail.com): "
if "%GMAIL%"=="" (
    echo [!] Vul alsjeblieft een geldig e-mailadres in om verder te gaan.
    echo.
    goto vraag_gmail
)
echo.
echo [+] Gmail-adres ingesteld: %GMAIL%
echo.

:: -------------------------------------------------------------------------
:: STAP 2: PYTHON 3 CONTROLE EN INSTALLATIE
:: -------------------------------------------------------------------------
echo [*] Stap 2/7: Python 3 controleren...
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [*] Python is nog niet aanwezig op dit systeem.
    echo [*] Bezig met automatische installatie via Windows Package Manager [winget]...
    where winget >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        winget install --id Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements
        if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
            set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"
        )
    ) else (
        echo [!] Winget niet gevonden. Installeer Python 3.12 handmatig vanaf https://www.python.org/downloads/
        pause
        exit /b 1
    )
)
python --version >nul 2>nul
if %ERRORLEVEL% equ 0 (
    for /f "tokens=*" %%v in ('python --version') do echo [+] Gevonden: %%v
) else (
    echo [!] Python kon niet worden gestart. Controleer je PATH-variabele.
)
echo.

:: -------------------------------------------------------------------------
:: STAP 3: GIT CONTROLE EN INSTALLATIE
:: -------------------------------------------------------------------------
echo [*] Stap 3/7: Git controleren...
where git >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [*] Git is nog niet aanwezig. Bezig met installatie via winget...
    where winget >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements
        if exist "C:\Program Files\Git\cmd\git.exe" set "PATH=C:\Program Files\Git\cmd;%PATH%"
    )
)
where git >nul 2>nul
if %ERRORLEVEL% equ 0 (
    for /f "tokens=*" %%g in ('git --version') do echo [+] Gevonden: %%g
) else (
    echo [!] Git ontbreekt nog.
)
echo.

:: -------------------------------------------------------------------------
:: STAP 4: ANTIGRAVITY CLI [AGY] BINNENTREKKEN EN REGISTREREN
:: -------------------------------------------------------------------------
echo [*] Stap 4/7: Antigravity CLI [agy] controleren...
where agy >nul 2>nul
if %ERRORLEVEL% neq 0 (
    if exist "%LOCALAPPDATA%\agy\bin\agy.exe" (
        set "PATH=%LOCALAPPDATA%\agy\bin;%PATH%"
    ) else (
        echo [*] Antigravity CLI wordt binnengehaald via winget...
        where winget >nul 2>nul
        if %ERRORLEVEL% equ 0 (
            winget install --id Google.AntigravityCLI -e --accept-source-agreements --accept-package-agreements
            if exist "%LOCALAPPDATA%\agy\bin\agy.exe" set "PATH=%LOCALAPPDATA%\agy\bin;%PATH%"
        )
    )
)

where agy >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [+] Antigravity CLI [agy] staat gereed.
    call agy install --skip-aliases >nul 2>nul
    if not exist "%USERPROFILE%\.gemini\antigravity-cli\antigravity-oauth-token" (
        echo.
        echo [*] Eenmalige Google-koppeling voor Antigravity:
        echo [*] Log in je browser in met: %GMAIL%
        start "" agy
    )
) else (
    echo [!] Antigravity CLI niet in PATH. We gaan door; agy kan ook later worden toegevoegd.
)
echo.

:: -------------------------------------------------------------------------
:: STAP 5: GITHUB SUITE BINNENHALEN / BIJWERKEN
:: -------------------------------------------------------------------------
echo [*] Stap 5/7: Civic Case Engine suite controleren...
if exist "%~dp0.git" (
    echo [*] Git-repository herkend. Bezig met ophalen van laatste wijzigingen [git pull]...
    git pull --quiet
    echo [+] Suite is up-to-date.
) else (
    if not exist "%~dp0gui\tafel_gui.py" (
        echo [*] Bezig met binnenhalen van de Civic Case Engine suite...
        git clone https://github.com/XDupont-lab/Civic-Case-Engine.git CivicHelper
        cd CivicHelper
        echo [+] Suite binnengehaald in CivicHelper.
    ) else (
        echo [+] Bestanden van de suite zijn lokaal aanwezig.
    )
)
echo.

:: -------------------------------------------------------------------------
:: STAP 6: GRATIS NVIDIA NIM REGISTRATIE [MET HETZELFDE GMAIL-ADRES]
:: -------------------------------------------------------------------------
echo [*] Stap 6/7: Gratis NVIDIA NIM Modellen controleren [Multi-LLM kruistoets]...
set "NV_BESTAAT="
powershell -NoProfile -Command "if ([System.Environment]::GetEnvironmentVariable('NVIDIA_API_KEY', 'User')) { exit 0 } else { exit 1 }"
if %ERRORLEVEL% equ 0 set "NV_BESTAAT=1"
if defined NVIDIA_API_KEY set "NV_BESTAAT=1"

if defined NV_BESTAAT (
    echo [+] NVIDIA_API_KEY is al actief in je Windows-omgeving [Nemotron 120B en GPT-OSS gereed].
) else (
    echo.
    echo =======================================================================
    echo  GRATIS TWEEDE AI-CONTROLEUR [NVIDIA NIM] MET HETZELFDE GMAIL-ADRES
    echo =======================================================================
    echo  Civic Helper eist een onafhankelijke kruistoets op brieven en besluiten.
    echo  Via build.nvidia.com krijg je met %GMAIL% direct 1.000 gratis credits
    echo  zonder creditcard of abonnement.
    echo.
    set /p KEUZE_NV="Wil je nu direct je gratis NVIDIA-sleutel activeren? (J/N) [J]: "
    if /i not "%KEUZE_NV%"=="N" (
        echo [*] Browser opent naar build.nvidia.com/settings/api-keys...
        start https://build.nvidia.com/settings/api-keys
        echo.
        echo  1. Klik rechtsboven op 'Sign In' of 'Log In'.
        echo  2. Kies 'Continue with Google' en selecteer: %GMAIL%
        echo  3. Klik op 'Generate API Key' en kopieer de sleutel [begint met nvapi-].
        echo.
        set /p NV_KEY="Plak hier je nvapi-... sleutel (of druk op Enter om later te doen): "
        if not "%NV_KEY%"=="" (
            powershell -NoProfile -Command "[System.Environment]::SetEnvironmentVariable('NVIDIA_API_KEY', '%NV_KEY%', 'User')"
            set "NVIDIA_API_KEY=%NV_KEY%"
            echo [+] NVIDIA_API_KEY veilig opgeslagen in Windows-omgeving [nooit in git/bestanden].
        )
    )
)
echo.

:: -------------------------------------------------------------------------
:: STAP 7: EXTRA SOFTWARE EN PYTHON-BIBLIOTHEKEN INSTALLEREN
:: -------------------------------------------------------------------------
echo [*] Stap 7/7: Benodigde Python-bibliotheken controleren en installeren...
if exist "%~dp0requirements.txt" (
    python -m pip install -q -r "%~dp0requirements.txt"
    echo [+] Bibliotheken gereed [PyQt6, pypdf, pymupdf, requests, winocr, sound].
) else (
    python -m pip install -q PyQt6 pypdf pymupdf requests
    echo [+] Basisbibliotheken geïnstalleerd.
)

:: Mappen en persoonsmasker initialiseren
if exist "%~dp0gui\omgeving_inrichter.py" (
    python "%~dp0gui\omgeving_inrichter.py" >nul 2>nul
    echo [+] Veilige werkmappen [werk/, Dossier/, Incoming_Letters/] en persoonsmasker ingericht.
)

:: Maak optioneel een snelkoppeling op het Bureaublad
powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([System.IO.Path]::Combine([System.Environment]::GetFolderPath('Desktop'), 'Civic Helper - De Tafel.lnk')); $s.TargetPath = [System.IO.Path]::Combine('%~dp0', 'CivicHelper.cmd'); $s.WorkingDirectory = '%~dp0'; $s.Description = 'Civic Helper Tafelvenster'; $s.Save()" >nul 2>nul
echo [+] Snelkoppeling 'Civic Helper - De Tafel' aangemaakt op je Bureaublad.
echo.

:: -------------------------------------------------------------------------
:: OVERDRACHT NAAR STAGE 2 [AAN TAFEL]
:: -------------------------------------------------------------------------
echo =======================================================================
echo  STAGE 1 VOLTOOID!
echo  Gereedschap, Gmail [%GMAIL%], agy en NVIDIA staan gereed.
echo.
echo  START STAGE 2:
echo  Het Tafelvenster opent nu en start de standaard-prompt 'Verbind Omgeving'.
echo  Je lokale klerk [+agy] verwelkomt je aan Tafel en helpt je stap voor stap!
echo =======================================================================
echo.

if exist "%~dp0CivicHelper.cmd" (
    call "%~dp0CivicHelper.cmd" --verbind-omgeving
    exit /b 0
)

if exist "%~dp0gui\tafel_gui.py" (
    start "" pythonw "%~dp0gui\tafel_gui.py" --verbind-omgeving
    exit /b 0
)

pause
