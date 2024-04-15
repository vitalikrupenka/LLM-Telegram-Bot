#!/bin/bash

# Clean up
rm -rf requirements.txt
rm -rf telegram_bot_lambda.zip
rm -rf package/

# Generate dependencies and remove unwanted packages
pipreqs . --savepath requirements_tmp.txt
sed '/boto3/d' requirements_tmp.txt > requirements.txt
sed -i '' '/os/d' requirements.txt  # use sed -i for Linux
rm requirements_tmp.txt

# Generate package
pip install -r requirements.txt -t ./package/
cp lambda.py package/
cd package
zip -r ../telegram_bot_lambda.zip .
cd ..

# Upload the zip file to your S3 bucket
aws s3 cp telegram_bot_lambda.zip s3://$S3_TGBOT_BUCKET/$S3_TGBOT_LAMBDA

# Update Lambda function using the uploaded zip file
aws lambda update-function-code --function-name $AWS_TGBOT_LAMBDA_NAME --s3-bucket $S3_TGBOT_BUCKET --s3-key $S3_TGBOT_LAMBDA #--no-cli-pager

# Check command status
if [ $? -eq 0 ]; then
    echo -e "\033[0;32m$(date '+%Y-%m-%d %H:%M:%S'): Deployment completed successfully.\033[0m"
else
    echo -e "\033[0;31mSomething went wrong\033[0m"
fi