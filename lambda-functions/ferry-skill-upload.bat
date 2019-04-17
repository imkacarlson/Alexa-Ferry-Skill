@echo off

del index.zip
cd .\ferry-skill-lambda\
7z a -r ..\index.zip *
cd ..
aws lambda update-function-code --function-name ferry-skill --zip-file fileb://index.zip