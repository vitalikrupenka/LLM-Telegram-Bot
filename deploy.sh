#!/bin/bash

echo "Do you want to deploy with a layer? (y/N)"
read -n 1 -p "Press 'y' for Yes, any other key for No: " use_layer
echo # Move to a new line

# Function to deploy with layer
deploy_with_layer() {
    echo "Deploying with layer..."
    # Clean up previous builds
    rm -rf $S3_TGBOT_LAMBDA

    # Package only the Lambda function code
    zip -j $S3_TGBOT_LAMBDA ./lambda/lambda_function.py

    # Update Lambda function code directly (without S3)
    aws lambda update-function-code --function-name $AWS_TGBOT_LAMBDA_NAME --zip-file fileb://$S3_TGBOT_LAMBDA
}

# Function to deploy without layer
deploy_without_layer() {
    echo "Deploying without layer..."
    # Clean up
    rm -rf requirements.txt
    rm -rf $S3_TGBOT_LAMBDA
    rm -rf package/

    # Generate dependencies and remove unwanted packages
    pipreqs ./lambda --savepath requirements_tmp.txt
    sed '/boto3/d' requirements_tmp.txt > requirements.txt
    sed -i '' '/os/d' requirements.txt  # use sed -i for Linux
    rm requirements_tmp.txt

    # Generate package
    python3 -m pip install -r requirements.txt -t ./package/
    cp ./lambda/lambda_function.py package/
    cd package
    zip -r ../$S3_TGBOT_LAMBDA .
    cd ..

    # Upload the zip file to your S3 bucket
    aws s3 cp $S3_TGBOT_LAMBDA s3://$S3_TGBOT_BUCKET/$S3_TGBOT_LAMBDA

    # Update Lambda function using the uploaded zip file
    aws lambda update-function-code --function-name $AWS_TGBOT_LAMBDA_NAME --s3-bucket $S3_TGBOT_BUCKET --s3-key $S3_TGBOT_LAMBDA
}

# Check command status and print message
print_status() {
    if [ $? -eq 0 ]; then
        echo -e "\033[0;32m$(date '+%Y-%m-%d %H:%M:%S'): Deployment completed successfully.\033[0m"
    else
        echo -e "\033[0;31m$(date '+%Y-%m-%d %H:%M:%S'): Something went wrong. Check the logs.\033[0m"
    fi
}

# Main
if [[ "$use_layer" == "y" ]]; then
    deploy_with_layer
else
    deploy_without_layer
fi

print_status