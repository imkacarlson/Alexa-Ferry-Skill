@echo off

del index.zip
cd .\current-state-ferries-lambda\
7z a -r ..\index.zip *
cd ..
aws lambda update-function-code --function-name current-state-ferries --zip-file fileb://index.zip