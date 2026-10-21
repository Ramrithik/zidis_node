@echo off
echo ===================================================================
echo   Flashing ZIDIS_Node (Real 2011 Tohoku Earthquake Firmware)
echo ===================================================================
set PROG="C:\ST\STM32CubeIDE_2.2.0\STM32CubeIDE\plugins\com.st.stm32cube.ide.mcu.externaltools.cubeprogrammer.win32_2.2.500.202603051304\tools\bin\STM32_Programmer_CLI.exe"
set ELF="Debug\ZIDIS_Node.elf"

if not exist %ELF% (
    echo [ERROR] ELF file not found: %ELF%
    pause
    exit /b 1
)

echo [FLASH] Connecting to NUCLEO-H533RE over ST-LINK SWD...
%PROG% -c port=SWD -w %ELF% -v -rst
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Flashing failed! Please verify:
    echo   1. The NUCLEO-H533RE USB cable is firmly connected to your PC.
    echo   2. The ST-LINK status LED on the board is illuminated.
    echo.
) else (
    echo.
    echo ===================================================================
    echo   FLASH SUCCESSFUL! Board is now running real earthquake analysis!
    echo ===================================================================
)
pause
