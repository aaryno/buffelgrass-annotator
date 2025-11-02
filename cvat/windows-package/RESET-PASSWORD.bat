@echo off
REM Reset CVAT user password

echo.
echo Resetting annotator password...
echo.

docker exec cvat_server python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); user = User.objects.get(username='annotator'); user.set_password('buffelgrass2024'); user.save(); print('Password reset!')"

echo.
echo Password has been reset to: buffelgrass2024
echo.
pause

