@echo off

del index.zip
cd .\next-departure-lambda\
7z a -r ..\index.zip *
cd ..
aws lambda update-function-code --function-name next-departure --zip-file fileb://index.zip