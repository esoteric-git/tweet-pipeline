# Tweet Pipeline - Twitter Automation

This project automates posting tweets using AWS Lambda, Step Functions, and DynamoDB. It's designed to post tweets at random intervals between 1-6 hours, avoiding the 1-6 AM PST timeframe.

## Project Structure

- `lambda/post_tweet.py`: Lambda function for posting tweets and calculating wait times
- `buildspec.yaml`: CodeBuild specification for CI/CD pipeline
- `template.yaml`: SAM template for deploying AWS resources

## Prerequisites

1. AWS Account
2. AWS CLI configured with appropriate permissions
3. SAM CLI installed
4. Twitter Developer Account with API credentials

## Setup Instructions

### 1. SSM Parameters

Set up the following SSM parameters in your AWS account:

```
/twitter/<your-twitter-account>/consumer_key
/twitter/<your-twitter-account>/consumer_secret
/twitter/<your-twitter-account>/access_token
/twitter/<your-twitter-account>/access_token_secret
/twitter/<your-twitter-account>/bearer_token
/twitter/table_name
```

Replace `<your-twitter-account>` with your Twitter account name.

### 2. AWS Resources

1. Create a DynamoDB table:
   - Table name: Use the value you set in `/twitter/table_name`
   - Partition key: `id` (String)
   - Sort key: None

2. Create an S3 bucket for SAM deployments

### 3. Twitter API Credentials

1. Create a Twitter Developer account at https://developer.twitter.com/
2. Create a new project and app
3. Generate API keys and tokens
4. Store these credentials in SSM parameters as described above

## Deployment Instructions

1. Clone this repository
2. Update `buildspec.yaml`:
   - Replace `hard-code-your-account-id` with your AWS account ID
   - Replace `hard-code-your-S3-bucket-name` with your S3 bucket name
3. Update `lambda/post_tweet.py`:
   - Replace `'my-twitter'` with your Twitter account name
4. Deploy using SAM CLI:

```bash
sam build
sam deploy --guided
```

Follow the prompts to complete the deployment.

## Usage

After deployment, the Step Functions state machine will automatically start and manage the tweet posting process. You can monitor its execution in the AWS Step Functions console.

To add tweets to the queue, insert items into the DynamoDB table with the following structure:

```json
{
  "id": "unique-id",
  "tweet": "Your tweet content",
  "posted": false,
  "twitter_account": "your-twitter-account-name"
}
```

## Customization

- Adjust posting hours: Modify the `is_within_posting_hours()` function in `post_tweet.py`
- Change wait time range: Update the `calculate_wait_time()` function in `post_tweet.py`

## Troubleshooting

- Check CloudWatch Logs for Lambda function execution logs
- Verify SSM parameters are correctly set
- Ensure DynamoDB table has items to post

## Security Considerations

- Regularly rotate your Twitter API credentials
- Use IAM roles with least privilege principle
- Consider using AWS Secrets Manager for storing API credentials instead of SSM Parameter Store for additional security features

## Contributing

Please submit issues and pull requests for any improvements or bug fixes.

## License

[MIT License](LICENSE)