@echo off

del index.zip
cd .\make-predictions-lambda\
7z a -r ..\index.zip *
cd ..
aws lambda update-function-code --function-name make-predictions --zip-file fileb://index.zip