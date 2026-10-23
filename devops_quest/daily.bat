@echo off
title Ежедневный ритуал: скачал - поработал - загрузил
cd /d "%~dp0"

echo.
echo ================================================
echo    ЕЖЕДНЕВНЫЙ РИТУАЛ ДАНИЛА - 1 раз в день
echo    Скачать ^> поработать ^> сохранить ^> загрузить
echo ================================================
echo.

rem --- Шаг 0: если репозитория нет - создаём (один раз) ---
git rev-parse --git-dir >nul 2>&1
if errorlevel 1 (
  echo [0] Git-репозиторий не найден. Создаю...
  git init
)

set "REPO=%~dp0.."

rem --- .gitignore создаём один раз, чтобы мусор не попал в историю ---
if not exist "%REPO%\.gitignore" (
  echo __pycache__/> "%REPO%\.gitignore"
  echo *.pyc>> "%REPO%\.gitignore"
  echo .pytest_cache/>> "%REPO%\.gitignore"
  echo .venv/>> "%REPO%\.gitignore"
  echo .snapshots/>> "%REPO%\.gitignore"
  echo tmp/>> "%REPO%\.gitignore"
  echo scratch/>> "%REPO%\.gitignore"
  echo *.rar>> "%REPO%\.gitignore"
  echo CHAT_HISTORY_EXPORT.md>> "%REPO%\.gitignore"
  echo logs/*>> "%REPO%\.gitignore"
  echo !logs/guard_audit.jsonl>> "%REPO%\.gitignore"
  echo TEMPLATE_PORTABLE/>> "%REPO%\.gitignore"
  echo [0] Создан .gitignore - мусор не попадёт в историю.
)

rem --- Шаг 0.5: первичная настройка git (один раз) ---
git config user.name >nul 2>&1 || git config user.name "Daniil"
git config user.email >nul 2>&1 || git config user.email "daniil@local"
git config core.autocrlf false

rem --- Шаг 1: СКАЧАТЬ изменения ---
git remote | findstr /r ".*" >nul 2>&1
if not errorlevel 1 (
  echo [1] Скачиваю изменения с GitHub - git pull...
  git pull --no-rebase 2>nul || echo     Не получилось - проверь интернет. Продолжаю.
) else (
  echo [1] GitHub ещё не подключён - пропускаю скачивание.
  echo     Подключить позже: git remote add origin АДРЕС_РЕПОЗИТОРИЯ
)

rem --- Шаг 2: СОХРАНИТЬ все изменения ---
echo [2] Сохраняю изменения - git add...
git add -A

rem --- Шаг 3: контрольная точка дня ---
git diff --cached --quiet >nul 2>&1
if not errorlevel 1 goto :nothing_to_commit
for /f %%D in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set "STAMP=%%D"
git commit -m "day: %STAMP% progress backup" >nul 2>&1
if errorlevel 1 goto :commit_failed
echo [3] Контрольная точка создана: %STAMP%
goto :after_commit

:commit_failed
echo [3] ОШИБКА: коммит не создан. Сохраните этот экран и покажите Андрею или агенту.
goto :after_commit

:nothing_to_commit
echo [3] Новых изменений нет - коммит не нужен. Всё чисто.

:after_commit
rem --- Шаг 4: ЗАГРУЗИТЬ на GitHub ---
git remote | findstr /r ".*" >nul 2>&1
if not errorlevel 1 (
  echo [4] Загружаю на GitHub - git push...
  git push 2>nul || echo     Не получилось - проверь интернет или права.
) else (
  echo [4] GitHub ещё не подключён - пропуск. Не страшно:
  echo     история уже сохранена на твоём компьютере.
)

echo.
echo ================================================
echo    ГОТОВО. Ты только что использовал Git по-настоящему.
echo    Прогресс и серия дней - в надёжном месте.
echo ================================================
echo.
pause
