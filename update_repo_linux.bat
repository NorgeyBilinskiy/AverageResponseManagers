#!/bin/bash

# Переход в директорию с репозиторием
cd /My_Code/Other//EGELend

# Сохранение текущих изменений в stash
git stash push -m "Auto stash before pull"

# Удаление локальных изменений
git reset --hard HEAD

# Обновление кода из основного репозитория
git pull origin main

# Восстановление изменений из stash (если есть)
git stash pop

# Уведомление о успешном обновлении
echo "Code successfully updated from remote repository"
