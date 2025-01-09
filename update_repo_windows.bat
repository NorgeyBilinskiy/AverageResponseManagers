@echo off
REM Go to the directory with the repository
cd C:\My_Code\Other\EGELend

REM Saving current changes to stash
git stash push -m "Auto stash before pull"

REM Deleting local changes
git reset --hard HEAD

REM Updating code from the main repository
git pull origin main

REM Returning changes from stash (if any)
git stash pop

REM Notification of successful update
echo "Code successfully updated from remote repository"
pause
