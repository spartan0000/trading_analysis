$ACCOUNT_ID = aws sts get-caller-identity --query Account --output text
$REGION = "us-east-1"
$REPO = "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/insider-trading"

docker build --platform linux/amd64 --provenance=false -t insider-trading .
docker tag insider-trading:latest "$REPO:latest"
docker push "$REPO:latest"
aws lambda update-function-code --function-name insider-trading --image-uri "$REPO:latest" --region $REGION

Write-Host "Deployed successfully"