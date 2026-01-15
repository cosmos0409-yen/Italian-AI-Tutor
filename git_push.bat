@echo off
echo ==========================================
echo    Quick Git Push for Italian App
echo ==========================================
echo.

:: Check if .git exists
if not exist .git (
    echo Error: Not a git repository. Initializing...
    git init
)

:: Add all changes
echo Adding files...
git add .

:: Ask for commit message
set /p commit_msg="Enter commit message (default: Update): "
if "%commit_msg%"=="" set commit_msg=Update

:: Commit
echo Committing...
git commit -m "%commit_msg%"

:: Push
echo Pushing to GitHub...
git push

if %errorlevel% neq 0 (
    echo.
    echo Warning: Push failed. You might need to set up the remote origin or sign in.
    echo To add origin: git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
    echo.
    pause
    exit /b
)

echo.
echo ==========================================
echo          Success!
echo ==========================================
timeout /t 3
