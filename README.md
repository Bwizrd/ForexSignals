python -m venv ForexSignals source ForexSignals/bin/activate

pip install ipykernel

python -m ipykernel install —name=ForexSignals

jupyter kernelspec list


python processAndClassifyAllFiles.py
python processAndClassify.py
python telegramReader.py
python sheets.py
python messagesToSheets.py
python getBackdatedDataAndPassToSheet.py

python resizeCells.py   
python uploadImageAndShow.py  

TODO:

Process the image of the potential for long or short
Get the values using cv2

https://docs.google.com/spreadsheets/d/1ZZtLDrHAXPao97ndJqLLajooM5f5a3XBfKwWTokHg90/edit#gid=626506614

poetry run python DataSourceHistoric.py --ccy_pair EURUSD --start_date 2024-05-21 --end_date 2024-05-22 --resolution 1Min